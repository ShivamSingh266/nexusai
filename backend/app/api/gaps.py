from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.gap import DemandSignal, analyze_gap
from app.core.representations import SkillEntry, SkillProfile
from app.schemas.gap import (
    GapAnalyzeRequest,
    GapAnalyzeResponse,
    GapItemResponse,
)


router = APIRouter(
    prefix="/gaps",
    tags=["Skill Gaps"],
)


def _to_skill_profile(profile_data) -> SkillProfile:
    profile = SkillProfile(
        owner_id=profile_data.owner_id,
        kind=profile_data.kind,
    )

    for skill in profile_data.skills:
        profile.add_skill(
            SkillEntry(
                skill_id=skill.skill_id,
                proficiency=skill.proficiency,
                proficiency_level=skill.proficiency_level,
                min_proficiency=skill.min_proficiency,
                importance=skill.importance,
                evidence=tuple(skill.evidence),
            )
        )

    return profile


@router.post(
    "/analyze",
    response_model=GapAnalyzeResponse,
    summary="Analyze candidate skill gaps",
)
def analyze_gap_endpoint(
    request: GapAnalyzeRequest,
) -> GapAnalyzeResponse:
    candidate = _to_skill_profile(request.candidate)
    target = _to_skill_profile(request.target)

    try:
        demand_signals = {
            skill_id: DemandSignal(
                demand=signal.demand,
                trend_multiplier=signal.trend_multiplier,
            )
            for skill_id, signal in request.demand_signals.items()
        }

        gaps = analyze_gap(
            candidate,
            target,
            demand_signals,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return GapAnalyzeResponse(
        gaps=[
            GapItemResponse(
                skill_id=gap.skill_id,
                severity=gap.severity,
                demand=gap.demand,
                trend_multiplier=gap.trend_multiplier,
                role_importance=gap.role_importance,
                priority=gap.priority,
                explanation=gap.explanation,
            )
            for gap in gaps
        ]
    )