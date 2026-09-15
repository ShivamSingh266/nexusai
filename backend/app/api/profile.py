from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.applicant_profile import ApplicantProfile
from app.models.user import User
from app.schemas.profile import (
    ApplicantProfileCreate,
    ApplicantProfileResponse,
    ApplicantProfileUpdate,
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