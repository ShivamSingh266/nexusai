"""Focused tests for the first deterministic Gap Analysis slice."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.canonical_skill import CanonicalSkill
from app.models.user import Role

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db: Session = TestingSessionLocal()
    db.add(Role(name="applicant", description="Applicant"))
    for number in range(1, 5):
        db.add(
            CanonicalSkill(
                skill_id=f"SKILL_{number:04d}",
                canonical_name=f"Skill {number}",
                normalized_name=f"skill {number}",
                category="IT/Software - Data & AI",
                source="ESCO",
                taxonomy_version="v1.2.1",
            )
        )
    db.commit()
    db.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield

    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def register(client: TestClient, email: str) -> tuple[str, int]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Gap User",
            "role": "applicant",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["data"]["id"]


def request_payload(user_id: int = 1) -> dict:
    return {
        "candidate": {
            "subject_id": user_id,
            "taxonomy_version": "v1.2.1",
            "skills": [
                {"skill_id": "SKILL_0001", "taxonomy_version": "v1.2.1"}
            ],
        },
        "target": {
            "job_id": None,
            "required_skills": [
                {
                    "skill_id": "SKILL_0001",
                    "taxonomy_version": "v1.2.1",
                    "role_importance": 1.0,
                },
                {
                    "skill_id": "SKILL_0002",
                    "taxonomy_version": "v1.2.1",
                    "role_importance": 0.5,
                },
            ],
        },
        "context": {"district_id": None, "sector": None},
    }


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_gap_requires_authentication(client: TestClient):
    response = client.post("/api/v1/gaps/analyze", json=request_payload())
    assert response.status_code in (401, 403)


def test_partial_match_has_metadata(client: TestClient):
    token, user_id = register(client, "gap@example.com")
    response = client.post(
        "/api/v1/gaps/analyze",
        json=request_payload(user_id),
        headers=auth(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["skill_id"] for item in body["data"]["matched_skills"]] == ["SKILL_0001"]
    assert [item["skill_id"] for item in body["data"]["missing_skills"]] == ["SKILL_0002"]
    assert body["data"]["matched_skills"][0]["coverage"] == 1.0
    assert body["meta"] == {
        "scoring_version": "gap-v1",
        "taxonomy_version": "v1.2.1",
        "demand_source_version": "naukri:indian-job-market-dataset-2025",
    }
    assert body["model_version"] is None
    assert body["source_version"] == "backend-v1"
    assert body["generated_at"]


def test_all_skills_matched(client: TestClient):
    token, user_id = register(client, "all@example.com")
    payload = request_payload(user_id)
    payload["candidate"]["skills"].append(
        {"skill_id": "SKILL_0002", "taxonomy_version": "v1.2.1"}
    )
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 200
    assert response.json()["data"]["missing_skills"] == []


def test_completely_missing_skills(client: TestClient):
    token, user_id = register(client, "missing@example.com")
    payload = request_payload(user_id)
    payload["candidate"]["skills"] = []
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 200
    assert len(response.json()["data"]["missing_skills"]) == 2


def test_priority_and_neutral_trend_fallback(client: TestClient):
    token, user_id = register(client, "priority@example.com")
    payload = request_payload(user_id)
    payload["candidate"]["skills"] = []
    payload["target"]["required_skills"] = [
        {
            "skill_id": "SKILL_0001",
            "taxonomy_version": "v1.2.1",
            "role_importance": 0.5,
        }
    ]
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 200, response.text
    missing = response.json()["data"]["missing_skills"][0]
    assert missing["normalized_demand"] is not None
    assert missing["priority"] == pytest.approx(missing["normalized_demand"] * 0.5)
    assert missing["trend_multiplier"] == 1.0
    assert any("neutral trend" in warning for warning in response.json()["warnings"])


def test_invalid_taxonomy_and_skill_ids_are_rejected(client: TestClient):
    token, user_id = register(client, "invalid@example.com")
    payload = request_payload(user_id)
    payload["candidate"]["skills"][0]["skill_id"] = "SKILL_9999"
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 422

    payload = request_payload(user_id)
    payload["candidate"]["taxonomy_version"] = "v9.9.9"
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 422


def test_duplicates_and_nullable_proficiency_are_handled(client: TestClient):
    token, user_id = register(client, "duplicates@example.com")
    payload = request_payload(user_id)
    payload["candidate"]["skills"] = [
        {
            "skill_id": "SKILL_0001",
            "taxonomy_version": "v1.2.1",
            "proficiency_level": None,
            "years_experience": None,
        },
        {"skill_id": "SKILL_0001", "taxonomy_version": "v1.2.1"},
    ]
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 422

    payload = request_payload(user_id)
    payload["target"]["required_skills"].append(
        payload["target"]["required_skills"][0]
    )
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 422


def test_unavailable_demand_is_not_fabricated(client: TestClient):
    token, user_id = register(client, "nodemand@example.com")
    payload = request_payload(user_id)
    payload["candidate"]["skills"] = []
    payload["target"]["required_skills"] = [
        {
            "skill_id": "SKILL_0004",
            "taxonomy_version": "v1.2.1",
            "role_importance": 1.0,
        }
    ]
    payload["context"] = {"district_id": "does-not-exist", "sector": "missing"}
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 200
    missing = response.json()["data"]["missing_skills"][0]
    assert missing["normalized_demand"] is None
    assert missing["priority"] is None
    assert any("Demand unavailable" in warning for warning in response.json()["warnings"])


def test_legacy_free_text_skills_are_ignored_with_warning(client: TestClient):
    token, user_id = register(client, "legacy@example.com")
    skill_response = client.post(
        "/api/v1/skills",
        json={"skill_name": "Legacy Free Text", "proficiency_level": "expert"},
        headers=auth(token),
    )
    assert skill_response.status_code == 201, skill_response.text

    payload = request_payload(user_id)
    payload["candidate"]["skills"] = []
    response = client.post("/api/v1/gaps/analyze", json=payload, headers=auth(token))
    assert response.status_code == 200, response.text
    assert any("free-text applicant skills" in warning for warning in response.json()["warnings"])
