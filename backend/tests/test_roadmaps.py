from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
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
