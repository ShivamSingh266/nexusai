from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.main import app
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill
from app.models.canonical_skill import CanonicalSkill
from app.models.company import Company
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.user import Role, User


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
    db = TestingSessionLocal()
    for role_name in ("applicant", "recruiter", "government", "admin"):
        db.add(Role(name=role_name, description=role_name))
    db.add(
        CanonicalSkill(
            skill_id="SKILL_0001",
            canonical_name="Python",
            normalized_name="python",
            category="technical",
            source="ESCO",
            taxonomy_version=settings.TAXONOMY_VERSION,
        )
    )
    db.add(
        CanonicalSkill(
            skill_id="SKILL_0002",
            canonical_name="SQL",
            normalized_name="sql",
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
            "full_name": "Roadmap User",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def register_with_id(client: TestClient, email: str, role: str) -> tuple[str, int]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Roadmap User",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["data"]["id"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def roadmap_payload() -> dict:
    return {
        "title": "Python upskilling",
        "taxonomy_version": settings.TAXONOMY_VERSION,
        "items": [
            {
                "skill_id": "SKILL_0001",
                "taxonomy_version": settings.TAXONOMY_VERSION,
                "position": 0,
                "course_id": "106105167",
                "resource_url": "https://example.com/python",
                "resource_title": "Python course",
            },
            {
                "skill_id": "SKILL_0002",
                "taxonomy_version": settings.TAXONOMY_VERSION,
                "position": 1,
                "status": "in_progress",
            },
        ],
    }


def add_profile(
    user_id: int,
    *,
    skill_ids: list[str] | None = None,
) -> None:
    db = TestingSessionLocal()
    db.add(
        ApplicantProfile(
            user_id=user_id,
            location="Pune",
            education="BSc Computer Science",
            experience_years=2,
        )
    )
    for skill_id in skill_ids or []:
        db.add(
            ApplicantSkill(
                user_id=user_id,
                skill_id=skill_id,
                taxonomy_version=settings.TAXONOMY_VERSION,
                skill_name=skill_id,
                proficiency_level="intermediate",
            )
        )
    db.commit()
    db.close()


def add_role_token(email: str, role_name: str) -> str:
    db = TestingSessionLocal()
    role = db.query(Role).filter(Role.name == role_name).one()
    user = User(
        email=email,
        password_hash=hash_password("password123"),
        full_name="Roadmap Role User",
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    token = create_access_token(user.id, role_name)
    db.close()
    return token


def add_published_job(skill_ids: list[str], *, status: str = "published") -> int:
    db = TestingSessionLocal()
    company = Company(company_name="Generation Company")
    db.add(company)
    db.flush()
    job = Job(company_id=company.id, title="Generated Job", status=status)
    db.add(job)
    db.flush()
    db.add_all(
        [
            JobSkill(
                job_id=job.id,
                skill_id=skill_id,
                taxonomy_version=settings.TAXONOMY_VERSION,
                role_importance=1.0,
            )
            for skill_id in skill_ids
        ]
    )
    db.commit()
    job_id = job.id
    db.close()
    return job_id


def test_applicant_can_create_retrieve_and_update_roadmap(client: TestClient):
    token = register(client, "roadmap-applicant@example.com", "applicant")

    created = client.post(
        "/api/v1/roadmaps",
        headers=auth(token),
        json=roadmap_payload(),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["title"] == "Python upskilling"
    assert [item["position"] for item in body["items"]] == [0, 1]
    assert body["items"][0]["course_id"] == "106105167"

    roadmap_id = body["id"]
    item_id = body["items"][0]["id"]
    retrieved = client.get(f"/api/v1/roadmaps/{roadmap_id}", headers=auth(token))
    assert retrieved.status_code == 200
    assert retrieved.json()["items"][0]["skill_id"] == "SKILL_0001"

    updated = client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/items/{item_id}",
        headers=auth(token),
        json={"status": "completed"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "completed"
    assert updated.json()["position"] == 0


def test_roadmap_persists_and_lists_for_owner_only(client: TestClient):
    token = register(client, "roadmap-owner@example.com", "applicant")
    other_token = register(client, "roadmap-other@example.com", "applicant")
    created = client.post(
        "/api/v1/roadmaps",
        headers=auth(token),
        json=roadmap_payload(),
    )
    roadmap_id = created.json()["id"]

    assert client.get("/api/v1/roadmaps", headers=auth(token)).status_code == 200
    assert client.get(
        f"/api/v1/roadmaps/{roadmap_id}",
        headers=auth(other_token),
    ).status_code == 404


@pytest.mark.parametrize(
    "headers",
    [
        {},
    ],
)
def test_unauthenticated_access_is_rejected(client: TestClient, headers: dict):
    assert client.get("/api/v1/roadmaps", headers=headers).status_code == 403


def test_non_applicant_role_is_rejected(client: TestClient):
    token = register(client, "roadmap-recruiter@example.com", "recruiter")
    assert client.get("/api/v1/roadmaps", headers=auth(token)).status_code == 403


@pytest.mark.parametrize(
    ("skill_id", "taxonomy_version", "expected_status"),
    [
        ("SKILL_9999", "v1.2.1", 422),
        ("SKILL_0001", "v9.9.9", 422),
    ],
)
def test_invalid_skill_or_taxonomy_is_rejected(
    client: TestClient,
    skill_id: str,
    taxonomy_version: str,
    expected_status: int,
):
    token = register(client, f"roadmap-invalid-{skill_id}-{taxonomy_version}@example.com", "applicant")
    payload = roadmap_payload()
    payload["items"][0]["skill_id"] = skill_id
    payload["items"][0]["taxonomy_version"] = taxonomy_version
    response = client.post("/api/v1/roadmaps", headers=auth(token), json=payload)
    assert response.status_code == expected_status


def test_item_versions_must_match_roadmap(client: TestClient):
    token = register(client, "roadmap-item-version@example.com", "applicant")
    payload = roadmap_payload()
    payload["items"][0]["taxonomy_version"] = "v9.9.9"
    response = client.post("/api/v1/roadmaps", headers=auth(token), json=payload)
    assert response.status_code == 422


def test_generate_roadmap_loads_persisted_profile_and_maps_missing_skills(
    client: TestClient,
):
    token, user_id = register_with_id(client, "roadmap-generate@example.com", "applicant")
    add_profile(user_id, skill_ids=["SKILL_0001"])

    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={
            "target": {
                "required_skills": [
                    {
                        "skill_id": "SKILL_0001",
                        "taxonomy_version": settings.TAXONOMY_VERSION,
                    },
                    {
                        "skill_id": "SKILL_0002",
                        "taxonomy_version": settings.TAXONOMY_VERSION,
                    },
                ]
            },
            "title": "Generated roadmap",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == "Generated roadmap"
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["skill_id"] == "SKILL_0002"
    assert item["taxonomy_version"] == settings.TAXONOMY_VERSION
    assert item["position"] == 0
    assert item["status"] == "pending"
    assert item["notes"] == "Required canonical skill is absent from the candidate profile."
    assert item["course_id"] is None
    assert item["resource_url"] is None
    assert item["resource_title"] is None


def test_generate_roadmap_supports_published_job_and_no_gaps(client: TestClient):
    token, user_id = register_with_id(client, "roadmap-job-generate@example.com", "applicant")
    add_profile(user_id, skill_ids=["SKILL_0001", "SKILL_0002"])
    job_id = add_published_job(["SKILL_0001", "SKILL_0002"])

    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={"target": {"job_id": job_id}},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == "Roadmap for target job"
    assert body["items"] == []


def test_generate_roadmap_orders_priority_and_nulls_deterministically(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.core import gap as gap_core

    token, user_id = register_with_id(client, "roadmap-order-generate@example.com", "applicant")
    add_profile(user_id)

    def fake_signals(*, skill_ids, district_id, sector):
        return {
            "SKILL_0001": gap_core.DemandSignal(0.4, 1.0),
            "SKILL_0002": gap_core.DemandSignal(0.8, 1.0),
        }

    monkeypatch.setattr(gap_core, "load_demand_signals", fake_signals)
    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={
            "target": {
                "required_skills": [
                    {
                        "skill_id": "SKILL_0001",
                        "taxonomy_version": settings.TAXONOMY_VERSION,
                        "role_importance": 1.0,
                    },
                    {
                        "skill_id": "SKILL_0002",
                        "taxonomy_version": settings.TAXONOMY_VERSION,
                        "role_importance": 1.0,
                    },
                ]
            }
        },
    )

    assert response.status_code == 201, response.text
    assert [item["skill_id"] for item in response.json()["items"]] == [
        "SKILL_0002",
        "SKILL_0001",
    ]


def test_generate_roadmap_rejects_invalid_job_and_non_applicant(client: TestClient):
    token, user_id = register_with_id(client, "roadmap-invalid-job@example.com", "applicant")
    add_profile(user_id)
    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={"target": {"job_id": 999999}},
    )
    assert response.status_code == 404

    unpublished_job_id = add_published_job(["SKILL_0001"], status="draft")
    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={"target": {"job_id": unpublished_job_id}},
    )
    assert response.status_code == 404

    recruiter_token = register(client, "roadmap-generate-recruiter@example.com", "recruiter")
    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(recruiter_token),
        json={"target": {"required_skills": []}},
    )
    assert response.status_code == 403

    government_token = add_role_token(
        "roadmap-generate-government@example.com",
        "government",
    )
    response = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(government_token),
        json={"target": {"required_skills": []}},
    )
    assert response.status_code == 403


def test_generate_roadmap_repeated_requests_create_new_roadmaps(client: TestClient):
    token, user_id = register_with_id(client, "roadmap-repeat@example.com", "applicant")
    add_profile(user_id)
    payload = {
        "target": {
            "required_skills": [
                {
                    "skill_id": "SKILL_0002",
                    "taxonomy_version": settings.TAXONOMY_VERSION,
                }
            ]
        }
    }

    first = client.post("/api/v1/roadmaps/generate", headers=auth(token), json=payload)
    second = client.post("/api/v1/roadmaps/generate", headers=auth(token), json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_generate_roadmap_rejects_invalid_target_and_profile_state(client: TestClient):
    token, user_id = register_with_id(
        client,
        "roadmap-invalid-target@example.com",
        "applicant",
    )
    add_profile(user_id)

    invalid_skill = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={
            "target": {
                "required_skills": [
                    {
                        "skill_id": "SKILL_9999",
                        "taxonomy_version": settings.TAXONOMY_VERSION,
                    }
                ]
            }
        },
    )
    assert invalid_skill.status_code == 422

    taxonomy_mismatch = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(token),
        json={
            "target": {
                "required_skills": [
                    {
                        "skill_id": "SKILL_0001",
                        "taxonomy_version": "v9.9.9",
                    }
                ]
            }
        },
    )
    assert taxonomy_mismatch.status_code == 422

    no_profile_token = register(client, "roadmap-no-profile@example.com", "applicant")
    no_profile = client.post(
        "/api/v1/roadmaps/generate",
        headers=auth(no_profile_token),
        json={"target": {"required_skills": []}},
    )
    assert no_profile.status_code == 422
