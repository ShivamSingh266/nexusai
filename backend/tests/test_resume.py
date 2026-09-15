from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app
from app.models.applicant_skill import ApplicantSkill
from app.models.resume import Resume
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
def setup_database(tmp_path_factory):
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    for role_name in ("applicant", "recruiter", "government", "admin"):
        db.add(Role(name=role_name, description=role_name))
    db.commit()
    db.close()

    previous_storage_dir = settings.RESUME_STORAGE_DIR
    settings.RESUME_STORAGE_DIR = str(tmp_path_factory.mktemp("resumes"))
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    settings.RESUME_STORAGE_DIR = previous_storage_dir
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
            "full_name": "Resume User",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def pdf_bytes(size: int = 13) -> bytes:
    return b"%PDF-1.7\n" + b"x" * max(0, size - 9)


def docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
    return buffer.getvalue()


def test_pdf_upload_persists_metadata_and_does_not_mutate_skills(client: TestClient):
    token = register(client, "resume-pdf@example.com", "applicant")

    before = TestingSessionLocal()
    try:
        assert before.scalars(select(ApplicantSkill)).all() == []
    finally:
        before.close()

    response = client.post(
        "/api/v1/profile/resume",
        headers=auth(token),
        files={"file": ("../../unsafe.pdf", pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["original_filename"] == "unsafe.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["file_size"] == len(pdf_bytes())
    assert ".." not in body["storage_reference"]
    assert "/" in body["storage_reference"]

    metadata = client.get("/api/v1/profile/resume", headers=auth(token))
    assert metadata.status_code == 200
    assert metadata.json()["id"] == body["id"]

    after = TestingSessionLocal()
    try:
        assert after.scalars(select(ApplicantSkill)).all() == []
        assert after.scalar(select(Resume)) is not None
    finally:
        after.close()


def test_docx_upload_is_supported(client: TestClient):
    token = register(client, "resume-docx@example.com", "applicant")

    response = client.post(
        "/api/v1/profile/resume",
        headers=auth(token),
        files={
            "file": (
                "resume.docx",
                docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["content_type"].endswith("wordprocessingml.document")


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("resume.txt", b"plain text", "text/plain"),
        ("resume.pdf", b"not a pdf", "application/pdf"),
        ("resume.docx", b"not a docx", "application/pdf"),
    ],
)
def test_unsupported_type_is_rejected(
    client: TestClient,
    filename: str,
    content: bytes,
    content_type: str,
):
    token = register(client, f"reject-{filename.replace('.', '')}@example.com", "applicant")
    response = client.post(
        "/api/v1/profile/resume",
        headers=auth(token),
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == 415


def test_file_larger_than_five_mb_is_rejected(client: TestClient):
    token = register(client, "resume-large@example.com", "applicant")
    response = client.post(
        "/api/v1/profile/resume",
        headers=auth(token),
        files={"file": ("large.pdf", pdf_bytes(5 * 1024 * 1024 + 1), "application/pdf")},
    )
    assert response.status_code == 413


def test_unauthenticated_and_non_applicant_uploads_are_rejected(client: TestClient):
    unauthenticated = client.post(
        "/api/v1/profile/resume",
        files={"file": ("resume.pdf", pdf_bytes(), "application/pdf")},
    )
    assert unauthenticated.status_code == 403

    recruiter_token = register(client, "resume-recruiter@example.com", "recruiter")
    forbidden = client.post(
        "/api/v1/profile/resume",
        headers=auth(recruiter_token),
        files={"file": ("resume.pdf", pdf_bytes(), "application/pdf")},
    )
    assert forbidden.status_code == 403


def test_replacement_is_deterministic_and_cleans_old_object(client: TestClient):
    token = register(client, "resume-replace@example.com", "applicant")
    first = client.post(
        "/api/v1/profile/resume",
        headers=auth(token),
        files={"file": ("first.pdf", pdf_bytes(), "application/pdf")},
    )
    first_reference = first.json()["storage_reference"]
    first_path = Path(settings.RESUME_STORAGE_DIR) / first_reference
    assert first_path.exists()

    second = client.post(
        "/api/v1/profile/resume",
        headers=auth(token),
        files={"file": ("second.pdf", pdf_bytes(), "application/pdf")},
    )
    second_body = second.json()
    assert second_body["id"] == first.json()["id"]
    assert second_body["original_filename"] == "second.pdf"
    assert second_body["storage_reference"] != first_reference
    assert not first_path.exists()


def test_cross_user_metadata_access_is_protected(client: TestClient):
    owner_token = register(client, "resume-owner@example.com", "applicant")
    other_token = register(client, "resume-other@example.com", "applicant")
    upload = client.post(
        "/api/v1/profile/resume",
        headers=auth(owner_token),
        files={"file": ("owner.pdf", pdf_bytes(), "application/pdf")},
    )
    assert upload.status_code == 201

    assert client.get(
        "/api/v1/profile/resume",
        headers=auth(other_token),
    ).status_code == 404


def test_resume_without_existing_metadata_returns_not_found(client: TestClient):
    token = register(client, "resume-missing@example.com", "applicant")
    assert client.get(
        "/api/v1/profile/resume",
        headers=auth(token),
    ).status_code == 404
