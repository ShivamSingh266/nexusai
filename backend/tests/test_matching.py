"""Focused tests for deterministic candidate/job matching."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.applicant_profile import ApplicantProfile
from app.models.applicant_skill import ApplicantSkill
from app.models.canonical_skill import CanonicalSkill
from app.models.company import Company
from app.models.job import Job
from app.models.job_observation import JobLocationObservation
from app.models.job_skill import JobSkill
from app.models.user import Role, User

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
    db: Session = TestingSessionLocal()
    roles = [Role(name=name, description=name) for name in ["applicant", "recruiter", "admin"]]
    db.add_all(roles)
    for number in range(1, 4):
        db.add(
            CanonicalSkill(
                skill_id=f"SKILL_{number:04d}",
                canonical_name=f"Skill {number}",
                normalized_name=f"skill {number}",
                category="technical",
                source="ESCO",
                taxonomy_version="v1.2.1",
            )
        )
    db.commit()
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
        json={"email": email, "password": "password123", "full_name": role, "role": role},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["data"]["id"]


def create_recruiter_job(
    client: TestClient,
    email: str,
    *,
    skill_ids: list[str],
    role_importances: list[float] | None = None,
    education_requirement: str | None = "Computer Science",
    location: str | None = "Pune",
) -> tuple[str, dict]:
    token, _ = register(client, email, "recruiter")
    company = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": email.split("@")[0]},
        headers=auth(token),
    )
    assert company.status_code == 201, company.text
    job = client.post(
        "/api/v1/jobs",
        json={
            "title": "Matching Engineer",
            "status": "published",
            "experience_min": 2,
            "experience_max": 5,
            "education_requirement": education_requirement,
            "location": location,
        },
        headers=auth(token),
    )
    assert job.status_code == 201, job.text
    importances = role_importances or [1.0 for _ in skill_ids]
    for skill_id, importance in zip(skill_ids, importances):
        response = client.post(
            f"/api/v1/jobs/{job.json()['id']}/skills",
            json={
                "skill_id": skill_id,
                "taxonomy_version": "v1.2.1",
                "role_importance": importance,
            },
            headers=auth(token),
        )
        assert response.status_code == 201, response.text
    return token, job.json()


def add_candidate_data(db: Session, candidate_id: int, skill_ids: list[str]):
    db.add(
        ApplicantProfile(
            user_id=candidate_id,
            location="Pune",
            education="Computer Science",
            experience_years=3,
        )
    )
    db.add_all(
        [
            ApplicantSkill(
                user_id=candidate_id,
                skill_name=skill_id,
                skill_id=skill_id,
                taxonomy_version="v1.2.1",
                proficiency_level="intermediate",
            )
            for skill_id in skill_ids
        ]
    )
    db.commit()


def test_candidate_matching_scores_components_and_renormalizes(
    client: TestClient,
):
    candidate_token, candidate_id = register(
        client,
        "match-candidate@example.com",
        "applicant",
    )

    db = TestingSessionLocal()
    add_candidate_data(
        db,
        candidate_id,
        ["SKILL_0001"],
    )

    candidate_profile = (
        db.query(ApplicantProfile)
        .filter(ApplicantProfile.user_id == candidate_id)
        .one()
    )
    candidate_profile.bio = (
        "Software engineer building matching systems and software applications."
    )
    db.commit()
    db.close()

    _, job = create_recruiter_job(
        client,
        "match-owner@example.com",
        skill_ids=["SKILL_0001", "SKILL_0002"],
        role_importances=[1.0, 0.5],
    )

    db = TestingSessionLocal()
    persisted_job = db.get(Job, job["id"])
    assert persisted_job is not None
    persisted_job.description = (
        "Software engineer building matching systems and software applications."
    )
    db.commit()
    db.close()

    response = client.get(
        "/api/v1/matching/jobs",
        headers=auth(candidate_token),
    )
    assert response.status_code == 200, response.text

    body = response.json()
    result = next(
        item
        for item in body["data"]
        if item["job_id"] == job["id"]
    )

    assert result["component_scores"]["skill_coverage"] == pytest.approx(2 / 3)
    assert "semantic_similarity" in result["component_scores"]

    semantic = result["component_scores"]["semantic_similarity"]
    assert semantic > 0.0

    assert set(result["available_components"]) == {
        "skill_coverage",
        "semantic_similarity",
        "experience",
        "education",
        "location_work_mode",
    }

    assert "semantic_similarity" not in result["omitted_components"]

    expected_score = (
        (2 / 3) * 0.60
        + semantic * 0.20
        + 1.0 * 0.10
        + 1.0 * 0.05
        + 1.0 * 0.05
    )
    assert result["score"] == pytest.approx(expected_score)

    assert not any(
        "Semantic similarity is unavailable" in warning
        for warning in result["warnings"]
    )

    assert result["taxonomy_version"] == "v1.2.1"
    assert result["explanation"]


def test_recruiter_matching_candidates_and_deterministic_output(client: TestClient):
    owner_token, job = create_recruiter_job(client, "candidate-owner@example.com", skill_ids=["SKILL_0001"])
    candidate_token, candidate_id = register(client, "ranked-candidate@example.com", "applicant")
    db = TestingSessionLocal()
    add_candidate_data(db, candidate_id, ["SKILL_0001"])
    db.close()
    recruiter_token, _ = register(client, "viewer-recruiter@example.com", "recruiter")
    company = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": "viewer-company"},
        headers=auth(recruiter_token),
    )
    assert company.status_code == 201

    # The viewer recruiter does not own the job and must not see it.
    denied = client.get(f"/api/v1/matching/candidates/{job['id']}", headers=auth(recruiter_token))
    assert denied.status_code == 404
    first = client.get(f"/api/v1/matching/candidates/{job['id']}", headers=auth(owner_token))
    second = client.get(f"/api/v1/matching/candidates/{job['id']}", headers=auth(owner_token))
    assert first.status_code == 200, first.text
    assert first.json()["data"] == second.json()["data"]
    assert candidate_id in {item["candidate_id"] for item in first.json()["data"]}
    assert candidate_token


def test_missing_candidate_profile_and_rbac(client: TestClient):
    applicant_token, _ = register(client, "no-profile@example.com", "applicant")
    assert client.get("/api/v1/matching/jobs", headers=auth(applicant_token)).status_code == 404
    recruiter_token, _ = register(client, "not-applicant@example.com", "recruiter")
    assert client.get("/api/v1/matching/jobs", headers=auth(recruiter_token)).status_code == 403
    assert client.get("/api/v1/matching/candidates/999999", headers=auth(applicant_token)).status_code == 403


def test_no_canonical_candidate_skills_and_no_job_skills(client: TestClient):
    candidate_token, candidate_id = register(client, "no-skills@example.com", "applicant")
    db = TestingSessionLocal()
    db.add(ApplicantProfile(user_id=candidate_id, location="Pune"))
    db.commit()
    db.close()
    assert client.get("/api/v1/matching/jobs", headers=auth(candidate_token)).status_code == 422

    recruiter_token, _ = register(client, "empty-job-owner@example.com", "recruiter")
    company = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": "empty-job-company"},
        headers=auth(recruiter_token),
    )
    assert company.status_code == 201
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Empty Matching Job", "status": "published"},
        headers=auth(recruiter_token),
    )
    assert job.status_code == 201
    assert client.get(
        f"/api/v1/matching/candidates/{job.json()['id']}",
        headers=auth(recruiter_token),
    ).status_code == 422


def test_taxonomy_mismatch_is_reported(client: TestClient):
    candidate_token, candidate_id = register(client, "taxonomy-match@example.com", "applicant")
    db = TestingSessionLocal()
    add_candidate_data(db, candidate_id, ["SKILL_0001"])
    db.close()
    recruiter_token, _ = register(client, "taxonomy-owner@example.com", "recruiter")
    company = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": "taxonomy-company"},
        headers=auth(recruiter_token),
    )
    assert company.status_code == 201
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Mismatched Job", "status": "published"},
        headers=auth(recruiter_token),
    )
    assert job.status_code == 201
    db = TestingSessionLocal()
    db.add(JobSkill(job_id=job.json()["id"], skill_id="SKILL_0001", taxonomy_version="v9.9.9"))
    db.commit()
    db.close()
    response = client.get("/api/v1/matching/jobs", headers=auth(candidate_token))
    assert response.status_code == 200
    assert all(item["job_id"] != job.json()["id"] for item in response.json()["data"])
    assert any("Taxonomy version mismatch" in warning for warning in response.json()["warnings"])


def test_candidate_with_no_matching_skills_scores_zero_coverage(client: TestClient):
    candidate_token, candidate_id = register(client, "no-match-cand@example.com", "applicant")
    db = TestingSessionLocal()
    add_candidate_data(db, candidate_id, ["SKILL_0003"])
    db.close()
    _, job = create_recruiter_job(
        client,
        "no-match-owner@example.com",
        skill_ids=["SKILL_0001", "SKILL_0002"],
    )

    response = client.get("/api/v1/matching/jobs", headers=auth(candidate_token))
    assert response.status_code == 200
    result = next(item for item in response.json()["data"] if item["job_id"] == job["id"])
    assert result["component_scores"]["skill_coverage"] == 0.0


def test_unavailable_components_renormalize_correctly(client: TestClient):
    # Candidate with NO experience, NO education, NO location
    candidate_token, candidate_id = register(client, "bare-cand@example.com", "applicant")
    db = TestingSessionLocal()
    db.add(ApplicantProfile(user_id=candidate_id))
    db.add(
        ApplicantSkill(
            user_id=candidate_id,
            skill_name="SKILL_0001",
            skill_id="SKILL_0001",
            taxonomy_version="v1.2.1",
        )
    )
    db.commit()
    db.close()

    # Job with skills only (no exp, edu, loc)
    token, _ = register(client, "bare-job-owner@example.com", "recruiter")
    company = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": "bare-company"},
        headers=auth(token),
    )
    assert company.status_code == 201
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Bare Job", "status": "published"},
        headers=auth(token),
    )
    assert job.status_code == 201
    client.post(
        f"/api/v1/jobs/{job.json()['id']}/skills",
        json={"skill_id": "SKILL_0001", "taxonomy_version": "v1.2.1", "role_importance": 1.0},
        headers=auth(token),
    )

    response = client.get("/api/v1/matching/jobs", headers=auth(candidate_token))
    assert response.status_code == 200
    result = next(item for item in response.json()["data"] if item["job_id"] == job.json()["id"])
    assert result["available_components"] == ["skill_coverage"]
    assert set(result["omitted_components"]) == {
        "semantic_similarity",
        "experience",
        "education",
        "location_work_mode",
    }
    # With only skill_coverage available, score == skill_coverage (1.0)
    assert result["score"] == pytest.approx(1.0)


def test_deterministic_tie_breaking(client: TestClient):
    candidate_token, candidate_id = register(client, "tie-cand@example.com", "applicant")
    db = TestingSessionLocal()
    add_candidate_data(db, candidate_id, ["SKILL_0001"])
    db.close()

    # Create two identical jobs
    _, job_a = create_recruiter_job(client, "tie-owner-a@example.com", skill_ids=["SKILL_0001"])
    _, job_b = create_recruiter_job(client, "tie-owner-b@example.com", skill_ids=["SKILL_0001"])

    response = client.get("/api/v1/matching/jobs", headers=auth(candidate_token))
    assert response.status_code == 200
    jobs_in_resp = [
        item for item in response.json()["data"]
        if item["job_id"] in (job_a["id"], job_b["id"])
    ]
    assert len(jobs_in_resp) == 2
    assert jobs_in_resp[0]["score"] == jobs_in_resp[1]["score"]
    # Tied scores must sort by job_id ascending
    assert jobs_in_resp[0]["job_id"] < jobs_in_resp[1]["job_id"]


def test_core_match_candidate_to_job_components():
    from app.core.matching import match_candidate_to_job
    from app.core.representations import SkillProfile, SkillProfileSkill

    candidate = SkillProfile(
        subject_id=1,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=(
            SkillProfileSkill(skill_id="SKILL_0001", taxonomy_version="v1.2.1"),
        ),
        experience_years=4.0,
        education="B.Tech Computer Science",
        location="Pune",
    )

    job = Job(
        id=1,
        company_id=1,
        title="Software Engineer",
        status="published",
        experience_min=2.0,
        experience_max=5.0,
        education_requirement="Computer Science",
        location="Pune",
        work_mode="onsite",
    )
    job.job_skills = [
        JobSkill(id=1, job_id=1, skill_id="SKILL_0001", taxonomy_version="v1.2.1", role_importance=1.0),
        JobSkill(id=2, job_id=1, skill_id="SKILL_0002", taxonomy_version="v1.2.1", role_importance=1.0),
    ]

    result = match_candidate_to_job(candidate, job)
    assert result.component_scores["skill_coverage"] == 0.5
    assert result.component_scores["experience"] == 1.0
    assert result.component_scores["education"] == 1.0
    assert result.component_scores["location_work_mode"] == 1.0
    # Available weights: 0.6 + 0.1 + 0.05 + 0.05 = 0.8
    # Score: (0.5*0.6 + 1.0*0.1 + 1.0*0.05 + 1.0*0.05) / 0.8 = (0.3 + 0.1 + 0.05 + 0.05) / 0.8 = 0.5 / 0.8 = 0.625
    assert result.score == pytest.approx(0.625)


def test_core_matching_accepts_any_normalized_market_district_without_weight_changes():
    from app.core.matching import MATCHING_WEIGHTS, match_candidate_to_job
    from app.core.representations import SkillProfile, SkillProfileSkill

    candidate = SkillProfile(
        subject_id=1,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=(SkillProfileSkill(skill_id="SKILL_0001", taxonomy_version="v1.2.1"),),
        location="Mumbai",
    )
    job = Job(id=1, company_id=1, title="Market Engineer", status="published")
    job.location_observations = [
        JobLocationObservation(job_id=1, district="Pune"),
        JobLocationObservation(job_id=1, district="Mumbai"),
    ]
    job.job_skills = [
        JobSkill(
            id=1,
            job_id=1,
            skill_id="SKILL_0001",
            taxonomy_version="v1.2.1",
            role_importance=1.0,
        )
    ]

    result = match_candidate_to_job(candidate, job)

    assert result.component_scores["location_work_mode"] == 1.0
    assert MATCHING_WEIGHTS == {
        "skill_coverage": 0.60,
        "semantic_similarity": 0.20,
        "experience": 0.10,
        "education": 0.05,
        "location_work_mode": 0.05,
    }


def test_core_match_candidate_experience_out_of_range():
    from app.core.matching import match_candidate_to_job
    from app.core.representations import SkillProfile, SkillProfileSkill

    candidate = SkillProfile(
        subject_id=1,
        subject_type="applicant",
        taxonomy_version="v1.2.1",
        skills=(SkillProfileSkill(skill_id="SKILL_0001", taxonomy_version="v1.2.1"),),
        experience_years=1.0,  # Below min of 3.0
    )
    job = Job(
        id=1,
        company_id=1,
        title="Senior Engineer",
        experience_min=3.0,
    )
    job.job_skills = [
        JobSkill(id=1, job_id=1, skill_id="SKILL_0001", taxonomy_version="v1.2.1", role_importance=1.0),
    ]
    result = match_candidate_to_job(candidate, job)
    assert result.component_scores["experience"] == 0.0
    # Available weights: 0.6 (skill) + 0.1 (exp) = 0.7
    # Score: (1.0*0.6 + 0.0*0.1) / 0.7 = 0.6 / 0.7
    assert result.score == pytest.approx(0.6 / 0.7)
