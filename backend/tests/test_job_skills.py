"""Tests for canonical skills attached to job postings."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.canonical_skill import CanonicalSkill
from app.models.company import Company
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.user import Role

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


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
    for role_name in ["applicant", "recruiter", "government", "admin"]:
        db.add(Role(name=role_name, description=role_name))
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


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client: TestClient, email: str, role: str) -> tuple[str, int]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": role.title(),
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["data"]["id"]


def create_recruiter_job(
    client: TestClient,
    email: str,
    *,
    status: str = "draft",
    company_name: str | None = None,
) -> tuple[str, dict]:
    token, _ = register(client, email, "recruiter")
    company_response = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": company_name or email.split("@")[0]},
        headers=auth(token),
    )
    assert company_response.status_code == 201, company_response.text
    job_response = client.post(
        "/api/v1/jobs",
        json={"title": "Backend Engineer", "status": status},
        headers=auth(token),
    )
    assert job_response.status_code == 201, job_response.text
    return token, job_response.json()


def create_skill_payload(
    skill_id: str = "SKILL_0001",
    *,
    importance: float = 1.0,
    mandatory: bool = True,
) -> dict:
    return {
        "skill_id": skill_id,
        "taxonomy_version": "v1.2.1",
        "role_importance": importance,
        "is_mandatory": mandatory,
    }


def test_create_list_patch_and_delete_job_skill(client: TestClient):
    token, job = create_recruiter_job(client, "crud_job_skill@example.com")
    create = client.post(
        f"/api/v1/jobs/{job['id']}/skills",
        json=create_skill_payload(importance=0.75, mandatory=False),
        headers=auth(token),
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["skill_id"] == "SKILL_0001"
    assert body["role_importance"] == 0.75
    assert body["is_mandatory"] is False

    listed = client.get(f"/api/v1/jobs/{job['id']}/skills", headers=auth(token))
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patched = client.patch(
        f"/api/v1/jobs/{job['id']}/skills/SKILL_0001",
        json={"role_importance": 0.5, "is_mandatory": True},
        headers=auth(token),
    )
    assert patched.status_code == 200
    assert patched.json()["role_importance"] == 0.5

    deleted = client.delete(
        f"/api/v1/jobs/{job['id']}/skills/SKILL_0001",
        headers=auth(token),
    )
    assert deleted.status_code == 204


def test_bulk_create_rejects_duplicate_payload_and_supports_multiple_skills(client: TestClient):
    token, job = create_recruiter_job(client, "bulk_job_skill@example.com")
    duplicate_payload = {
        "skills": [create_skill_payload(), create_skill_payload()]
    }
    duplicate = client.post(
        f"/api/v1/jobs/{job['id']}/skills/bulk",
        json=duplicate_payload,
        headers=auth(token),
    )
    assert duplicate.status_code == 422

    bulk = client.post(
        f"/api/v1/jobs/{job['id']}/skills/bulk",
        json={"skills": [create_skill_payload(), create_skill_payload("SKILL_0002")]},
        headers=auth(token),
    )
    assert bulk.status_code == 201, bulk.text
    assert {item["skill_id"] for item in bulk.json()} == {"SKILL_0001", "SKILL_0002"}


def test_unique_constraint_returns_conflict(client: TestClient):
    token, job = create_recruiter_job(client, "unique_job_skill@example.com")
    path = f"/api/v1/jobs/{job['id']}/skills"
    assert client.post(path, json=create_skill_payload(), headers=auth(token)).status_code == 201
    duplicate = client.post(path, json=create_skill_payload(), headers=auth(token))
    assert duplicate.status_code == 409


def test_role_importance_and_canonical_validation(client: TestClient):
    token, job = create_recruiter_job(client, "validation_job_skill@example.com")
    path = f"/api/v1/jobs/{job['id']}/skills"
    for importance in [-0.01, 1.01]:
        response = client.post(
            path,
            json=create_skill_payload(importance=importance),
            headers=auth(token),
        )
        assert response.status_code == 422

    invalid = client.post(
        path,
        json=create_skill_payload("SKILL_9999"),
        headers=auth(token),
    )
    assert invalid.status_code == 422

    mismatch = client.post(
        path,
        json={**create_skill_payload(), "taxonomy_version": "v9.9.9"},
        headers=auth(token),
    )
    assert mismatch.status_code == 422


def test_recruiter_ownership_and_no_company_rules(client: TestClient):
    owner_token, job = create_recruiter_job(client, "owner_job_skill@example.com")
    other_token, _ = create_recruiter_job(client, "other_job_skill@example.com")
    path = f"/api/v1/jobs/{job['id']}/skills"

    assert client.post(path, json=create_skill_payload(), headers=auth(other_token)).status_code == 404
    assert client.get(path, headers=auth(other_token)).status_code == 404
    assert client.post(path, json=create_skill_payload(), headers=auth(owner_token)).status_code == 201

    no_company_token, _ = register(client, "nocompany_job_skill@example.com", "recruiter")
    assert client.post(path, json=create_skill_payload("SKILL_0002"), headers=auth(no_company_token)).status_code == 403


def test_applicant_reads_only_published_jobs_and_cannot_mutate(client: TestClient):
    owner_token, published = create_recruiter_job(
        client, "published_job_skill@example.com", status="published"
    )
    _, draft = create_recruiter_job(client, "draft_job_skill@example.com", status="draft")
    _, closed = create_recruiter_job(client, "closed_job_skill@example.com", status="closed")
    assert client.post(
        f"/api/v1/jobs/{published['id']}/skills",
        json=create_skill_payload(),
        headers=auth(owner_token),
    ).status_code == 201

    applicant_token, _ = register(client, "reader_job_skill@example.com", "applicant")
    published_path = f"/api/v1/jobs/{published['id']}/skills"
    assert client.get(published_path, headers=auth(applicant_token)).status_code == 200
    assert client.get(f"/api/v1/jobs/{draft['id']}/skills", headers=auth(applicant_token)).status_code == 404
    assert client.get(f"/api/v1/jobs/{closed['id']}/skills", headers=auth(applicant_token)).status_code == 404
    assert client.post(published_path, json=create_skill_payload("SKILL_0002"), headers=auth(applicant_token)).status_code == 403
    assert client.patch(f"{published_path}/SKILL_0001", json={"role_importance": 0.2}, headers=auth(applicant_token)).status_code == 403
    assert client.delete(f"{published_path}/SKILL_0001", headers=auth(applicant_token)).status_code == 403


def test_database_cascade_and_canonical_restrict():
    db: Session = TestingSessionLocal()
    company = Company(company_name="Constraint Company")
    db.add(company)
    db.flush()
    job = Job(company_id=company.id, title="Constraint Job")
    skill = db.get(CanonicalSkill, "SKILL_0004")
    db.add(job)
    db.flush()
    db.add(JobSkill(job_id=job.id, skill_id=skill.skill_id, taxonomy_version="v1.2.1"))
    db.commit()

    db.delete(job)
    db.commit()
    assert db.query(JobSkill).filter(JobSkill.job_id == job.id).count() == 0

    job = Job(company_id=company.id, title="Restrict Job")
    db.add(job)
    db.flush()
    db.add(JobSkill(job_id=job.id, skill_id=skill.skill_id, taxonomy_version="v1.2.1"))
    db.commit()
    db.delete(skill)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.close()
