from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.applicant_skill import ApplicantSkill
from app.models.user import User
from app.schemas.skills import (
    ApplicantSkillCreate,
    ApplicantSkillResponse,
    ApplicantSkillUpdate,
)

router = APIRouter(
    prefix="/skills",
    tags=["Applicant Skills"],
)


@router.get(
    "",
    response_model=list[ApplicantSkillResponse],
)
def get_skills(
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    skills = (
        db.query(ApplicantSkill)
        .filter(ApplicantSkill.user_id == current_user.id)
        .order_by(ApplicantSkill.id)
        .all()
    )

    return skills


@router.post(
    "",
    response_model=ApplicantSkillResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_skill(
    skill_data: ApplicantSkillCreate,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    existing_skill = (
        db.query(ApplicantSkill)
        .filter(
            ApplicantSkill.user_id == current_user.id,
            ApplicantSkill.skill_name.ilike(skill_data.skill_name),
        )
        .first()
    )

    if existing_skill is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skill already exists in applicant profile",
        )

    skill = ApplicantSkill(
        user_id=current_user.id,
        **skill_data.model_dump(),
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return skill


@router.put(
    "/{skill_id}",
    response_model=ApplicantSkillResponse,
)
def update_skill(
    skill_id: int,
    skill_data: ApplicantSkillUpdate,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    skill = (
        db.query(ApplicantSkill)
        .filter(
            ApplicantSkill.id == skill_id,
            ApplicantSkill.user_id == current_user.id,
        )
        .first()
    )

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    update_data = skill_data.model_dump(exclude_unset=True)

    if "skill_name" in update_data:
        duplicate_skill = (
            db.query(ApplicantSkill)
            .filter(
                ApplicantSkill.user_id == current_user.id,
                ApplicantSkill.skill_name.ilike(update_data["skill_name"]),
                ApplicantSkill.id != skill_id,
            )
            .first()
        )

        if duplicate_skill is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another skill with this name already exists",
            )

    for field, value in update_data.items():
        setattr(skill, field, value)

    db.commit()
    db.refresh(skill)

    return skill


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_skill(
    skill_id: int,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
):
    skill = (
        db.query(ApplicantSkill)
        .filter(
            ApplicantSkill.id == skill_id,
            ApplicantSkill.user_id == current_user.id,
        )
        .first()
    )

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )

    db.delete(skill)
    db.commit()

    return None