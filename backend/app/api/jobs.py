"""
Job management API — /api/v1/jobs

Authorization matrix:
  recruiter : create, read (company-scoped), update, delete
              draft/published/closed all visible for own company
  applicant : read published jobs only (GET list + GET detail)
              cannot create / update / delete
  government: read published jobs only (same as applicant)
  admin     : read-only here (admin CRUD via admin panel, not this router)

Cross-company isolation:
  Recruiters can only modify jobs that belong to their company.
  A recruiter without a company gets 403 on mutating operations.

Future extension point:
  When Member 4's canonical_skills table lands, a separate JobSkill router
  (POST /jobs/{id}/skills, DELETE /jobs/{id}/skills/{skill_id}) will be
  added without changing this file.
"""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db, require_roles
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.job import JobCreate, JobListResponse, JobResponse, JobUpdate

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100


def _get_recruiter_company_id(current_user: User) -> int:
    """
    Return the company_id of a recruiter, or raise 403 if they have no company.
    Recruiters must have a company before they can manage jobs.
    """
    if current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must create a company profile before managing job postings.",
        )
    return current_user.company_id


def _get_owned_job(job_id: int, company_id: int, db: Session) -> Job:
    """
    Fetch a job that belongs to the given company. Returns 404 if not found
    or if the job belongs to a different company (prevents information leakage).
    """
    job = db.get(Job, job_id)
    if job is None or job.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )
    return job


def _build_list_query(
    db: Session,
    *,
    company_id: int | None,
    status_filter: str | None,
    title: str | None,
    location: str | None,
    employment_type: str | None,
    work_mode: str | None,
):
    """
    Build a filtered SQLAlchemy query. When company_id is provided, all
    statuses for that company are returned (recruiter view). Otherwise only
    published jobs are returned (applicant/public view), and company_id
    filtering is omitted.
    """
    q = db.query(Job)

    if company_id is not None:
        # Recruiter: see all own jobs, filtered by requested status if any
        q = q.filter(Job.company_id == company_id)
        if status_filter:
            q = q.filter(Job.status == status_filter)
    else:
        # Public / applicant / government: published only, ignores status_filter
        q = q.filter(Job.status == JobStatus.published.value)

    if title:
        q = q.filter(Job.title.ilike(f"%{title}%"))
    if location:
        q = q.filter(Job.location.ilike(f"%{location}%"))
    if employment_type:
        q = q.filter(Job.employment_type == employment_type)
    if work_mode:
        q = q.filter(Job.work_mode == work_mode)

    return q


# ---------------------------------------------------------------------------
# POST /jobs — recruiter creates a job
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job posting (recruiter only)",
)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Job:
    """
    Create a new job posting under the authenticated recruiter's company.
    The recruiter must have a company profile first (403 otherwise).
    New jobs default to 'draft' status unless explicitly set to 'published'.
    """
    company_id = _get_recruiter_company_id(current_user)

    job = Job(
        company_id=company_id,
        **job_data.model_dump(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# GET /jobs — list jobs (role-aware)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=JobListResponse,
    summary="List job postings",
)
def list_jobs(
    # Filters
    title: str | None = Query(default=None, description="Partial title search"),
    location: str | None = Query(default=None, description="Partial location search"),
    employment_type: str | None = Query(default=None),
    work_mode: str | None = Query(default=None),
    job_status: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status (recruiter only; ignored for applicants)",
    ),
    # Pagination
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    # Auth — optional so applicants and unauthenticated users both work
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """
    List jobs with filtering and pagination.

    - Recruiters see all jobs belonging to their company (all statuses).
    - Applicants, government users, and unauthenticated callers see only
      published jobs across all companies.

    Filters: title (partial), location (partial), employment_type, work_mode.
    Recruiter-only filter: status (draft | published | closed).
    """
    is_recruiter = (
        current_user is not None
        and current_user.role.name in ("recruiter", "admin")
    )

    recruiter_company_id: int | None = None
    if is_recruiter and current_user.company_id is not None:
        recruiter_company_id = current_user.company_id

    q = _build_list_query(
        db,
        company_id=recruiter_company_id,
        status_filter=job_status if is_recruiter else None,
        title=title,
        location=location,
        employment_type=employment_type,
        work_mode=work_mode,
    )

    total = q.count()
    jobs = (
        q.order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return JobListResponse(
        data=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ---------------------------------------------------------------------------
# GET /jobs/{job_id} — single job detail
# ---------------------------------------------------------------------------


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get a single job posting",
)
def get_job(
    job_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Job:
    """
    Retrieve a specific job.

    - Recruiters can view any job that belongs to their company (any status).
    - All other callers can only view published jobs.
    """
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    is_recruiter = (
        current_user is not None
        and current_user.role.name in ("recruiter", "admin")
    )

    if is_recruiter:
        # Recruiter may only see their own company's job
        if current_user.company_id != job.company_id:
            # Return 404 to avoid leaking the existence of other companies' jobs
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
    else:
        # Applicant / government / unauthenticated: published only
        if job.status != JobStatus.published.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )

    return job


# ---------------------------------------------------------------------------
# PATCH /jobs/{job_id} — recruiter updates a job
# ---------------------------------------------------------------------------


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update a job posting (recruiter only)",
)
def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Job:
    """
    Partially update a job posting. Only the provided fields are changed.
    The recruiter must own the job's company.
    """
    company_id = _get_recruiter_company_id(current_user)
    job = _get_owned_job(job_id, company_id, db)

    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# DELETE /jobs/{job_id} — recruiter deletes a job
# ---------------------------------------------------------------------------


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job posting (recruiter only)",
)
def delete_job(
    job_id: int,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> None:
    """
    Permanently delete a job posting. Only the owning company's recruiter
    may delete it.
    """
    company_id = _get_recruiter_company_id(current_user)
    job = _get_owned_job(job_id, company_id, db)

    db.delete(job)
    db.commit()
    return None
