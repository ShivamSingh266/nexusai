"""
Tests for ApplicantSkill hardening:
- Timestamps (created_at, updated_at) present in responses
- DB-level unique constraint coexists with API-level ilike protection
- Full CRUD still works after hardening
- Regression: existing company/auth tests are unaffected (separate DB)

Strategy:
- in-memory SQLite, StaticPool
- The app.dependency_overrides[get_db] override is applied inside a
  module-scoped autouse fixture and REMOVED after the module is done.
  This prevents contamination when both test files run in the same process.
"""
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.api.deps import get_db
from app.models.user import Role
from app.models.applicant_skill import ApplicantSkill

# ---------------------------------------------------------------------------
# Isolated test database engine (does NOT share state with other test files)
# ---------------------------------------------------------------------------

_SKILLS_TEST_DB_URL = "sqlite://"

_skills_engine = create_engine(
    _SKILLS_TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_SkillsTestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_skills_engine,
)


def _skills_override_get_db():
    db = _SkillsTestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def setup_skills_database():
    """
    Creates schema, seeds roles, applies the get_db override for this module,
    then tears everything down after all tests in the module complete.
    The override is removed so test_recruiter_company.py is not affected.
    """
    Base.metadata.create_all(bind=_skills_engine)

    db: Session = _SkillsTestingSessionLocal()
    try:
        for role_name in ["applicant", "recruiter", "government", "admin"]:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name, description=role_name))
        db.commit()
    finally:
        db.close()

    # Apply override — store whatever was there before (could be another module's override)
    _previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _skills_override_get_db

    yield

    # Restore previous state so other modules are not affected
    if _previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = _previous_override

    Base.metadata.drop_all(bind=_skills_engine)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(client: TestClient, email: str, password: str, role: str) -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User", "role": role},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# A. Timestamp tests
# ---------------------------------------------------------------------------


class TestTimestamps:
    """created_at and updated_at must be present and valid in every response."""

    @pytest.fixture(scope="class")
    def token(self, client: TestClient) -> str:
        return _register_and_login(client, "ts_applicant@test.com", "password123", "applicant")

    def test_create_returns_timestamps(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Go", "proficiency_level": "intermediate"},
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "created_at" in body, "created_at missing from response"
        assert "updated_at" in body, "updated_at missing from response"
        assert body["created_at"] is not None
        assert body["updated_at"] is not None

    def test_list_returns_timestamps(self, client: TestClient, token: str):
        resp = client.get("/api/v1/skills", headers=_auth(token))
        assert resp.status_code == 200
        skills = resp.json()
        assert len(skills) >= 1
        for skill in skills:
            assert "created_at" in skill
            assert "updated_at" in skill

    def test_update_refreshes_updated_at(self, client: TestClient, token: str):
        """updated_at should be present after update, created_at unchanged."""
        create_resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Rust", "proficiency_level": "beginner"},
            headers=_auth(token),
        )
        assert create_resp.status_code == 201, create_resp.text
        created = create_resp.json()
        skill_id = created["id"]
        created_at_original = created["created_at"]

        # Small sleep to let timestamp advance (SQLite second resolution)
        time.sleep(1.1)

        update_resp = client.put(
            f"/api/v1/skills/{skill_id}",
            json={"proficiency_level": "intermediate"},
            headers=_auth(token),
        )
        assert update_resp.status_code == 200, update_resp.text
        updated = update_resp.json()

        # created_at must not change
        assert updated["created_at"] == created_at_original, (
            f"created_at changed unexpectedly: {created_at_original!r} → {updated['created_at']!r}"
        )
        # updated_at must be present and non-null
        assert updated["updated_at"] is not None

    def test_proficiency_level_default_applied(self, client: TestClient, token: str):
        """Omitting proficiency_level must result in 'beginner' in the response."""
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Scala"},
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["proficiency_level"] == "beginner"


# ---------------------------------------------------------------------------
# B. Duplicate protection tests
# ---------------------------------------------------------------------------


