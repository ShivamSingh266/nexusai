from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.models.canonical_skill import CanonicalSkill
from app.models.user import Role
from app.services import government_data


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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
    db = TestingSessionLocal()
    for role_name in ("applicant", "recruiter", "government", "admin"):
        db.add(Role(name=role_name, description=role_name))
    for skill_id, name in (
        ("SKILL_0001", "Python"),
        ("SKILL_0020", "Skill 20"),
        ("SKILL_0254", "Skill 254"),
        ("SKILL_0486", "Skill 486"),
    ):
        db.add(
            CanonicalSkill(
                skill_id=skill_id,
                canonical_name=name,
                normalized_name=name.lower().replace(" ", "-"),
                category="technical",
                source="ESCO",
                taxonomy_version=settings.TAXONOMY_VERSION,
            )
        )
    db.commit()
    db.close()
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def register(client: TestClient, email: str, role: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Government User",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_government_demand_requires_role_and_exposes_evidence(client: TestClient):
    government_token = register(client, "government@example.com", "government")
    response = client.get(
        "/api/v1/government/demand?skill_id=SKILL_0254",
        headers=auth(government_token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source_version"] == "member4-processed-v1"
    assert body["meta"]["taxonomy_version"] == settings.TAXONOMY_VERSION
    assert body["data"]
    assert "Forecast data is unavailable" in body["warnings"][0]
    assert body["data"]
    assert {row["skill_id"] for row in body["data"]} == {"SKILL_0254"}


def test_courses_and_training_gaps_are_available(client: TestClient):
    token = register(client, "government-data@example.com", "government")
    courses = client.get(
        "/api/v1/government/courses?skill_id=SKILL_0486",
        headers=auth(token),
    )
    gaps = client.get(
        "/api/v1/government/training-gaps?skill_id=SKILL_0020",
        headers=auth(token),
    )
    assert courses.status_code == 200
    assert gaps.status_code == 200
    assert courses.json()["meta"]["taxonomy_version"] == settings.TAXONOMY_VERSION
    assert gaps.json()["meta"]["taxonomy_version"] == settings.TAXONOMY_VERSION
    assert courses.json()["data"]
    assert gaps.json()["data"]
    assert {row["skill_id"] for row in gaps.json()["data"]} == {"SKILL_0020"}


def test_non_government_roles_and_unauthenticated_access_are_rejected(client: TestClient):
    applicant_token = register(client, "government-applicant@example.com", "applicant")
    recruiter_token = register(client, "government-recruiter@example.com", "recruiter")
    assert client.get(
        "/api/v1/government/demand",
        headers=auth(applicant_token),
    ).status_code == 403
    assert client.get(
        "/api/v1/government/demand",
        headers=auth(recruiter_token),
    ).status_code == 403
    assert client.get("/api/v1/government/demand").status_code == 403


def test_admin_access_and_demand_order_are_deterministic(client: TestClient):
    token = register(client, "government-admin@example.com", "admin")
    first = client.get("/api/v1/government/demand", headers=auth(token))
    second = client.get("/api/v1/government/demand", headers=auth(token))
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


def test_demand_filters_match_requested_values(client: TestClient):
    token = register(client, "government-filters@example.com", "government")
    baseline = client.get("/api/v1/government/demand", headers=auth(token)).json()["data"]
    row = baseline[0]
    for parameter in ("district_id", "sector"):
        response = client.get(
            f"/api/v1/government/demand?{parameter}={row[parameter]}",
            headers=auth(token),
        )
        assert response.status_code == 200
        assert all(item[parameter] == row[parameter] for item in response.json()["data"])


def test_malformed_dataset_returns_controlled_error(client: TestClient, tmp_path, monkeypatch):
    malformed = tmp_path / "skill_demand_history.csv"
    malformed.write_text("skill_id,district_id\nSKILL_0254,Amravati\n", encoding="utf-8")
    monkeypatch.setattr(government_data, "_processed_dir", lambda: tmp_path)
    government_data._read_csv.cache_clear()

    token = register(client, "government-malformed@example.com", "government")
    response = client.get("/api/v1/government/demand", headers=auth(token))

    assert response.status_code == 503
    assert response.json()["detail"] == "Demand dataset invalid"
    government_data._read_csv.cache_clear()


def test_invalid_skill_filter_is_rejected(client: TestClient):
    token = register(client, "government-invalid@example.com", "government")
    response = client.get(
        "/api/v1/government/demand?skill_id=SKILL_9999",
        headers=auth(token),
    )
    assert response.status_code == 422
