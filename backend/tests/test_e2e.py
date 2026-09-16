"""Cross-module workflows using the production FastAPI routes and services."""

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
from app.models.user import Role, User
from app.core.security import create_access_token, hash_password
from app.services.skill_profile import load_candidate_skill_profile


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


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client: TestClient, email: str, role: str) -> tuple[str, int]:
    if role in {"government", "admin"}:
        db = TestingSessionLocal()
        try:
            role_record = db.query(Role).filter(Role.name == role).one()
            user = User(
                email=email,
                password_hash=hash_password("password123"),
                full_name=role.title(),
                role_id=role_record.id,
            )
            db.add(user)
            db.commit()
            return create_access_token(user.id, role), user.id
        finally:
            db.close()
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


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db: Session = TestingSessionLocal()
    try:
        db.add_all(
            [Role(name=name, description=name) for name in ("applicant", "recruiter", "government", "admin")]
        )
        db.add_all(
            [
                CanonicalSkill(
                    skill_id="SKILL_0001",
                    canonical_name="Python",
                    normalized_name="python",
                    category="IT/Software - Data & AI",
                    source="ESCO",
                    taxonomy_version=settings.TAXONOMY_VERSION,
                ),
                CanonicalSkill(
                    skill_id="SKILL_0002",
                    canonical_name="SQL",
                    normalized_name="sql",
                    category="IT/Software - Data & AI",
                    source="ESCO",
                    taxonomy_version=settings.TAXONOMY_VERSION,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_applicant_recruiter_workflow_and_ownership(client: TestClient):
    applicant_token, applicant_id = register(client, "e2e-applicant@example.com", "applicant")
    other_applicant_token, _ = register(client, "e2e-other-applicant@example.com", "applicant")

    assert client.post(
        "/api/v1/profile",
        json={"location": "Pune", "education": "Computer Science", "experience_years": 3},
        headers=auth(applicant_token),
    ).status_code == 201
    canonical_skill = client.post(
        "/api/v1/skills",
        json={
            "skill_name": "Python",
            "skill_id": "SKILL_0001",
            "taxonomy_version": settings.TAXONOMY_VERSION,
            "proficiency_level": "intermediate",
        },
        headers=auth(applicant_token),
    )
    assert canonical_skill.status_code == 201, canonical_skill.text
    assert canonical_skill.json()["years_experience"] is None
    assert client.post(
        "/api/v1/skills",
        json={"skill_name": "Unmapped free-text skill"},
        headers=auth(applicant_token),
    ).status_code == 201

    db = TestingSessionLocal()
    try:
        profile = load_candidate_skill_profile(db, applicant_id)
    finally:
        db.close()
    assert profile.taxonomy_version == settings.TAXONOMY_VERSION
    assert [(skill.skill_id, skill.taxonomy_version, skill.years_experience) for skill in profile.skills] == [
        ("SKILL_0001", settings.TAXONOMY_VERSION, None)
    ]

    recruiter_token, _ = register(client, "e2e-recruiter@example.com", "recruiter")
    company = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": "E2E Systems"},
        headers=auth(recruiter_token),
    )
    assert company.status_code == 201, company.text
    job = client.post(
        "/api/v1/jobs",
        json={
            "title": "Platform Engineer",
            "status": "published",
            "location": "Pune",
            "education_requirement": "Computer Science",
            "experience_min": 2,
            "experience_max": 5,
        },
        headers=auth(recruiter_token),
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]
    assert isinstance(job_id, int)
    for skill_id, importance in (("SKILL_0001", 1.0), ("SKILL_0002", 0.8)):
        response = client.post(
            f"/api/v1/jobs/{job_id}/skills",
            json={
                "skill_id": skill_id,
                "taxonomy_version": settings.TAXONOMY_VERSION,
                "role_importance": importance,
            },
            headers=auth(recruiter_token),
        )
        assert response.status_code == 201, response.text

    gap = client.post(
        "/api/v1/gaps/analyze",
        json={
            "candidate": {
                "subject_id": profile.subject_id,
                "subject_type": profile.subject_type,
                "taxonomy_version": profile.taxonomy_version,
                "skills": [skill.__dict__ for skill in profile.skills],
                "location": profile.location,
                "education": profile.education,
                "experience_years": profile.experience_years,
            },
            "target": {"job_id": job_id},
            "context": {"district_id": "Pune", "sector": "IT/Software - Data & AI"},
        },
        headers=auth(applicant_token),
    )
    assert gap.status_code == 200, gap.text
    assert gap.json()["meta"]["taxonomy_version"] == settings.TAXONOMY_VERSION
    assert {item["skill_id"] for item in gap.json()["data"]["missing_skills"]} == {"SKILL_0002"}

    applicant_matches = client.get("/api/v1/matching/jobs", headers=auth(applicant_token))
    assert applicant_matches.status_code == 200, applicant_matches.text
    matched_job = next(item for item in applicant_matches.json()["data"] if item["job_id"] == job_id)
    assert matched_job["taxonomy_version"] == settings.TAXONOMY_VERSION
    assert "skill_coverage" in matched_job["component_scores"]
    assert applicant_matches.json()["source_version"] == "backend-v1"

    roadmap = client.post(
        "/api/v1/roadmaps",
        json={
            "title": "Close the SQL gap",
            "taxonomy_version": settings.TAXONOMY_VERSION,
            "items": [{"skill_id": "SKILL_0002", "taxonomy_version": settings.TAXONOMY_VERSION, "position": 0}],
        },
        headers=auth(applicant_token),
    )
    assert roadmap.status_code == 201, roadmap.text
    assert roadmap.json()["applicant_id"] == applicant_id
    assert client.get(f"/api/v1/roadmaps/{roadmap.json()['id']}", headers=auth(other_applicant_token)).status_code == 404

    candidates = client.get(f"/api/v1/matching/candidates/{job_id}", headers=auth(recruiter_token))
    assert candidates.status_code == 200, candidates.text
    candidate_match = next(item for item in candidates.json()["data"] if item["candidate_id"] == applicant_id)
    assert candidate_match["component_scores"]
    assert candidate_match["explanation"]
    assert client.get(f"/api/v1/matching/candidates/{job_id}", headers=auth(applicant_token)).status_code == 403

    other_recruiter_token, _ = register(client, "e2e-other-recruiter@example.com", "recruiter")
    assert client.post(
        "/api/v1/recruiter/company",
        json={"company_name": "Other E2E Systems"},
        headers=auth(other_recruiter_token),
    ).status_code == 201
    assert client.get(f"/api/v1/matching/candidates/{job_id}", headers=auth(other_recruiter_token)).status_code == 404

    shortlist = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": applicant_id, "match_score": candidate_match["score"]},
        headers=auth(recruiter_token),
    )
    assert shortlist.status_code == 201, shortlist.text
    assert shortlist.json()["match_score"] == candidate_match["score"]
    assert client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": applicant_id},
        headers=auth(recruiter_token),
    ).status_code == 409


def test_government_workflow_is_read_only_and_role_protected(client: TestClient):
    government_token, _ = register(client, "e2e-government@example.com", "government")
    admin_token, _ = register(client, "e2e-admin@example.com", "admin")
    applicant_token, _ = register(client, "e2e-government-applicant@example.com", "applicant")
    recruiter_token, _ = register(client, "e2e-government-recruiter@example.com", "recruiter")

    db = TestingSessionLocal()
    try:
        users_before = db.query(User).count()
    finally:
        db.close()
    for path in ("demand", "courses", "training-gaps"):
        response = client.get(f"/api/v1/government/{path}", headers=auth(government_token))
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["meta"]["taxonomy_version"] == settings.TAXONOMY_VERSION
        assert body["source_version"]
        assert "generated_at" in body
        assert isinstance(body["warnings"], list)
    assert client.get("/api/v1/government/demand", headers=auth(admin_token)).status_code == 200
    for token in (applicant_token, recruiter_token):
        assert client.get("/api/v1/government/demand", headers=auth(token)).status_code == 403
    assert client.get("/api/v1/government/demand").status_code == 403
    db = TestingSessionLocal()
    try:
        assert db.query(User).count() == users_before
    finally:
        db.close()
