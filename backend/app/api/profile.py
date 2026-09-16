from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.applicant_profile import ApplicantProfile
from app.models.resume import Resume
from app.models.user import User
from app.schemas.profile import (
    ApplicantProfileCreate,
    ApplicantProfileResponse,
    ApplicantProfileUpdate,
)
from app.core.config import settings
from app.schemas.resume import ResumeResponse
from app.services.resume_storage import (
    ResumeSizeError,
    ResumeTypeError,
    delete_stored_resume,
    store_resume_upload,
)


router = APIRouter(
    prefix="/profile",
    tags=["Applicant Profile"],
)


@router.get(
    "",
    response_model=ApplicantProfileResponse,
)
def get_profile(
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(ApplicantProfile)
        .filter(ApplicantProfile.user_id == current_user.id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant profile not found",
        )

    return profile


@router.post(
    "",
    response_model=ApplicantProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    profile_data: ApplicantProfileCreate,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    existing_profile = (
        db.query(ApplicantProfile)
        .filter(ApplicantProfile.user_id == current_user.id)
        .first()
    )

    if existing_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Applicant profile already exists",
        )

    profile = ApplicantProfile(
        user_id=current_user.id,
        **profile_data.model_dump(),
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.put(
    "",
    response_model=ApplicantProfileResponse,
)
def update_profile(
    profile_data: ApplicantProfileUpdate,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(ApplicantProfile)
        .filter(ApplicantProfile.user_id == current_user.id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Applicant profile not found",
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


def _resume_response(resume: Resume) -> ResumeResponse:
    return ResumeResponse(
        id=resume.id,
        storage_reference=resume.storage_key,
        original_filename=resume.original_filename,
        content_type=resume.content_type,
        file_size=resume.file_size,
        uploaded_at=resume.uploaded_at,
    )


@router.post(
    "/resume",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    try:
        stored = store_resume_upload(
            file,
            applicant_id=current_user.id,
            storage_root=settings.RESUME_STORAGE_DIR,
        )
    except ResumeSizeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except ResumeTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    existing_resume = db.scalar(
        select(Resume).where(Resume.applicant_id == current_user.id)
    )
    old_storage_key = existing_resume.storage_key if existing_resume else None

    try:
        if existing_resume is None:
            resume = Resume(
                applicant_id=current_user.id,
                storage_key=stored.storage_key,
                original_filename=stored.original_filename,
                content_type=stored.content_type,
                file_size=stored.file_size,
            )
            db.add(resume)
        else:
            resume = existing_resume
            resume.storage_key = stored.storage_key
            resume.original_filename = stored.original_filename
            resume.content_type = stored.content_type
            resume.file_size = stored.file_size

        db.commit()
        db.refresh(resume)
    except Exception:
        db.rollback()
        delete_stored_resume(settings.RESUME_STORAGE_DIR, stored.storage_key)
        raise

    if old_storage_key:
        delete_stored_resume(settings.RESUME_STORAGE_DIR, old_storage_key)

    return _resume_response(resume)


@router.get(
    "/resume",
    response_model=ResumeResponse,
)
def get_resume(
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    resume = db.scalar(
        select(Resume).where(Resume.applicant_id == current_user.id)
    )
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return _resume_response(resume)