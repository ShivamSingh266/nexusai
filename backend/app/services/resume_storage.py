"""Safe local storage for applicant resume uploads."""

from __future__ import annotations

import ntpath
import os
import uuid
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile


MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
}


class ResumeUploadError(ValueError):
    """Base error for invalid resume uploads."""


class ResumeTypeError(ResumeUploadError):
    """The extension, content type, or file signature is unsupported."""


class ResumeSizeError(ResumeUploadError):
    """The upload exceeds the configured maximum size."""


@dataclass(frozen=True)
class StoredResume:
    storage_key: str
    original_filename: str
    content_type: str
    file_size: int


def _safe_original_filename(filename: str | None) -> tuple[str, str]:
    raw_filename = (filename or "").strip()
    basename = ntpath.basename(raw_filename)
    if not basename or basename in {".", ".."}:
        raise ResumeTypeError("A valid PDF or DOCX filename is required")

    suffix = Path(basename).suffix.lower()
    expected_content_type = ALLOWED_CONTENT_TYPES.get(suffix)
    if expected_content_type is None:
        raise ResumeTypeError("Only PDF and DOCX resumes are supported")

    return basename, expected_content_type


def _validate_content(content: bytes, suffix: str, content_type: str) -> None:
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise ResumeTypeError("The uploaded file is not a valid PDF")

    if suffix == ".docx":
        if not zipfile.is_zipfile(BytesIO(content)):
            raise ResumeTypeError("The uploaded file is not a valid DOCX")
        with zipfile.ZipFile(BytesIO(content)) as archive:
            if "[Content_Types].xml" not in archive.namelist():
                raise ResumeTypeError("The uploaded file is not a valid DOCX")

    if not content_type:
        raise ResumeTypeError("A content type is required")


def store_resume_upload(
    upload: UploadFile,
    *,
    applicant_id: int,
    storage_root: str | Path,
) -> StoredResume:
    """Validate and atomically store an upload under a generated key."""

    original_filename, expected_content_type = _safe_original_filename(
        upload.filename
    )
    content_type = (upload.content_type or "").lower()
    if content_type != expected_content_type:
        raise ResumeTypeError("Filename extension and content type do not match")

    content = upload.file.read(MAX_RESUME_SIZE_BYTES + 1)
    if len(content) > MAX_RESUME_SIZE_BYTES:
        raise ResumeSizeError("Resume file exceeds the 5 MB limit")
    _validate_content(content, Path(original_filename).suffix.lower(), content_type)

    root = Path(storage_root).expanduser().resolve()
    storage_key = f"{applicant_id}/{uuid.uuid4().hex}{Path(original_filename).suffix.lower()}"
    destination = (root / storage_key).resolve()
    if root not in destination.parents:
        raise ResumeUploadError("Invalid storage location")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary_path.write_bytes(content)
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return StoredResume(
        storage_key=storage_key,
        original_filename=original_filename,
        content_type=content_type,
        file_size=len(content),
    )


def delete_stored_resume(storage_root: str | Path, storage_key: str) -> None:
    """Delete one generated storage key without accepting filesystem paths."""

    root = Path(storage_root).expanduser().resolve()
    target = (root / storage_key).resolve()
    if root not in target.parents:
        raise ValueError("Invalid storage key")
    target.unlink(missing_ok=True)
