"""
Tests for the Recruiter Company endpoints.

Strategy:
- Use an in-memory SQLite database per test module (shared session-scoped fixture).
- Override FastAPI's get_db dependency to use the test DB.
- Create users via the /auth/register endpoint to exercise real auth flow.
- Authenticate via /auth/login to obtain JWTs.
- All company operations go through the API (no direct DB manipulation except teardown).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import SessionLocal
from app.main import app
from app.api.deps import get_db
from app.models.user import Role, User
from app.core.security import create_access_token, hash_password

# ---------------------------------------------------------------------------
# Test database setup (in-memory SQLite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite://"  # in-memory

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()



# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create all tables and seed roles once for the whole module."""
    Base.metadata.create_all(bind=engine)

    # Seed roles so /auth/register can resolve them
    db: Session = TestingSessionLocal()
    try:
        roles = ["applicant", "recruiter", "government", "admin"]
        for role_name in roles:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name, description=role_name))
        db.commit()
    finally:
        db.close()

    # Apply override, preserving any previously set override
    _previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    yield

    # Restore previous state
    if _previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper: register + login, return bearer token
# ---------------------------------------------------------------------------


def _register_and_login(client: TestClient, email: str, password: str, role: str) -> str:
    if role in {"government", "admin"}:
        db: Session = TestingSessionLocal()
        try:
            role_record = db.query(Role).filter(Role.name == role).one()
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name="Test User",
                role_id=role_record.id,
            )
            db.add(user)
            db.commit()
            return create_access_token(user.id, role)
        finally:
            db.close()
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role": role,
        },
    )
    assert reg.status_code == 201, reg.text
    return reg.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests: unauthenticated access
# ---------------------------------------------------------------------------


class TestUnauthenticated:
    def test_get_company_no_token_returns_403(self, client: TestClient):
        """HTTPBearer with auto_error=True returns 403 when no header is present."""
        resp = client.get("/api/v1/recruiter/company")
        assert resp.status_code in (401, 403), resp.text

    def test_create_company_no_token_returns_403(self, client: TestClient):
        resp = client.post("/api/v1/recruiter/company", json={"company_name": "Acme"})
        assert resp.status_code in (401, 403), resp.text

    def test_patch_company_no_token_returns_403(self, client: TestClient):
        resp = client.patch("/api/v1/recruiter/company", json={"company_name": "Acme"})
        assert resp.status_code in (401, 403), resp.text

    def test_get_company_invalid_token_returns_401(self, client: TestClient):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# Tests: wrong-role access (applicant and government)
# ---------------------------------------------------------------------------


class TestForbiddenRoles:
    @pytest.fixture(scope="class")
    def applicant_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "applicant_role@test.com", "password123", "applicant"
        )

    @pytest.fixture(scope="class")
    def government_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "government_role@test.com", "password123", "government"
        )

    def test_applicant_get_company_returns_403(
        self, client: TestClient, applicant_token: str
    ):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(applicant_token),
        )
        assert resp.status_code == 403, resp.text

    def test_applicant_create_company_returns_403(
        self, client: TestClient, applicant_token: str
    ):
        resp = client.post(
            "/api/v1/recruiter/company",
            json={"company_name": "Illegal Co"},
            headers=_auth_headers(applicant_token),
        )
        assert resp.status_code == 403, resp.text

    def test_applicant_patch_company_returns_403(
        self, client: TestClient, applicant_token: str
    ):
        resp = client.patch(
            "/api/v1/recruiter/company",
            json={"company_name": "Illegal Co"},
            headers=_auth_headers(applicant_token),
        )
        assert resp.status_code == 403, resp.text

    def test_government_get_company_returns_403(
        self, client: TestClient, government_token: str
    ):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(government_token),
        )
        assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Tests: recruiter happy-path
# ---------------------------------------------------------------------------


