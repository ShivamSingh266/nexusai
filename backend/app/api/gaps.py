"""Applicant gap analysis API."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.gap import DEMAND_SOURCE_VERSION, SCORING_VERSION, analyze_gap
from app.core.representations import SkillProfile, SkillProfileSkill
from app.models.canonical_skill import CanonicalSkill
from app.models.job import Job, JobStatus
from app.models.job_skill import JobSkill
from app.models.user import User
from app.schemas.gap import (
    GapAnalysisRequest,
    GapAnalysisResponse,
    RequiredSkillRequest,
)

router = APIRouter(prefix="/gaps", tags=["Gap Analysis"])


def _validate_canonical_skills(references, taxonomy_version: str, db: Session) -> None:
    for reference in references:
        canonical_skill = db.get(CanonicalSkill, reference.skill_id)
        if canonical_skill is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Canonical skill not found: {reference.skill_id}",
            )
        if canonical_skill.taxonomy_version != taxonomy_version:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Taxonomy version mismatch for {reference.skill_id}",
            )
        if reference.taxonomy_version != canonical_skill.taxonomy_version:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Taxonomy version mismatch for {reference.skill_id}",
            )


def _resolve_required_skills(
    request: GapAnalysisRequest,
    taxonomy_version: str,
    db: Session,
) -> list[RequiredSkillRequest]:
    """Resolve a published internal job when no explicit target is supplied."""
    if request.target.required_skills or request.target.job_id is None:
        return request.target.required_skills

    job = db.get(Job, request.target.job_id)
    if job is None or job.status != JobStatus.published.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    job_skills = (
        db.query(JobSkill)
        .filter(JobSkill.job_id == job.id)
        .order_by(JobSkill.id)
        .all()
    )
    if not job_skills:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job has no canonical skills",
        )

    resolved: list[RequiredSkillRequest] = []
    for job_skill in job_skills:
        canonical_skill = db.get(CanonicalSkill, job_skill.skill_id)
        if (
            canonical_skill is None
            or canonical_skill.taxonomy_version != job_skill.taxonomy_version
            or job_skill.taxonomy_version != taxonomy_version
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Taxonomy version mismatch for {job_skill.skill_id}",
            )
        resolved.append(
            RequiredSkillRequest(
                skill_id=job_skill.skill_id,
                taxonomy_version=job_skill.taxonomy_version,
                role_importance=float(job_skill.role_importance),
            )
        )
    return resolved


@router.post("/analyze", response_model=GapAnalysisResponse)
def analyze_applicant_gap(
    request: GapAnalysisRequest,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> GapAnalysisResponse:
    """Analyze explicit canonical target skills for the authenticated applicant."""
    if request.candidate.subject_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate profile does not belong to the authenticated applicant",
        )

    candidate_references = request.candidate.skills
    candidate_ids = [skill.skill_id for skill in candidate_references]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Candidate skills must not contain duplicates",
        )

    _validate_canonical_skills(candidate_references, request.candidate.taxonomy_version, db)
    required_skills = _resolve_required_skills(
        request,
        request.candidate.taxonomy_version,
        db,
    )
    _validate_canonical_skills(required_skills, request.candidate.taxonomy_version, db)

    candidate = SkillProfile(
        subject_id=request.candidate.subject_id,
        subject_type=request.candidate.subject_type,
        taxonomy_version=request.candidate.taxonomy_version,
        skills=tuple(
            SkillProfileSkill(
                skill_id=skill.skill_id,
                taxonomy_version=skill.taxonomy_version,
                proficiency_level=skill.proficiency_level,
                years_experience=skill.years_experience,
            )
            for skill in candidate_references
        ),
        location=request.candidate.location,
        education=request.candidate.education,
        experience_years=request.candidate.experience_years,
    )
    matched, missing, warnings = analyze_gap(
        candidate=candidate,
        required_skills=tuple(
            (skill.skill_id, skill.role_importance)
            for skill in required_skills
        ),
        district_id=request.context.district_id,
        sector=request.context.sector,
    )

    if any(skill.skill_id is None for skill in current_user.applicant_skills):
        warnings.append("Unmapped free-text applicant skills were ignored.")

    return GapAnalysisResponse(
        data={
            "matched_skills": [skill.__dict__ for skill in matched],
            "missing_skills": [skill.__dict__ for skill in missing],
        },
        meta={
            "scoring_version": SCORING_VERSION,
            "taxonomy_version": request.candidate.taxonomy_version,
            "demand_source_version": DEMAND_SOURCE_VERSION,
        },
        model_version=None,
        source_version="backend-v1",
        generated_at=datetime.now(timezone.utc),
        warnings=warnings,
    )