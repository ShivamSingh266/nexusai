from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.gaps import _resolve_required_skills, _validate_canonical_skills
from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.core.gap import analyze_gap
from app.core.representations import SkillProfile
from app.models.canonical_skill import CanonicalSkill
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapItemStatus, RoadmapStatus
from app.models.user import User
from app.schemas.gap import CandidateProfileRequest, GapAnalysisRequest
from app.schemas.roadmap import (
    RoadmapCreate,
    RoadmapGenerateRequest,
    RoadmapItemResponse,
    RoadmapItemUpdate,
    RoadmapResponse,
)
from app.services.skill_profile import (
    CandidateProfileNotFoundError,
    CandidateSkillValidationError,
    load_candidate_skill_profile,
)

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


def _validate_skill(skill_id: str, taxonomy_version: str, db: Session) -> None:
    skill = db.get(CanonicalSkill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Canonical skill not found: {skill_id}",
        )
    if skill.taxonomy_version != taxonomy_version:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Taxonomy version mismatch for {skill_id}",
        )


def _get_owned_roadmap(roadmap_id: int, user_id: int, db: Session) -> Roadmap:
    roadmap = (
        db.query(Roadmap)
        .options(selectinload(Roadmap.items))
        .filter(Roadmap.id == roadmap_id, Roadmap.applicant_id == user_id)
        .first()
    )
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return roadmap


@router.post("", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap(
    roadmap_data: RoadmapCreate,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> Roadmap:
    if roadmap_data.taxonomy_version != settings.TAXONOMY_VERSION:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported taxonomy version",
        )
    for item in roadmap_data.items:
        _validate_skill(item.skill_id, item.taxonomy_version, db)

    roadmap = Roadmap(
        applicant_id=current_user.id,
        title=roadmap_data.title,
        taxonomy_version=roadmap_data.taxonomy_version,
        status=roadmap_data.status.value,
    )
    roadmap.items = [
        RoadmapItem(
            skill_id=item.skill_id,
            taxonomy_version=item.taxonomy_version,
            position=item.position,
            status=item.status.value,
            course_id=item.course_id,
            resource_url=str(item.resource_url) if item.resource_url else None,
            resource_title=item.resource_title,
            notes=item.notes,
        )
        for item in roadmap_data.items
    ]
    db.add(roadmap)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Roadmap item positions must be unique",
        ) from exc
    return _get_owned_roadmap(roadmap.id, current_user.id, db)


@router.post(
    "/generate",
    response_model=RoadmapResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_roadmap(
    request: RoadmapGenerateRequest,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> Roadmap:
    """Generate a new deterministic roadmap from the applicant's persisted gaps."""
    try:
        candidate = load_candidate_skill_profile(db, current_user.id)
    except CandidateProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Applicant profile is required to generate a roadmap",
        ) from exc
    except CandidateSkillValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    candidate_ids = [skill.skill_id for skill in candidate.skills]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Applicant skills must not contain duplicates",
        )

    required_skills = _resolve_required_skills(
        _roadmap_request_to_gap_request(request, candidate),
        candidate.taxonomy_version,
        db,
    )
    _validate_canonical_skills(required_skills, candidate.taxonomy_version, db)
    _, missing_skills, _ = analyze_gap(
        candidate=candidate,
        required_skills=tuple(
            (skill.skill_id, skill.role_importance)
            for skill in required_skills
        ),
        district_id=request.context.district_id,
        sector=request.context.sector,
    )

    roadmap = Roadmap(
        applicant_id=current_user.id,
        title=_roadmap_title(request.title, request.target.job_id),
        taxonomy_version=settings.TAXONOMY_VERSION,
        status=RoadmapStatus.active,
        items=[
            RoadmapItem(
                skill_id=skill.skill_id,
                taxonomy_version=skill.taxonomy_version,
                position=position,
                status=RoadmapItemStatus.pending,
                notes=skill.explanation,
            )
            for position, skill in enumerate(missing_skills)
        ],
    )
    db.add(roadmap)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Generated roadmap could not be persisted",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generated roadmap could not be persisted",
        ) from exc
    return _get_owned_roadmap(roadmap.id, current_user.id, db)


def _roadmap_request_to_gap_request(
    request: RoadmapGenerateRequest,
    candidate: SkillProfile,
) -> GapAnalysisRequest:
    """Build the existing gap request shape without accepting client candidate data."""
    return GapAnalysisRequest(
        candidate=CandidateProfileRequest(
            subject_id=candidate.subject_id,
            subject_type=candidate.subject_type,
            taxonomy_version=candidate.taxonomy_version,
            skills=[
                {
                    "skill_id": skill.skill_id,
                    "taxonomy_version": skill.taxonomy_version,
                    "proficiency_level": skill.proficiency_level,
                    "years_experience": skill.years_experience,
                }
                for skill in candidate.skills
            ],
            location=candidate.location,
            education=candidate.education,
            experience_years=candidate.experience_years,
        ),
        target=request.target,
        context=request.context,
    )


def _roadmap_title(title: str | None, job_id: int | None) -> str:
    if title is not None and title.strip():
        return title.strip()
    if job_id is not None:
        return "Roadmap for target job"
    return "Generated skills roadmap"


@router.get("", response_model=list[RoadmapResponse])
def list_roadmaps(
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> list[Roadmap]:
    return (
        db.query(Roadmap)
        .options(selectinload(Roadmap.items))
        .filter(Roadmap.applicant_id == current_user.id)
        .order_by(Roadmap.id)
        .all()
    )


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
def get_roadmap(
    roadmap_id: int,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> Roadmap:
    return _get_owned_roadmap(roadmap_id, current_user.id, db)


@router.patch("/{roadmap_id}/items/{item_id}", response_model=RoadmapItemResponse)
def update_roadmap_item(
    roadmap_id: int,
    item_id: int,
    item_data: RoadmapItemUpdate,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> RoadmapItem:
    roadmap = _get_owned_roadmap(roadmap_id, current_user.id, db)
    item = next((item for item in roadmap.items if item.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found")

    for field, value in item_data.model_dump(exclude_unset=True).items():
        setattr(item, field, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{roadmap_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roadmap_item(
    roadmap_id: int,
    item_id: int,
    current_user: User = Depends(require_roles("applicant")),
    db: Session = Depends(get_db),
) -> None:
    roadmap = _get_owned_roadmap(roadmap_id, current_user.id, db)
    item = next((item for item in roadmap.items if item.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found")
    db.delete(item)
    db.commit()
