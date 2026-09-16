"""Focused tests for recruiter shortlist foundation."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.company import Company
from app.models.job import Job
from app.models.shortlist import Shortlist
from app.models.user import Role, User
from app.core.security import create_access_token, hash_password

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
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
        json={"email": email, "password": "password123", "full_name": f"User {email}", "role": role},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return body["access_token"], body["data"]["id"]


def create_recruiter_and_job(client: TestClient, email_prefix: str) -> tuple[str, int, int]:
    token, _ = register(client, f"{email_prefix}@company.com", "recruiter")
    company_res = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": f"{email_prefix} Corp"},
        headers=auth(token),
    )
    assert company_res.status_code == 201, company_res.text
    company_id = company_res.json()["id"]

    job_res = client.post(
        "/api/v1/jobs",
        json={
            "title": f"Engineer at {email_prefix}",
            "status": "published",
            "experience_min": 2,
            "experience_max": 5,
        },
        headers=auth(token),
    )
    assert job_res.status_code == 201, job_res.text
    job_id = job_res.json()["id"]
    return token, company_id, job_id


def test_recruiter_can_shortlist_candidate_for_owned_job(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "acme")
    _, cand_id = register(client, "cand1@test.com", "applicant")

    res = client.post(
        "/api/v1/shortlists",
        json={
            "job_id": job_id,
            "candidate_id": cand_id,
            "notes": "Strong candidate with full-stack skills.",
            "match_score": 0.85,
        },
        headers=auth(token),
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["job_id"] == job_id
    assert data["candidate_id"] == cand_id
    assert data["notes"] == "Strong candidate with full-stack skills."
    assert data["match_score"] == 0.85
    assert data["candidate"] is not None
    assert data["candidate"]["id"] == cand_id
    assert data["candidate"]["email"] == "cand1@test.com"


def test_duplicate_shortlist_returns_409_conflict(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "beta")
    _, cand_id = register(client, "cand2@test.com", "applicant")

    res1 = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token),
    )
    assert res1.status_code == 201, res1.text

    res2 = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token),
    )
    assert res2.status_code == 409, res2.text
    assert "already shortlisted" in res2.json()["detail"].lower()


def test_database_unique_constraint_on_job_and_candidate():
    db: Session = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "cand1@test.com").first()
        job = db.query(Job).first()
        assert user is not None and job is not None

        # Attempt to insert a duplicate shortlist entry directly into DB
        entry1 = Shortlist(job_id=job.id, candidate_id=user.id)
        entry2 = Shortlist(job_id=job.id, candidate_id=user.id)
        # Entry1 may already exist from first test, so catch IntegrityError
        with pytest.raises(IntegrityError):
            db.add(entry1)
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_recruiter_cannot_shortlist_for_other_company_job(client: TestClient):
    token_a, _, job_a = create_recruiter_and_job(client, "comp_a")
    token_b, _, _ = create_recruiter_and_job(client, "comp_b")
    _, cand_id = register(client, "cand3@test.com", "applicant")

    res = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_a, "candidate_id": cand_id},
        headers=auth(token_b),
    )
    assert res.status_code == 404, res.text
    assert "Job not found" in res.json()["detail"]


def test_recruiter_without_company_cannot_shortlist(client: TestClient):
    token_no_comp, _ = register(client, "nocompany@recruiter.com", "recruiter")
    _, _, job_id = create_recruiter_and_job(client, "comp_c")
    _, cand_id = register(client, "cand4@test.com", "applicant")

    res = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token_no_comp),
    )
    assert res.status_code == 403, res.text
    assert "company profile" in res.json()["detail"].lower()


def test_nonexistent_candidate_returns_404(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_d")

    res = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": 999999},
        headers=auth(token),
    )
    assert res.status_code == 404, res.text
    assert "Candidate not found" in res.json()["detail"]


def test_non_applicant_candidate_rejected_with_422(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_e")
    recruiter_token, recruiter_id = register(client, "otherrecruiter@test.com", "recruiter")

    res = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": recruiter_id},
        headers=auth(token),
    )
    assert res.status_code == 422, res.text
    assert "applicant" in res.json()["detail"].lower()


def test_invalid_match_score_rejected_with_422(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_f")
    _, cand_id = register(client, "cand5@test.com", "applicant")

    res_high = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id, "match_score": 1.5},
        headers=auth(token),
    )
    assert res_high.status_code == 422

    res_neg = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id, "match_score": -0.1},
        headers=auth(token),
    )
    assert res_neg.status_code == 422


def test_list_shortlists_for_job(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_g")
    _, cand1 = register(client, "cand_g1@test.com", "applicant")
    _, cand2 = register(client, "cand_g2@test.com", "applicant")

    client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand1, "notes": "Cand 1"},
        headers=auth(token),
    )
    client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand2, "notes": "Cand 2"},
        headers=auth(token),
    )

    # Test GET /shortlists/job/{job_id}
    res = client.get(f"/api/v1/shortlists/job/{job_id}", headers=auth(token))
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) == 2
    cand_ids = {item["candidate_id"] for item in data}
    assert cand_ids == {cand1, cand2}
    assert all(item["candidate"]["email"] is not None for item in data)

    # Test GET /shortlists?job_id={job_id}
    res_query = client.get(f"/api/v1/shortlists?job_id={job_id}", headers=auth(token))
    assert res_query.status_code == 200, res_query.text
    assert len(res_query.json()) == 2


def test_list_shortlists_for_unowned_job_returns_404(client: TestClient):
    _, _, job_a = create_recruiter_and_job(client, "comp_h1")
    token_b, _, _ = create_recruiter_and_job(client, "comp_h2")

    res = client.get(f"/api/v1/shortlists/job/{job_a}", headers=auth(token_b))
    assert res.status_code == 404, res.text


def test_list_all_shortlists_scoped_to_recruiter_company(client: TestClient):
    token_a, _, job_a = create_recruiter_and_job(client, "comp_i1")
    token_b, _, job_b = create_recruiter_and_job(client, "comp_i2")
    _, cand_a = register(client, "cand_i1@test.com", "applicant")
    _, cand_b = register(client, "cand_i2@test.com", "applicant")

    client.post("/api/v1/shortlists", json={"job_id": job_a, "candidate_id": cand_a}, headers=auth(token_a))
    client.post("/api/v1/shortlists", json={"job_id": job_b, "candidate_id": cand_b}, headers=auth(token_b))

    res_a = client.get("/api/v1/shortlists", headers=auth(token_a))
    assert res_a.status_code == 200
    entries_a = res_a.json()
    assert all(entry["job_id"] == job_a for entry in entries_a)

    res_b = client.get("/api/v1/shortlists", headers=auth(token_b))
    assert res_b.status_code == 200
    entries_b = res_b.json()
    assert all(entry["job_id"] == job_b for entry in entries_b)


def test_get_and_update_shortlist_entry(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_j")
    _, cand_id = register(client, "cand_j@test.com", "applicant")

    created = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id, "notes": "Initial note"},
        headers=auth(token),
    ).json()
    shortlist_id = created["id"]

    # GET single
    res_get = client.get(f"/api/v1/shortlists/{shortlist_id}", headers=auth(token))
    assert res_get.status_code == 200
    assert res_get.json()["notes"] == "Initial note"

    # PATCH note
    res_patch = client.patch(
        f"/api/v1/shortlists/{shortlist_id}",
        json={"notes": "Updated note after interview"},
        headers=auth(token),
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["notes"] == "Updated note after interview"


def test_delete_shortlist_by_id(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_k")
    _, cand_id = register(client, "cand_k@test.com", "applicant")

    created = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token),
    ).json()
    shortlist_id = created["id"]

    # Delete
    del_res = client.delete(f"/api/v1/shortlists/{shortlist_id}", headers=auth(token))
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/api/v1/shortlists/{shortlist_id}", headers=auth(token))
    assert get_res.status_code == 404


def test_delete_shortlist_by_job_and_candidate(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_l")
    _, cand_id = register(client, "cand_l@test.com", "applicant")

    client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token),
    )

    # Delete by job & candidate
    del_res = client.delete(f"/api/v1/shortlists/job/{job_id}/candidate/{cand_id}", headers=auth(token))
    assert del_res.status_code == 204

    # Second delete returns 404
    del_res2 = client.delete(f"/api/v1/shortlists/job/{job_id}/candidate/{cand_id}", headers=auth(token))
    assert del_res2.status_code == 404


def test_delete_shortlist_for_other_company_job_returns_404(client: TestClient):
    token_a, _, job_a = create_recruiter_and_job(client, "comp_m1")
    token_b, _, _ = create_recruiter_and_job(client, "comp_m2")
    _, cand_id = register(client, "cand_m@test.com", "applicant")

    created = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_a, "candidate_id": cand_id},
        headers=auth(token_a),
    ).json()

    del_res = client.delete(f"/api/v1/shortlists/{created['id']}", headers=auth(token_b))
    assert del_res.status_code == 404


def test_applicant_role_forbidden_from_shortlist_endpoints(client: TestClient):
    token_rec, _, job_id = create_recruiter_and_job(client, "comp_n")
    token_app, cand_id = register(client, "cand_n@test.com", "applicant")

    # Applicant cannot POST
    res_post = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token_app),
    )
    assert res_post.status_code == 403

    # Applicant cannot GET
    res_get = client.get(f"/api/v1/shortlists/job/{job_id}", headers=auth(token_app))
    assert res_get.status_code == 403

    # Applicant cannot DELETE
    res_del = client.delete(f"/api/v1/shortlists/job/{job_id}/candidate/{cand_id}", headers=auth(token_app))
    assert res_del.status_code == 403


def test_unauthenticated_requests_are_rejected(client: TestClient):
    # Missing token returns 403 per NexusAI deps.py convention
    res_no_auth = client.post("/api/v1/shortlists", json={"job_id": 1, "candidate_id": 1})
    assert res_no_auth.status_code == 403
    assert "Not authenticated" in res_no_auth.json()["detail"]

    # Invalid token returns 401
    res_bad_token = client.get("/api/v1/shortlists", headers=auth("invalid-token-xyz"))
    assert res_bad_token.status_code == 401


def test_admin_can_manage_any_shortlist(client: TestClient):
    token_rec, _, job_id = create_recruiter_and_job(client, "comp_o")
    db: Session = TestingSessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        admin = User(
            email="admin_shortlist@nexusai.com",
            password_hash=hash_password("password123"),
            full_name="Admin Shortlist",
            role_id=admin_role.id,
        )
        db.add(admin)
        db.commit()
        token_admin = create_access_token(admin.id, "admin")
    finally:
        db.close()
    _, cand_id = register(client, "cand_o@test.com", "applicant")

    # Admin shortlists candidate for recruiter's job
    res_post = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id, "notes": "Admin shortlist"},
        headers=auth(token_admin),
    )
    assert res_post.status_code == 201, res_post.text
    shortlist_id = res_post.json()["id"]

    # Admin reads shortlist for the job
    res_get = client.get(f"/api/v1/shortlists/job/{job_id}", headers=auth(token_admin))
    assert res_get.status_code == 200
    assert any(s["id"] == shortlist_id for s in res_get.json())

    # Admin deletes shortlist entry
    res_del = client.delete(f"/api/v1/shortlists/{shortlist_id}", headers=auth(token_admin))
    assert res_del.status_code == 204


def test_cascade_delete_job_removes_shortlist(client: TestClient):
    token, _, job_id = create_recruiter_and_job(client, "comp_p")
    _, cand_id = register(client, "cand_p@test.com", "applicant")

    res = client.post(
        "/api/v1/shortlists",
        json={"job_id": job_id, "candidate_id": cand_id},
        headers=auth(token),
    )
    assert res.status_code == 201
    shortlist_id = res.json()["id"]

    # Delete the job
    del_job_res = client.delete(f"/api/v1/jobs/{job_id}", headers=auth(token))
    assert del_job_res.status_code == 204

    # Verify shortlist entry was cascaded and removed
    db: Session = TestingSessionLocal()
    try:
        entry = db.query(Shortlist).filter(Shortlist.id == shortlist_id).first()
        assert entry is None
    finally:
        db.close()
