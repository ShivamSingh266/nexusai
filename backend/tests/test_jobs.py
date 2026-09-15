"""
Tests for the Jobs module — /api/v1/jobs

Coverage:
  A. CRUD (create, read, update, delete)
  B. RBAC (recruiter, applicant, government, unauthenticated, admin)
  C. Status lifecycle (draft → published → closed)
  D. Draft visibility (applicants CANNOT see draft/closed jobs)
  E. Cross-company isolation (recruiter cannot touch another company's jobs)
  F. Filters (title, location, employment_type, work_mode, status)
  G. Pagination
  H. Validation errors (missing title, inverted salary range, bad status)
  I. Regression (all existing endpoints still work)

Strategy:
  - in-memory SQLite, StaticPool
  - get_db override applied + removed inside autouse fixture (no cross-module leak)
  - All state created via the API; direct DB manipulation only for verification
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.api.deps import get_db
from app.models.user import Role

# ---------------------------------------------------------------------------
# Isolated test database
# ---------------------------------------------------------------------------

_JOBS_TEST_DB_URL = "sqlite://"

_jobs_engine = create_engine(
    _JOBS_TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_JobsTestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_jobs_engine,
)


def _jobs_override_get_db():
    db = _JobsTestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def setup_jobs_database():
    """Create schema, seed roles, apply override; tear down after module."""
    Base.metadata.create_all(bind=_jobs_engine)

    db: Session = _JobsTestingSessionLocal()
    try:
        for role_name in ["applicant", "recruiter", "government", "admin"]:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name, description=role_name))
        db.commit()
    finally:
        db.close()

    _previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _jobs_override_get_db

    yield

    if _previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous

    Base.metadata.drop_all(bind=_jobs_engine)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(
    client: TestClient, email: str, password: str, role: str
) -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User", "role": role},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_company(client: TestClient, token: str, name: str = "Acme Corp") -> dict:
    resp = client.post(
        "/api/v1/recruiter/company",
        json={"company_name": name, "industry": "Technology"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_job(
    client: TestClient,
    token: str,
    *,
    title: str = "Software Engineer",
    status: str = "draft",
    **kwargs,
) -> dict:
    payload = {"title": title, "status": status, **kwargs}
    resp = client.post("/api/v1/jobs", json=payload, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# A. CRUD tests
# ---------------------------------------------------------------------------


class TestJobCRUD:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        token = _register_and_login(client, "crud_recruiter@test.com", "password123", "recruiter")
        _create_company(client, token, "CRUD Corp")
        return token

    def test_create_job_returns_201(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={
                "title": "Backend Engineer",
                "description": "Build APIs",
                "location": "Nairobi",
                "employment_type": "full_time",
                "work_mode": "hybrid",
                "experience_min": 2.0,
                "experience_max": 5.0,
                "salary_min": 60000,
                "salary_max": 100000,
                "status": "draft",
            },
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["title"] == "Backend Engineer"
        assert body["status"] == "draft"
        assert body["company_id"] is not None
        assert body["id"] is not None
        assert "created_at" in body
        assert "updated_at" in body

    def test_get_own_draft_job_as_recruiter(self, client: TestClient, recruiter_token: str):
        """Recruiter can fetch their own draft job by ID."""
        job = _create_job(client, recruiter_token, title="Draft Job", status="draft")
        resp = client.get(f"/api/v1/jobs/{job['id']}", headers=_auth(recruiter_token))
        assert resp.status_code == 200
        assert resp.json()["title"] == "Draft Job"

    def test_list_own_jobs_as_recruiter(self, client: TestClient, recruiter_token: str):
        resp = client.get("/api/v1/jobs", headers=_auth(recruiter_token))
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body
        assert "page" in body
        assert "page_size" in body
        assert "total_pages" in body
        assert body["total"] >= 1

    def test_patch_job_updates_fields(self, client: TestClient, recruiter_token: str):
        job = _create_job(client, recruiter_token, title="Old Title")
        resp = client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"title": "New Title", "location": "Lagos"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "New Title"
        assert body["location"] == "Lagos"
        assert body["status"] == "draft"  # unchanged

    def test_patch_unset_fields_not_nullified(self, client: TestClient, recruiter_token: str):
        """PATCH semantics: only provided fields change."""
        job = _create_job(
            client,
            recruiter_token,
            title="Stable Job",
            location="Mombasa",
            employment_type="contract",
        )
        resp = client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"title": "Stable Job Updated"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["location"] == "Mombasa"  # unchanged
        assert body["employment_type"] == "contract"  # unchanged

    def test_delete_job_returns_204(self, client: TestClient, recruiter_token: str):
        job = _create_job(client, recruiter_token, title="To Delete")
        resp = client.delete(f"/api/v1/jobs/{job['id']}", headers=_auth(recruiter_token))
        assert resp.status_code == 204

        # Confirm it's gone from recruiter's list
        get_resp = client.get(f"/api/v1/jobs/{job['id']}", headers=_auth(recruiter_token))
        assert get_resp.status_code == 404

    def test_delete_nonexistent_job_returns_404(self, client: TestClient, recruiter_token: str):
        resp = client.delete("/api/v1/jobs/999999", headers=_auth(recruiter_token))
        assert resp.status_code == 404

    def test_patch_nonexistent_job_returns_404(self, client: TestClient, recruiter_token: str):
        resp = client.patch(
            "/api/v1/jobs/999999",
            json={"title": "Ghost"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 404

    def test_default_status_is_draft(self, client: TestClient, recruiter_token: str):
        """Creating a job without an explicit status defaults to 'draft'."""
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "No Status Job"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "draft"


# ---------------------------------------------------------------------------
# B. RBAC tests
# ---------------------------------------------------------------------------


class TestJobRBAC:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        token = _register_and_login(client, "rbac_recruiter@test.com", "password123", "recruiter")
        _create_company(client, token, "RBAC Corp")
        return token

    @pytest.fixture(scope="class")
    def applicant_token(self, client: TestClient) -> str:
        return _register_and_login(client, "rbac_applicant@test.com", "password123", "applicant")

    @pytest.fixture(scope="class")
    def government_token(self, client: TestClient) -> str:
        return _register_and_login(client, "rbac_government@test.com", "password123", "government")

    @pytest.fixture(scope="class")
    def published_job_id(self, client: TestClient, recruiter_token: str) -> int:
        job = _create_job(client, recruiter_token, title="Public Job", status="published")
        return job["id"]

    def test_applicant_cannot_create_job(
        self, client: TestClient, applicant_token: str
    ):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Hack Job"},
            headers=_auth(applicant_token),
        )
        assert resp.status_code == 403

    def test_government_cannot_create_job(
        self, client: TestClient, government_token: str
    ):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Hack Job"},
            headers=_auth(government_token),
        )
        assert resp.status_code == 403

    def test_applicant_cannot_patch_job(
        self, client: TestClient, applicant_token: str, published_job_id: int
    ):
        resp = client.patch(
            f"/api/v1/jobs/{published_job_id}",
            json={"title": "Modified"},
            headers=_auth(applicant_token),
        )
        assert resp.status_code == 403

    def test_applicant_cannot_delete_job(
        self, client: TestClient, applicant_token: str, published_job_id: int
    ):
        resp = client.delete(
            f"/api/v1/jobs/{published_job_id}",
            headers=_auth(applicant_token),
        )
        assert resp.status_code == 403

    def test_applicant_can_list_published_jobs(
        self, client: TestClient, applicant_token: str, published_job_id: int
    ):
        resp = client.get("/api/v1/jobs", headers=_auth(applicant_token))
        assert resp.status_code == 200
        ids = [j["id"] for j in resp.json()["data"]]
        assert published_job_id in ids

    def test_applicant_can_get_published_job(
        self, client: TestClient, applicant_token: str, published_job_id: int
    ):
        resp = client.get(f"/api/v1/jobs/{published_job_id}", headers=_auth(applicant_token))
        assert resp.status_code == 200

    def test_unauthenticated_can_list_published_jobs(
        self, client: TestClient, published_job_id: int
    ):
        resp = client.get("/api/v1/jobs")
        assert resp.status_code == 200
        ids = [j["id"] for j in resp.json()["data"]]
        assert published_job_id in ids

    def test_unauthenticated_can_get_published_job(
        self, client: TestClient, published_job_id: int
    ):
        resp = client.get(f"/api/v1/jobs/{published_job_id}")
        assert resp.status_code == 200

    def test_recruiter_without_company_cannot_create(self, client: TestClient):
        """Recruiter with no company profile gets 403 on create."""
        no_company_token = _register_and_login(
            client, "nocompany_recruiter@test.com", "password123", "recruiter"
        )
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Some Job"},
            headers=_auth(no_company_token),
        )
        assert resp.status_code == 403

    def test_government_can_list_published_jobs(
        self, client: TestClient, government_token: str
    ):
        resp = client.get("/api/v1/jobs", headers=_auth(government_token))
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# C. Status lifecycle tests
# ---------------------------------------------------------------------------


class TestJobStatus:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        token = _register_and_login(client, "status_recruiter@test.com", "password123", "recruiter")
        _create_company(client, token, "Status Corp")
        return token

    def test_publish_job(self, client: TestClient, recruiter_token: str):
        job = _create_job(client, recruiter_token, title="Will Publish")
        assert job["status"] == "draft"

        resp = client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"status": "published"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_close_job(self, client: TestClient, recruiter_token: str):
        job = _create_job(client, recruiter_token, title="Will Close", status="published")
        resp = client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"status": "closed"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    def test_invalid_status_returns_422(self, client: TestClient, recruiter_token: str):
        job = _create_job(client, recruiter_token, title="Bad Status Test")
        resp = client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"status": "pending_review"},  # not a valid value
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# D. Draft visibility — applicants must NOT see draft or closed jobs
# ---------------------------------------------------------------------------


class TestDraftVisibility:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        token = _register_and_login(
            client, "draft_vis_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Draft Vis Corp")
        return token

    @pytest.fixture(scope="class")
    def applicant_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "draft_vis_applicant@test.com", "password123", "applicant"
        )

    def test_applicant_cannot_see_draft_in_list(
        self, client: TestClient, recruiter_token: str, applicant_token: str
    ):
        _create_job(client, recruiter_token, title="Hidden Draft", status="draft")
        resp = client.get("/api/v1/jobs", headers=_auth(applicant_token))
        assert resp.status_code == 200
        titles = [j["title"] for j in resp.json()["data"]]
        assert "Hidden Draft" not in titles

    def test_applicant_cannot_get_draft_by_id(
        self, client: TestClient, recruiter_token: str, applicant_token: str
    ):
        job = _create_job(client, recruiter_token, title="Hidden Draft ID", status="draft")
        resp = client.get(f"/api/v1/jobs/{job['id']}", headers=_auth(applicant_token))
        assert resp.status_code == 404

    def test_applicant_cannot_see_closed_in_list(
        self, client: TestClient, recruiter_token: str, applicant_token: str
    ):
        job = _create_job(client, recruiter_token, title="Closed Job", status="published")
        client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"status": "closed"},
            headers=_auth(recruiter_token),
        )
        resp = client.get("/api/v1/jobs", headers=_auth(applicant_token))
        titles = [j["title"] for j in resp.json()["data"]]
        assert "Closed Job" not in titles

    def test_applicant_cannot_get_closed_by_id(
        self, client: TestClient, recruiter_token: str, applicant_token: str
    ):
        job = _create_job(client, recruiter_token, title="Closed ID Job", status="published")
        client.patch(
            f"/api/v1/jobs/{job['id']}",
            json={"status": "closed"},
            headers=_auth(recruiter_token),
        )
        resp = client.get(f"/api/v1/jobs/{job['id']}", headers=_auth(applicant_token))
        assert resp.status_code == 404

    def test_recruiter_can_see_all_statuses_in_own_list(
        self, client: TestClient, recruiter_token: str
    ):
        """Recruiter sees draft, published, and closed in their own listing."""
        _create_job(client, recruiter_token, title="Recruiter Draft", status="draft")
        pub = _create_job(client, recruiter_token, title="Recruiter Published", status="published")
        client.patch(
            f"/api/v1/jobs/{pub['id']}",
            json={"status": "closed"},
            headers=_auth(recruiter_token),
        )

        resp = client.get("/api/v1/jobs", headers=_auth(recruiter_token))
        assert resp.status_code == 200
        statuses = {j["status"] for j in resp.json()["data"]}
        assert "draft" in statuses
        assert "closed" in statuses


# ---------------------------------------------------------------------------
# E. Cross-company isolation
# ---------------------------------------------------------------------------


class TestCrossCompanyIsolation:
    @pytest.fixture(scope="class")
    def company_a_token(self, client: TestClient) -> str:
        token = _register_and_login(
            client, "company_a_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Company A")
        return token

    @pytest.fixture(scope="class")
    def company_b_token(self, client: TestClient) -> str:
        token = _register_and_login(
            client, "company_b_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Company B")
        return token

    def test_recruiter_a_cannot_get_company_b_draft(
        self, client: TestClient, company_a_token: str, company_b_token: str
    ):
        """Company B's draft job is invisible to Company A's recruiter."""
        job_b = _create_job(client, company_b_token, title="B Draft Job", status="draft")
        resp = client.get(f"/api/v1/jobs/{job_b['id']}", headers=_auth(company_a_token))
        assert resp.status_code == 404

    def test_recruiter_a_cannot_patch_company_b_job(
        self, client: TestClient, company_a_token: str, company_b_token: str
    ):
        job_b = _create_job(client, company_b_token, title="B Patch Target", status="published")
        resp = client.patch(
            f"/api/v1/jobs/{job_b['id']}",
            json={"title": "Hacked by A"},
            headers=_auth(company_a_token),
        )
        assert resp.status_code == 404

    def test_recruiter_a_cannot_delete_company_b_job(
        self, client: TestClient, company_a_token: str, company_b_token: str
    ):
        job_b = _create_job(client, company_b_token, title="B Delete Target", status="published")
        resp = client.delete(
            f"/api/v1/jobs/{job_b['id']}",
            headers=_auth(company_a_token),
        )
        assert resp.status_code == 404

    def test_recruiter_listing_scoped_to_own_company(
        self, client: TestClient, company_a_token: str, company_b_token: str
    ):
        """Recruiter A's listing does not contain Company B's jobs."""
        _create_job(client, company_a_token, title="A Exclusive Job", status="draft")
        _create_job(client, company_b_token, title="B Exclusive Job", status="draft")

        resp = client.get("/api/v1/jobs", headers=_auth(company_a_token))
        titles = [j["title"] for j in resp.json()["data"]]
        assert "A Exclusive Job" in titles
        assert "B Exclusive Job" not in titles

    def test_published_job_from_b_visible_to_applicant_not_a_recruiter(
        self, client: TestClient, company_a_token: str, company_b_token: str
    ):
        """Applicant can see B's published job, but A's recruiter list does not include it."""
        job_b = _create_job(client, company_b_token, title="B Public", status="published")

        # A's recruiter list does not include B's job
        recruiter_resp = client.get("/api/v1/jobs", headers=_auth(company_a_token))
        ids_a = [j["id"] for j in recruiter_resp.json()["data"]]
        assert job_b["id"] not in ids_a

        # Unauthenticated list DOES include B's published job
        public_resp = client.get("/api/v1/jobs")
        ids_public = [j["id"] for j in public_resp.json()["data"]]
        assert job_b["id"] in ids_public


# ---------------------------------------------------------------------------
# F. Filter tests
# ---------------------------------------------------------------------------


class TestJobFilters:
    @pytest.fixture(scope="class")
    def setup(self, client: TestClient):
        """Create a recruiter with company and a variety of published jobs."""
        token = _register_and_login(
            client, "filter_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Filter Corp")

        jobs = [
            {"title": "Python Developer", "location": "Nairobi", "employment_type": "full_time", "work_mode": "remote", "status": "published"},
            {"title": "Java Engineer", "location": "Lagos", "employment_type": "contract", "work_mode": "onsite", "status": "published"},
            {"title": "Python Architect", "location": "Nairobi", "employment_type": "full_time", "work_mode": "hybrid", "status": "published"},
            {"title": "Data Analyst", "location": "Cape Town", "employment_type": "part_time", "work_mode": "remote", "status": "published"},
            {"title": "Secret Draft", "status": "draft"},
        ]
        for j in jobs:
            _create_job(client, token, **j)

        return token

    def test_filter_by_title(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs?title=python")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all("Python" in j["title"] or "python" in j["title"].lower() for j in data)
        assert len(data) >= 2

    def test_filter_by_location(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs?location=Nairobi")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all("Nairobi" in j["location"] for j in data)

    def test_filter_by_employment_type(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs?employment_type=full_time")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(j["employment_type"] == "full_time" for j in data)

    def test_filter_by_work_mode(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs?work_mode=remote")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(j["work_mode"] == "remote" for j in data)

    def test_status_filter_ignored_for_public(self, client: TestClient, setup: str):
        """The status= query param is ignored for non-recruiter callers; only published returned."""
        resp = client.get("/api/v1/jobs?status=draft")
        assert resp.status_code == 200
        data = resp.json()["data"]
        # Even when requesting draft, public gets only published
        assert all(j["status"] == "published" for j in data)

    def test_recruiter_status_filter(self, client: TestClient, setup: str):
        """Recruiter can filter their own jobs by status."""
        resp = client.get("/api/v1/jobs?status=draft", headers=_auth(setup))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(j["status"] == "draft" for j in data)
        assert len(data) >= 1

    def test_combined_filters(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs?title=python&work_mode=remote")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(
            "python" in j["title"].lower() and j["work_mode"] == "remote"
            for j in data
        )


# ---------------------------------------------------------------------------
# G. Pagination tests
# ---------------------------------------------------------------------------


class TestJobPagination:
    @pytest.fixture(scope="class")
    def setup(self, client: TestClient):
        """Create a recruiter with 15 published jobs."""
        token = _register_and_login(
            client, "page_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Page Corp")
        for i in range(15):
            _create_job(client, token, title=f"Page Job {i:02d}", status="published")
        return token

    def test_default_page_size(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs")
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert body["total"] >= 15

    def test_custom_page_size(self, client: TestClient, setup: str):
        resp = client.get("/api/v1/jobs?page_size=5")
        body = resp.json()
        assert len(body["data"]) <= 5
        assert body["page_size"] == 5
        assert body["total_pages"] >= 3

    def test_second_page(self, client: TestClient, setup: str):
        resp1 = client.get("/api/v1/jobs?page=1&page_size=5")
        resp2 = client.get("/api/v1/jobs?page=2&page_size=5")
        ids1 = {j["id"] for j in resp1.json()["data"]}
        ids2 = {j["id"] for j in resp2.json()["data"]}
        assert ids1.isdisjoint(ids2), "Page 1 and Page 2 must not share job IDs"

    def test_page_beyond_total(self, client: TestClient, setup: str):
        """Requesting a page beyond the total returns empty data, not an error."""
        resp = client.get("/api/v1/jobs?page=9999&page_size=20")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_page_size_limit(self, client: TestClient, setup: str):
        """page_size > 100 should be rejected with 422."""
        resp = client.get("/api/v1/jobs?page_size=101")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# H. Validation tests
# ---------------------------------------------------------------------------


class TestJobValidation:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        token = _register_and_login(
            client, "val_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Val Corp")
        return token

    def test_missing_title_returns_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"description": "No title here"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_empty_title_returns_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": ""},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_inverted_experience_range_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Bad Range", "experience_min": 10, "experience_max": 2},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_inverted_salary_range_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Bad Salary", "salary_min": 100000, "salary_max": 50000},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_negative_salary_min_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Neg Salary", "salary_min": -1},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_invalid_employment_type_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Bad Type", "employment_type": "apprenticeship"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_invalid_work_mode_422(self, client: TestClient, recruiter_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Bad Mode", "work_mode": "moon"},
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 422

    def test_valid_full_job_201(self, client: TestClient, recruiter_token: str):
        """A fully-populated job should create without error."""
        resp = client.post(
            "/api/v1/jobs",
            json={
                "title": "Full Stack Engineer",
                "description": "Work on everything",
                "location": "Remote",
                "employment_type": "full_time",
                "work_mode": "remote",
                "experience_min": 1.0,
                "experience_max": 3.5,
                "education_requirement": "Bachelor's degree",
                "salary_min": 40000,
                "salary_max": 70000,
                "status": "draft",
            },
            headers=_auth(recruiter_token),
        )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# I. Regression — existing endpoints must continue to work
# ---------------------------------------------------------------------------


class TestJobsRegression:
    """Verify that all pre-existing API surfaces are unaffected."""

    @pytest.fixture(scope="class")
    def applicant_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "regression_applicant@test.com", "password123", "applicant"
        )

    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        token = _register_and_login(
            client, "regression_recruiter@test.com", "password123", "recruiter"
        )
        _create_company(client, token, "Regression Corp")
        return token

    def test_health_check(self, client: TestClient):
        assert client.get("/health").status_code == 200

    def test_auth_register_login(self, client: TestClient):
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": "reg_test_jobs@test.com", "password": "password123",
                  "full_name": "Reg Test", "role": "applicant"},
        )
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        me = client.get("/api/v1/users/me", headers=_auth(token))
        assert me.status_code == 200

    def test_applicant_profile_crud(self, client: TestClient, applicant_token: str):
        create = client.post(
            "/api/v1/profile",
            json={"bio": "Jobs regression tester"},
            headers=_auth(applicant_token),
        )
        assert create.status_code == 201
        get = client.get("/api/v1/profile", headers=_auth(applicant_token))
        assert get.status_code == 200
        assert get.json()["bio"] == "Jobs regression tester"

    def test_applicant_skills_crud(self, client: TestClient, applicant_token: str):
        create = client.post(
            "/api/v1/skills",
            json={"skill_name": "Rust", "proficiency_level": "intermediate"},
            headers=_auth(applicant_token),
        )
        assert create.status_code == 201
        body = create.json()
        assert "created_at" in body
        assert "updated_at" in body
        lst = client.get("/api/v1/skills", headers=_auth(applicant_token))
        assert lst.status_code == 200
        assert any(s["skill_name"] == "Rust" for s in lst.json())

    def test_recruiter_company_crud(self, client: TestClient, recruiter_token: str):
        resp = client.get("/api/v1/recruiter/company", headers=_auth(recruiter_token))
        assert resp.status_code == 200
        assert "company_name" in resp.json()

    def test_jobs_do_not_appear_in_skills_endpoint(
        self, client: TestClient, applicant_token: str
    ):
        resp = client.get("/api/v1/skills", headers=_auth(applicant_token))
        assert resp.status_code == 200
        # Each item is an ApplicantSkill, never a job
        for item in resp.json():
            assert "title" not in item
            assert "company_id" not in item
