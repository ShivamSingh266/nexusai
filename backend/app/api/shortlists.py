from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.ranking import rank_candidates
from app.core.representations import SkillEntry, SkillProfile
from app.schemas.shortlist import (
    ShortlistCandidate,
    ShortlistRequest,
    ShortlistResponse,
)


router = APIRouter(
    prefix="/shortlists",
    tags=["Shortlists"],
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
    "",
    response_model=ShortlistResponse,
    summary="Rank candidates for a job",
)
def create_shortlist(
    request: ShortlistRequest,
) -> ShortlistResponse:
    job = _to_skill_profile(request.job)

    if job.kind != "job":
        raise HTTPException(
            status_code=422,
            detail="job.kind must be 'job'.",
        )

    candidates = [
        _to_skill_profile(candidate)
        for candidate in request.candidates
    ]

    invalid_candidates = [
        candidate.owner_id
        for candidate in candidates
        if candidate.kind != "candidate"
    ]

    if invalid_candidates:
        raise HTTPException(
            status_code=422,
            detail="All candidate profiles must have kind='candidate'.",
        )

    ranked = rank_candidates(job, candidates)

    return ShortlistResponse(
        candidates=[
            ShortlistCandidate(
                candidate_id=item.candidate_id,
                final_score=item.match.final_score,
                matched_skills=item.match.matched_skills,
                missing_skills=item.match.missing_skills,
                scoring_version=item.match.scoring_version,
                explanation={
                    "skill_score": item.match.explanation.skill_score,
                    "semantic_score": item.match.explanation.semantic_score,
                    "experience_score": item.match.explanation.experience_score,
                    "education_score": item.match.explanation.education_score,
                    "location_mode_score": item.match.explanation.location_mode_score,
                    "weights": item.match.explanation.weights,
                    "final_score": item.match.explanation.final_score,
                },
            )
            for item in ranked
        ]
    )