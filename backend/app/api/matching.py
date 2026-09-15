"""Candidate/job matching API."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_roles
from app.core.matching import (
    MATCHING_VERSION,
    MatchingError,
    NoUsableJobSkillsError,
    match_candidate_to_job,
)
from app.models.job import Job, JobStatus
from app.models.user import Role, User
from app.schemas.matching import MatchingResponse, MatchingResultResponse
from app.services.skill_profile import (
    CandidateNotFoundError,
    CandidateProfileNotFoundError,
    CandidateSkillValidationError,
    load_candidate_skill_profile,
)

router = APIRouter(prefix="/matching", tags=["Matching"])


def _response(
    results: list[MatchingResultResponse],
    warnings: list[str],
) -> MatchingResponse:
    return MatchingResponse(
        data=results,
        meta={"matching_version": MATCHING_VERSION},
        model_version=None,
        source_version="backend-v1",
        generated_at=datetime.now(timezone.utc),
        warnings=warnings,
    )


def _result(candidate_id: int, job: Job, match) -> MatchingResultResponse:
    taxonomy_version = job.job_skills[0].taxonomy_version
    return MatchingResultResponse(
        candidate_id=candidate_id,
        job_id=job.id,
        score=match.score,
        component_scores=match.component_scores,
        available_components=list(match.available_components),
        omitted_components=list(match.omitted_components),
        taxonomy_version=taxonomy_version,
        explanation=match.explanation,
        warnings=list(match.warnings),
    )


@router.get("/jobs", response_model=MatchingResponse)
def matching_jobs(
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> MatchingResponse:
    """Return published jobs ranked for the authenticated applicant."""
    try:
        candidate = load_candidate_skill_profile(db, current_user.id)
    except (CandidateNotFoundError, CandidateProfileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CandidateSkillValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if not candidate.skills:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Candidate has no usable canonical skills",
        )

    jobs = db.scalars(
        select(Job)
        .where(Job.status == JobStatus.published.value)
        .options(selectinload(Job.job_skills))
        .order_by(Job.id)
    ).all()
    results: list[MatchingResultResponse] = []
    warnings: list[str] = []
    for job in jobs:
        try:
            results.append(_result(current_user.id, job, match_candidate_to_job(candidate, job)))
        except NoUsableJobSkillsError:
            warnings.append(f"Job {job.id} was omitted because it has no usable canonical skills.")
        except MatchingError as exc:
            warnings.append(str(exc))
    results.sort(key=lambda item: (-item.score, item.job_id))
    return _response(results, warnings)


@router.get("/candidates/{job_id}", response_model=MatchingResponse)
def matching_candidates(
    job_id: int,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> MatchingResponse:
    """Return applicant candidates ranked for an owned internal job."""
    job = db.scalar(
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.job_skills))
    )
    is_admin = current_user.role.name == "admin"
    if job is None or (not is_admin and current_user.company_id != job.company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not job.job_skills:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job has no usable canonical skills",
        )

    candidates = db.scalars(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == "applicant")
        .order_by(User.id)
    ).all()
    results: list[MatchingResultResponse] = []
    warnings: list[str] = []
    for candidate_user in candidates:
        try:
            candidate = load_candidate_skill_profile(db, candidate_user.id)
            if not candidate.skills:
                warnings.append(
                    f"Candidate {candidate_user.id} was omitted because it has no usable canonical skills."
                )
                continue
            results.append(_result(candidate_user.id, job, match_candidate_to_job(candidate, job)))
        except (CandidateNotFoundError, CandidateProfileNotFoundError):
            warnings.append(f"Candidate {candidate_user.id} was omitted because its profile is unavailable.")
        except (CandidateSkillValidationError, MatchingError) as exc:
            warnings.append(str(exc))
    results.sort(key=lambda item: (-item.score, item.candidate_id))
    return _response(results, warnings)