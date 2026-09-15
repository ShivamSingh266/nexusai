from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate


router = APIRouter(
    prefix="/recruiter/company",
    tags=["Recruiter Company"],
)


@router.get(
    "",
    response_model=CompanyResponse,
    summary="Get the current recruiter's company profile",
)
def get_company(
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Company:
    """
    Return the company associated with the authenticated recruiter.
    Raises 404 if no company has been set up yet.
    """
    if current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found. Please create one first.",
        )

    company = db.get(Company, current_user.company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company profile for the current recruiter",
)
def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Company:
    """
    Create a new company and associate it with the authenticated recruiter.
    A recruiter may only have one company at a time. Raises 409 if already exists.
    """
    if current_user.company_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A company profile already exists. Use PATCH to update it.",
        )

    company = Company(**company_data.model_dump())
    db.add(company)
    db.flush()  # Populate company.id without committing

    current_user.company_id = company.id
    db.commit()
    db.refresh(company)

    return company


@router.patch(
    "",
    response_model=CompanyResponse,
    summary="Update the current recruiter's company profile",
)
def update_company(
    company_data: CompanyUpdate,
    current_user: User = Depends(require_roles("recruiter", "admin")),
    db: Session = Depends(get_db),
) -> Company:
    """
    Partially update the company associated with the authenticated recruiter.
    Only provided fields are updated (PATCH semantics).
    Raises 404 if no company has been set up yet.
    """
    if current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found. Please create one first.",
        )

    company = db.get(Company, current_user.company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = company_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)

    return company
