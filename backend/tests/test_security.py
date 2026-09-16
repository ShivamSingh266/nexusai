"""Release-gate tests for authentication and browser-facing API hardening."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import Settings, settings
from app.core.security import ALGORITHM, create_access_token, hash_password
from app.db.base import Base
from app.main import app
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
    db: Session = TestingSessionLocal()
    try:
        db.add_all(
            [Role(name=name, description=name) for name in ("applicant", "recruiter", "government", "admin")]
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


def test_only_applicant_and_recruiter_roles_can_self_register(client: TestClient):
    for role in ("applicant", "recruiter"):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"security-{role}@example.com",
                "password": "password123",
                "full_name": role.title(),
                "role": role,
            },
        )
        assert response.status_code == 201, response.text

    for role in ("government", "admin"):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"security-{role}@example.com",
                "password": "password123",
                "full_name": role.title(),
                "role": role,
            },
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "This role cannot be self-registered."


def test_invalid_expired_and_inactive_access_tokens_are_rejected(client: TestClient):
    db: Session = TestingSessionLocal()
    try:
        applicant_role = db.query(Role).filter(Role.name == "applicant").one()
        inactive = User(
            email="inactive-security@example.com",
            password_hash=hash_password("password123"),
            full_name="Inactive Applicant",
            role_id=applicant_role.id,
            is_active=False,
        )
        db.add(inactive)
        db.commit()
        inactive_token = create_access_token(inactive.id, "applicant")
        expired_token = jwt.encode(
            {
                "sub": str(inactive.id),
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            settings.JWT_SECRET_KEY,
            algorithm=ALGORITHM,
        )
    finally:
        db.close()

    for token in ("not-a-token", expired_token, inactive_token):
        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert "password" not in response.text.casefold()
        assert "token" not in response.text.casefold() or "access token" in response.text.casefold()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive-security@example.com", "password": "password123"},
    )
    assert login.status_code == 403


def test_cors_allows_only_configured_origin_and_declared_headers(client: TestClient):
    allowed = client.options(
        "/api/v1/meta/versions",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "authorization" in allowed.headers["access-control-allow-headers"].casefold()
    assert "*" not in allowed.headers["access-control-allow-methods"]

    denied = client.options(
        "/api/v1/meta/versions",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert denied.status_code == 400


@pytest.mark.parametrize(
    "secret",
    ("your-secret-key-here", "replace-with-a-long-random-jwt-signing-secret"),
)
def test_production_configuration_rejects_placeholder_jwt_secret(secret: str):
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY must not use a placeholder"):
        Settings(
            DATABASE_URL="postgresql://example.invalid/nexusai",
            JWT_SECRET_KEY=secret,
            ENVIRONMENT="production",
        )


def test_cors_configuration_rejects_wildcard_with_credentials():
    with pytest.raises(ValidationError, match="BACKEND_CORS_ORIGINS must not include"):
        Settings(
            DATABASE_URL="postgresql://example.invalid/nexusai",
            JWT_SECRET_KEY="a-real-test-secret",
            BACKEND_CORS_ORIGINS=["*"],
        )
