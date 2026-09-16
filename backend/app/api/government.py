from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_db, require_roles
from app.models.canonical_skill import CanonicalSkill
from app.models.user import User
from app.core.config import settings
from app.schemas.government import GovernmentResponse
from app.services.government_data import (
    DATASET_SOURCE_VERSION,
    GovernmentDatasetValidationError,
    read_courses,
    read_demand_history,
    read_training_gaps,
)

router = APIRouter(prefix="/government", tags=["Government"])


def _response(data: list[dict], *, warnings: list[str]) -> GovernmentResponse:
    return GovernmentResponse(
        data=data,
        meta={"count": len(data), "taxonomy_version": settings.TAXONOMY_VERSION},
        model_version=None,
        source_version=DATASET_SOURCE_VERSION,
        generated_at=datetime.now(timezone.utc),
        warnings=warnings,
    )


def _validate_skill(skill_id: str | None, db) -> None:
    if skill_id and db.get(CanonicalSkill, skill_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Canonical skill not found: {skill_id}",
        )


@router.get("/demand", response_model=GovernmentResponse)
def get_demand(
    skill_id: str | None = Query(default=None),
    district_id: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    current_user: User = Depends(require_roles("government", "admin")),
    db=Depends(get_db),
) -> GovernmentResponse:
    _validate_skill(skill_id, db)
    try:
        rows = read_demand_history(
            skill_id=skill_id,
            district_id=district_id,
            sector=sector,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Demand dataset unavailable") from exc
    except GovernmentDatasetValidationError as exc:
        raise HTTPException(status_code=503, detail="Demand dataset invalid") from exc
    return _response(
        rows,
        warnings=[
            "Forecast data is unavailable; this endpoint returns observed demand history only."
        ],
    )


@router.get("/courses", response_model=GovernmentResponse)
def get_courses(
    skill_id: str | None = Query(default=None),
    current_user: User = Depends(require_roles("government", "admin")),
    db=Depends(get_db),
) -> GovernmentResponse:
    _validate_skill(skill_id, db)
    try:
        rows = read_courses(skill_id=skill_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Course dataset unavailable") from exc
    except GovernmentDatasetValidationError as exc:
        raise HTTPException(status_code=503, detail="Course dataset invalid") from exc
    return _response(rows, warnings=[])


@router.get("/training-gaps", response_model=GovernmentResponse)
def get_training_gaps(
    skill_id: str | None = Query(default=None),
    current_user: User = Depends(require_roles("government", "admin")),
    db=Depends(get_db),
) -> GovernmentResponse:
    _validate_skill(skill_id, db)
    try:
        rows = read_training_gaps(skill_id=skill_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Training-gap dataset unavailable") from exc
    except GovernmentDatasetValidationError as exc:
        raise HTTPException(status_code=503, detail="Training-gap dataset invalid") from exc
    return _response(rows, warnings=[])