class TestRecruiterCompanyCRUD:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "recruiter_crud@test.com", "password123", "recruiter"
        )

    def test_get_company_before_creation_returns_404(
        self, client: TestClient, recruiter_token: str
    ):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 404, resp.text

    def test_create_company_returns_201(
        self, client: TestClient, recruiter_token: str
    ):
        payload = {
            "company_name": "Acme Corp",
            "description": "A great company",
            "industry": "Technology",
            "website": "https://acme.example.com",
            "location": "Nairobi, Kenya",
            "company_size": "51-200",
        }
        resp = client.post(
            "/api/v1/recruiter/company",
            json=payload,
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["company_name"] == "Acme Corp"
        assert body["industry"] == "Technology"
        assert body["id"] is not None
        assert "created_at" in body
        assert "updated_at" in body

    def test_get_company_after_creation_returns_200(
        self, client: TestClient, recruiter_token: str
    ):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["company_name"] == "Acme Corp"

    def test_create_company_again_returns_409(
        self, client: TestClient, recruiter_token: str
    ):
        """A recruiter cannot create a second company."""
        resp = client.post(
            "/api/v1/recruiter/company",
            json={"company_name": "Duplicate Corp"},
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 409, resp.text

    def test_patch_company_updates_fields(
        self, client: TestClient, recruiter_token: str
    ):
        resp = client.patch(
            "/api/v1/recruiter/company",
            json={"company_name": "Acme Corp Updated", "company_size": "201-500"},
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["company_name"] == "Acme Corp Updated"
        assert body["company_size"] == "201-500"
        # Untouched fields should remain
        assert body["industry"] == "Technology"

    def test_patch_company_unset_fields_not_nullified(
        self, client: TestClient, recruiter_token: str
    ):
        """PATCH semantics: fields not sent should not be cleared."""
        resp = client.patch(
            "/api/v1/recruiter/company",
            json={"location": "Lagos, Nigeria"},
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["location"] == "Lagos, Nigeria"
        # Other fields still intact
        assert body["company_name"] == "Acme Corp Updated"
        assert body["industry"] == "Technology"


# ---------------------------------------------------------------------------
# Tests: validation errors
# ---------------------------------------------------------------------------


class TestValidation:
    @pytest.fixture(scope="class")
    def recruiter_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "recruiter_validation@test.com", "password123", "recruiter"
        )

    def test_create_company_missing_name_returns_422(
        self, client: TestClient, recruiter_token: str
    ):
        """company_name is required on create."""
        resp = client.post(
            "/api/v1/recruiter/company",
            json={"industry": "Finance"},
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 422, resp.text

    def test_create_company_empty_name_returns_422(
        self, client: TestClient, recruiter_token: str
    ):
        """company_name min_length=1."""
        resp = client.post(
            "/api/v1/recruiter/company",
            json={"company_name": ""},
            headers=_auth_headers(recruiter_token),
        )
        assert resp.status_code == 422, resp.text


# ---------------------------------------------------------------------------
# Tests: isolation between recruiters
# ---------------------------------------------------------------------------


class TestIsolationBetweenRecruiters:
    """
    Recruiter A creates a company. Recruiter B should not be able to see or
    accidentally access Recruiter A's company; they get their own 404.
    """

    @pytest.fixture(scope="class")
    def recruiter_a_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "recruiter_a_isolation@test.com", "password123", "recruiter"
        )

    @pytest.fixture(scope="class")
    def recruiter_b_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "recruiter_b_isolation@test.com", "password123", "recruiter"
        )

    def test_recruiter_a_creates_company(
        self, client: TestClient, recruiter_a_token: str
    ):
        resp = client.post(
            "/api/v1/recruiter/company",
            json={"company_name": "Company A"},
            headers=_auth_headers(recruiter_a_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["company_name"] == "Company A"

    def test_recruiter_b_gets_404_not_recruiter_a_company(
        self, client: TestClient, recruiter_b_token: str
    ):
        """Recruiter B has no company → 404, does NOT see Recruiter A's company."""
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(recruiter_b_token),
        )
        assert resp.status_code == 404, resp.text

    def test_recruiter_b_creates_own_company(
        self, client: TestClient, recruiter_b_token: str
    ):
        resp = client.post(
            "/api/v1/recruiter/company",
            json={"company_name": "Company B"},
            headers=_auth_headers(recruiter_b_token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["company_name"] == "Company B"

    def test_recruiter_a_still_sees_own_company(
        self, client: TestClient, recruiter_a_token: str
    ):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(recruiter_a_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["company_name"] == "Company A"

    def test_recruiter_b_still_sees_own_company(
        self, client: TestClient, recruiter_b_token: str
    ):
        resp = client.get(
            "/api/v1/recruiter/company",
            headers=_auth_headers(recruiter_b_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["company_name"] == "Company B"


# ---------------------------------------------------------------------------
# Tests: existing applicant/auth endpoints still work (regression)
# ---------------------------------------------------------------------------


class TestExistingEndpointsRegression:
    @pytest.fixture(scope="class")
    def applicant_token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "applicant_regression@test.com", "password123", "applicant"
        )

    def test_health_check(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_get_me(self, client: TestClient, applicant_token: str):
        resp = client.get(
            "/api/v1/users/me",
            headers=_auth_headers(applicant_token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "applicant"

    def test_create_and_get_applicant_profile(
        self, client: TestClient, applicant_token: str
    ):
        create_resp = client.post(
            "/api/v1/profile",
            json={"bio": "Test applicant"},
            headers=_auth_headers(applicant_token),
        )
        assert create_resp.status_code == 201, create_resp.text

        get_resp = client.get(
            "/api/v1/profile",
            headers=_auth_headers(applicant_token),
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["bio"] == "Test applicant"

    def test_create_and_list_skills(
        self, client: TestClient, applicant_token: str
    ):
        create_resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Python", "proficiency_level": "expert"},
            headers=_auth_headers(applicant_token),
        )
        assert create_resp.status_code == 201, create_resp.text

        list_resp = client.get(
            "/api/v1/skills",
            headers=_auth_headers(applicant_token),
        )
        assert list_resp.status_code == 200
        skills = list_resp.json()
        assert any(s["skill_name"] == "Python" for s in skills)
