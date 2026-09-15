"""Recruiter shortlist management API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.models.job import Job
from app.models.shortlist import Shortlist
from app.models.user import User
from app.schemas.shortlist import (
    ShortlistCreate,
    ShortlistResponse,
    ShortlistUpdate,
)

router = APIRouter(
    prefix="/shortlists",
    tags=["Shortlists"],
)


def _check_recruiter_company(current_user: User) -> None:
    if current_user.role.name == "recruiter" and current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must create a company profile before managing shortlists.",
        )


def _get_owned_job(job_id: int, current_user: User, db: Session) -> Job:
    _check_recruiter_company(current_user)
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )
    if current_user.role.name != "admin" and job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )
    return job


def _get_candidate(candidate_id: int, db: Session) -> User:
    candidate = db.get(User, candidate_id)
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )
    if candidate.role.name != "applicant":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only candidates with applicant role can be shortlisted.",
        )
    return candidate


@router.post("", response_model=ShortlistResponse, status_code=status.HTTP_201_CREATED)
def create_shortlist(
    payload: ShortlistCreate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Shortlist:
    """Shortlist a candidate for a job."""
    job = _get_owned_job(payload.job_id, current_user, db)
    candidate = _get_candidate(payload.candidate_id, db)

    existing = (
        db.query(Shortlist)
        .filter(Shortlist.job_id == job.id, Shortlist.candidate_id == candidate.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate is already shortlisted for this job.",
        )

    shortlist_entry = Shortlist(
        job_id=job.id,
        candidate_id=candidate.id,
        notes=payload.notes,
        match_score=payload.match_score,
    )
    db.add(shortlist_entry)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate is already shortlisted for this job.",
        )
    db.refresh(shortlist_entry)
    return (
        db.query(Shortlist)
        .options(joinedload(Shortlist.candidate))
        .filter(Shortlist.id == shortlist_entry.id)
        .one()
    )


@router.get("/job/{job_id}", response_model=list[ShortlistResponse])
def list_shortlists_for_job(
    job_id: int,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> list[Shortlist]:
    """List shortlisted candidates for a recruiter-owned job."""
    job = _get_owned_job(job_id, current_user, db)
    return (
        db.query(Shortlist)
        .options(joinedload(Shortlist.candidate))
        .filter(Shortlist.job_id == job.id)
        .order_by(Shortlist.created_at.desc(), Shortlist.id.asc())
        .all()
    )


@router.get("", response_model=list[ShortlistResponse])
def list_shortlists(
    job_id: int | None = Query(default=None, description="Filter by job ID"),
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> list[Shortlist]:
    """List shortlists for recruiter's company or filtered by job."""
    if job_id is not None:
        return list_shortlists_for_job(job_id, current_user, db)

    _check_recruiter_company(current_user)
    query = db.query(Shortlist).options(joinedload(Shortlist.candidate))
    if current_user.role.name != "admin":
        query = query.join(Job, Shortlist.job_id == Job.id).filter(
            Job.company_id == current_user.company_id
        )
    return query.order_by(Shortlist.created_at.desc(), Shortlist.id.asc()).all()


@router.get("/{shortlist_id}", response_model=ShortlistResponse)
def get_shortlist_entry(
    shortlist_id: int,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Shortlist:
    """Get a single shortlist entry."""
    _check_recruiter_company(current_user)
    entry = (
        db.query(Shortlist)
        .options(joinedload(Shortlist.candidate), joinedload(Shortlist.job))
        .filter(Shortlist.id == shortlist_id)
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist entry not found.",
        )
    if current_user.role.name != "admin" and entry.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist entry not found.",
        )
    return entry


@router.patch("/{shortlist_id}", response_model=ShortlistResponse)
def update_shortlist_entry(
    shortlist_id: int,
    payload: ShortlistUpdate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Shortlist:
    """Update notes on a shortlist entry."""
    _check_recruiter_company(current_user)
    entry = (
        db.query(Shortlist)
        .options(joinedload(Shortlist.candidate), joinedload(Shortlist.job))
        .filter(Shortlist.id == shortlist_id)
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist entry not found.",
        )
    if current_user.role.name != "admin" and entry.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist entry not found.",
        )
    if payload.notes is not None:
        entry.notes = payload.notes
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{shortlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shortlist_by_id(
    shortlist_id: int,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> None:
    """Remove a candidate from a shortlist by shortlist ID."""
    _check_recruiter_company(current_user)
    entry = (
        db.query(Shortlist)
        .join(Job, Shortlist.job_id == Job.id)
        .filter(Shortlist.id == shortlist_id)
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist entry not found.",
        )
    if current_user.role.name != "admin" and entry.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist entry not found.",
        )
    db.delete(entry)
    db.commit()


@router.delete("/job/{job_id}/candidate/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shortlist_by_job_and_candidate(
    job_id: int,
    candidate_id: int,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> None:
    """Remove a candidate from a shortlist by job ID and candidate ID."""
    job = _get_owned_job(job_id, current_user, db)
    entry = (
        db.query(Shortlist)
        .filter(Shortlist.job_id == job.id, Shortlist.candidate_id == candidate_id)
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate is not shortlisted for this job.",
        )
    db.delete(entry)
    db.commit()