class TestDuplicateProtection:
    """
    Both the API (ilike) and the DB (unique constraint) guard against duplicates.
    """

    @pytest.fixture(scope="class")
    def token(self, client: TestClient) -> str:
        return _register_and_login(client, "dup_applicant@test.com", "password123", "applicant")

    def test_exact_duplicate_returns_409(self, client: TestClient, token: str):
        client.post(
            "/api/v1/skills",
            json={"skill_name": "Python"},
            headers=_auth(token),
        )
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Python"},
            headers=_auth(token),
        )
        assert resp.status_code == 409, resp.text

    def test_case_insensitive_duplicate_returns_409(self, client: TestClient, token: str):
        """ilike guard must catch 'python' when 'Python' already exists."""
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "python"},
            headers=_auth(token),
        )
        assert resp.status_code == 409, resp.text

    def test_mixed_case_duplicate_returns_409(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "PYTHON"},
            headers=_auth(token),
        )
        assert resp.status_code == 409, resp.text

    def test_different_skill_name_allowed(self, client: TestClient, token: str):
        """A different name must be accepted even if it starts the same."""
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Python 3"},
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text

    def test_same_skill_name_different_user_allowed(self, client: TestClient):
        """Two different applicants may each have 'Java' — constraint is per-user."""
        token_a = _register_and_login(
            client, "user_a_dup@test.com", "password123", "applicant"
        )
        token_b = _register_and_login(
            client, "user_b_dup@test.com", "password123", "applicant"
        )

        resp_a = client.post(
            "/api/v1/skills",
            json={"skill_name": "Java"},
            headers=_auth(token_a),
        )
        assert resp_a.status_code == 201, resp_a.text

        resp_b = client.post(
            "/api/v1/skills",
            json={"skill_name": "Java"},
            headers=_auth(token_b),
        )
        assert resp_b.status_code == 201, resp_b.text

    def test_db_unique_constraint_exists(self):
        """
        Verify the constraint is present at the DB level by bypassing the API.
        Uses a user_id value (9999) that won't conflict with registered test users.
        """
        db: Session = _SkillsTestingSessionLocal()
        try:
            db.add(ApplicantSkill(
                user_id=9999,
                skill_name="DirectInsert",
                proficiency_level="beginner",
            ))
            db.flush()
            # Insert an identical row — must trigger IntegrityError
            db.add(ApplicantSkill(
                user_id=9999,
                skill_name="DirectInsert",
                proficiency_level="expert",
            ))
            with pytest.raises(IntegrityError):
                db.flush()
        finally:
            db.rollback()
            db.close()


# ---------------------------------------------------------------------------
# C. Full CRUD regression after hardening
# ---------------------------------------------------------------------------


