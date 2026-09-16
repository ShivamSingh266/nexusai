from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.roadmap import (
    RoadmapCycleError,
    RoadmapStep,
    sequence_roadmap,
)
from app.schemas.roadmap import (
    RoadmapGenerateRequest,
    RoadmapGenerateResponse,
    RoadmapStepResponse,
)


router = APIRouter(
    prefix="/roadmaps",
    tags=["Roadmaps"],
)


ROADMAP_VERSION = "v1"


@router.post(
    "/generate",
    response_model=RoadmapGenerateResponse,
    summary="Generate a prerequisite-aware skill roadmap",
)
def generate_roadmap(
    request: RoadmapGenerateRequest,
) -> RoadmapGenerateResponse:
    steps = [
        RoadmapStep(
            skill_id=step.skill_id,
            priority=step.priority,
            prerequisites=tuple(step.prerequisites),
        )
        for step in request.steps
    ]

    try:
        ordered = sequence_roadmap(steps)
    except RoadmapCycleError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return RoadmapGenerateResponse(
        steps=[
            RoadmapStepResponse(
                skill_id=step.skill_id,
                priority=step.priority,
                prerequisites=list(step.prerequisites),
            )
            for step in ordered
        ],
        scoring_version=ROADMAP_VERSION,
    )