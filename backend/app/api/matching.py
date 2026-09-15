from __future__ import annotations

from fastapi import APIRouter

from app.core.matcher import match_profiles
from app.core.representations import SkillEntry, SkillProfile
from app.schemas.matching import (
    MatchRequest,
    MatchResponse,
    MatchExplanationResponse,
)


router = APIRouter(
    prefix="/matching",
    tags=["Matching"],
)


def _to_skill_profile(profile_data) -> SkillProfile:
    profile = SkillProfile(
        owner_id=profile_data.owner_id,
        kind=profile_data.kind,
        experience_years=profile_data.experience_years,
        education_level=profile_data.education_level,
        location=profile_data.location,
        work_mode=profile_data.work_mode,
        text=profile_data.text,
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
    "/profiles",
    response_model=MatchResponse,
    summary="Match a candidate profile against a job or role",
)
def match_profile_endpoint(request: MatchRequest) -> MatchResponse:
    candidate = _to_skill_profile(request.candidate)
    target = _to_skill_profile(request.target)

    if candidate.kind != "candidate":
        raise ValueError("candidate.kind must be 'candidate'.")

    if target.kind not in {"job", "role"}:
        raise ValueError("target.kind must be 'job' or 'role'.")

    result = match_profiles(candidate, target)

    return MatchResponse(
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        explanation=MatchExplanationResponse(
            skill_score=result.explanation.skill_score,
            semantic_score=result.explanation.semantic_score,
            experience_score=result.explanation.experience_score,
            education_score=result.explanation.education_score,
            location_mode_score=result.explanation.location_mode_score,
            weights=result.explanation.weights,
            final_score=result.explanation.final_score,
        ),
        final_score=result.final_score,
        scoring_version=result.scoring_version,
    )