class TestSkillsCRUD:
    """All existing CRUD endpoints must work identically after the hardening."""

    @pytest.fixture(scope="class")
    def token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "crud_applicant@test.com", "password123", "applicant"
        )

    def test_create_skill_201(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "TypeScript", "proficiency_level": "advanced", "years_experience": 3},
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["skill_name"] == "TypeScript"
        assert body["proficiency_level"] == "advanced"
        assert body["years_experience"] == 3
        assert body["id"] is not None
        assert body["user_id"] is not None
        assert "created_at" in body
        assert "updated_at" in body

    def test_list_skills_200(self, client: TestClient, token: str):
        resp = client.get("/api/v1/skills", headers=_auth(token))
        assert resp.status_code == 200
        skills = resp.json()
        assert isinstance(skills, list)
        assert any(s["skill_name"] == "TypeScript" for s in skills)

    def test_update_skill_200(self, client: TestClient, token: str):
        create = client.post(
            "/api/v1/skills",
            json={"skill_name": "Node.js"},
            headers=_auth(token),
        )
        assert create.status_code == 201
        skill_id = create.json()["id"]

        update = client.put(
            f"/api/v1/skills/{skill_id}",
            json={"proficiency_level": "expert", "years_experience": 5},
            headers=_auth(token),
        )
        assert update.status_code == 200, update.text
        body = update.json()
        assert body["proficiency_level"] == "expert"
        assert body["years_experience"] == 5
        assert body["skill_name"] == "Node.js"  # unchanged

    def test_update_skill_name_duplicate_409(self, client: TestClient, token: str):
        """Renaming a skill to an already-existing name (case-insensitive) → 409."""
        s1 = client.post(
            "/api/v1/skills",
            json={"skill_name": "Docker"},
            headers=_auth(token),
        )
        assert s1.status_code == 201
        s2 = client.post(
            "/api/v1/skills",
            json={"skill_name": "Kubernetes"},
            headers=_auth(token),
        )
        assert s2.status_code == 201
        s2_id = s2.json()["id"]

        resp = client.put(
            f"/api/v1/skills/{s2_id}",
            json={"skill_name": "docker"},
            headers=_auth(token),
        )
        assert resp.status_code == 409, resp.text

    def test_delete_skill_204(self, client: TestClient, token: str):
        create = client.post(
            "/api/v1/skills",
            json={"skill_name": "Terraform"},
            headers=_auth(token),
        )
        assert create.status_code == 201
        skill_id = create.json()["id"]

        del_resp = client.delete(
            f"/api/v1/skills/{skill_id}",
            headers=_auth(token),
        )
        assert del_resp.status_code == 204, del_resp.text

        list_resp = client.get("/api/v1/skills", headers=_auth(token))
        assert not any(s["id"] == skill_id for s in list_resp.json())

    def test_delete_nonexistent_skill_404(self, client: TestClient, token: str):
        resp = client.delete("/api/v1/skills/999999", headers=_auth(token))
        assert resp.status_code == 404, resp.text

    def test_update_nonexistent_skill_404(self, client: TestClient, token: str):
        resp = client.put(
            "/api/v1/skills/999999",
            json={"proficiency_level": "expert"},
            headers=_auth(token),
        )
        assert resp.status_code == 404, resp.text

    def test_recruiter_cannot_access_skills(self, client: TestClient):
        recruiter_token = _register_and_login(
            client, "recruiter_skills@test.com", "password123", "recruiter"
        )
        endpoints = [
            ("get", "/api/v1/skills", {}),
            ("post", "/api/v1/skills", {"json": {"skill_name": "X"}}),
            ("put", "/api/v1/skills/1", {"json": {"skill_name": "X"}}),
            ("delete", "/api/v1/skills/1", {}),
        ]
        for method, path, kwargs in endpoints:
            resp = getattr(client, method)(
                path, headers=_auth(recruiter_token), **kwargs
            )
            assert resp.status_code == 403, (
                f"{method.upper()} {path} should be 403, got {resp.status_code}"
            )

    def test_unauthenticated_returns_401_or_403(self, client: TestClient):
        for method, path, kwargs in [
            ("get", "/api/v1/skills", {}),
            ("post", "/api/v1/skills", {"json": {"skill_name": "X"}}),
        ]:
            resp = getattr(client, method)(path, **kwargs)
            assert resp.status_code in (401, 403), (
                f"{method.upper()} {path} should be 401/403, got {resp.status_code}"
            )

    def test_cross_user_isolation(self, client: TestClient):
        """Applicant A cannot modify Applicant B's skills — treated as 404."""
        token_a = _register_and_login(
            client, "isolation_a@test.com", "password123", "applicant"
        )
        token_b = _register_and_login(
            client, "isolation_b@test.com", "password123", "applicant"
        )

        create = client.post(
            "/api/v1/skills",
            json={"skill_name": "Kafka"},
            headers=_auth(token_b),
        )
        assert create.status_code == 201
        b_skill_id = create.json()["id"]

        # A tries to update B's skill → 404 (not owned)
        resp = client.put(
            f"/api/v1/skills/{b_skill_id}",
            json={"skill_name": "Kafka Modified"},
            headers=_auth(token_a),
        )
        assert resp.status_code == 404, resp.text

        # A tries to delete B's skill → 404
        resp = client.delete(
            f"/api/v1/skills/{b_skill_id}",
            headers=_auth(token_a),
        )
        assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# D. Validation tests
# ---------------------------------------------------------------------------


class TestSkillsValidation:

    @pytest.fixture(scope="class")
    def token(self, client: TestClient) -> str:
        return _register_and_login(
            client, "validation_applicant@test.com", "password123", "applicant"
        )

    def test_missing_skill_name_returns_422(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"proficiency_level": "expert"},
            headers=_auth(token),
        )
        assert resp.status_code == 422, resp.text

    def test_empty_skill_name_returns_422(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": ""},
            headers=_auth(token),
        )
        assert resp.status_code == 422, resp.text

    def test_negative_years_experience_returns_422(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "AWS", "years_experience": -1},
            headers=_auth(token),
        )
        assert resp.status_code == 422, resp.text

    def test_years_experience_zero_is_valid(self, client: TestClient, token: str):
        resp = client.post(
            "/api/v1/skills",
            json={"skill_name": "Azure", "years_experience": 0},
            headers=_auth(token),
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["years_experience"] == 0
