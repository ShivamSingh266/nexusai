"""Job-to-canonical-skill management API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db, require_roles
from app.models.canonical_skill import CanonicalSkill
from app.models.job import Job, JobStatus
from app.models.job_skill import JobSkill
from app.models.user import User
from app.schemas.job_skill import (
    JobSkillBulkCreate,
    JobSkillCreate,
    JobSkillResponse,
    JobSkillUpdate,
)

router = APIRouter(
    prefix="/jobs/{job_id}/skills",
    tags=["Job Skills"],
)


def _get_job_for_read(job_id: int, current_user: User | None, db: Session) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    is_recruiter = (
        current_user is not None
        and current_user.role.name in ("recruiter", "admin")
    )
    if is_recruiter:
        if current_user.company_id != job.company_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    elif job.status != JobStatus.published.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


def _get_owned_job(job_id: int, current_user: User, db: Session) -> Job:
    if current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must create a company profile before managing job skills.",
        )
    job = db.get(Job, job_id)
    if job is None or job.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


def _validate_skill(skill_data: JobSkillCreate, db: Session) -> CanonicalSkill:
    canonical_skill = db.get(CanonicalSkill, skill_data.skill_id)
    if canonical_skill is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Canonical skill not found: {skill_data.skill_id}",
        )
    if canonical_skill.taxonomy_version != skill_data.taxonomy_version:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Taxonomy version mismatch for {skill_data.skill_id}",
        )
    return canonical_skill


def _duplicate_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This canonical skill is already attached to the job.",
    )


@router.get("", response_model=list[JobSkillResponse])
def list_job_skills(
    job_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[JobSkill]:
    job = _get_job_for_read(job_id, current_user, db)
    return db.query(JobSkill).filter(JobSkill.job_id == job.id).order_by(JobSkill.id).all()


@router.post("", response_model=JobSkillResponse, status_code=status.HTTP_201_CREATED)
def create_job_skill(
    job_id: int,
    skill_data: JobSkillCreate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> JobSkill:
    job = _get_owned_job(job_id, current_user, db)
    _validate_skill(skill_data, db)
    if db.query(JobSkill).filter_by(job_id=job.id, skill_id=skill_data.skill_id).first():
        raise _duplicate_error()
    job_skill = JobSkill(job_id=job.id, **skill_data.model_dump())
    db.add(job_skill)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _duplicate_error()
    db.refresh(job_skill)
    return job_skill


@router.post("/bulk", response_model=list[JobSkillResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_job_skills(
    job_id: int,
    skill_data: JobSkillBulkCreate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> list[JobSkill]:
    job = _get_owned_job(job_id, current_user, db)
    existing_ids = {
        skill_id
        for (skill_id,) in db.query(JobSkill.skill_id).filter(JobSkill.job_id == job.id).all()
    }
    new_ids = {skill.skill_id for skill in skill_data.skills}
    if existing_ids.intersection(new_ids):
        raise _duplicate_error()
    for skill in skill_data.skills:
        _validate_skill(skill, db)
    job_skills = [JobSkill(job_id=job.id, **skill.model_dump()) for skill in skill_data.skills]
    db.add_all(job_skills)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _duplicate_error()
    for job_skill in job_skills:
        db.refresh(job_skill)
    return job_skills


@router.patch("/{skill_id}", response_model=JobSkillResponse)
def update_job_skill(
    job_id: int,
    skill_id: str,
    skill_data: JobSkillUpdate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> JobSkill:
    job = _get_owned_job(job_id, current_user, db)
    job_skill = (
        db.query(JobSkill)
        .filter(JobSkill.job_id == job.id, JobSkill.skill_id == skill_id)
        .first()
    )
    if job_skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job skill not found.")
    for field, value in skill_data.model_dump(exclude_unset=True).items():
        setattr(job_skill, field, value)
    db.commit()
    db.refresh(job_skill)
    return job_skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_skill(
    job_id: int,
    skill_id: str,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> None:
    job = _get_owned_job(job_id, current_user, db)
    job_skill = (
        db.query(JobSkill)
        .filter(JobSkill.job_id == job.id, JobSkill.skill_id == skill_id)
        .first()
    )
    if job_skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job skill not found.")
    db.delete(job_skill)
    db.commit()