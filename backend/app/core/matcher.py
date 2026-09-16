from __future__ import annotations

from dataclasses import dataclass

from app.core.matching import (
    MATCHING_VERSION,
    MatchingResult,
    match_candidate_to_job,
)
from app.core.representations import SkillProfile
from app.models.job import Job


@dataclass(frozen=True)
class MatchExplanation:
    skill_score: float
    semantic_score: float | None
    experience_score: float | None
    education_score: float | None
    location_mode_score: float | None
    weights: dict[str, float]
    final_score: float
    omitted_components: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class MatchResult:
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: MatchExplanation
    final_score: float
    scoring_version: str


def match_candidate_job(
    candidate: SkillProfile,
    job: Job,
) -> MatchResult:
    """
    Adapter around the shared DB-backed candidate/job matcher.

    The shared matching.py implementation is authoritative for persisted
    JobSkill requirements and taxonomy-version validation.
    """
    result: MatchingResult = match_candidate_to_job(candidate, job)

    required_ids = [
        job_skill.skill_id
        for job_skill in job.job_skills
        if job_skill.skill_id
    ]
    candidate_ids = {skill.skill_id for skill in candidate.skills}

    matched = sorted(
        skill_id
        for skill_id in required_ids
        if skill_id in candidate_ids
    )
    missing = sorted(
        skill_id
        for skill_id in required_ids
        if skill_id not in candidate_ids
    )

    explanation = MatchExplanation(
        skill_score=result.component_scores.get("skill_coverage", 0.0),
        semantic_score=result.component_scores.get("semantic_similarity"),
        experience_score=result.component_scores.get("experience"),
        education_score=result.component_scores.get("education"),
        location_mode_score=result.component_scores.get("location_work_mode"),
        weights={
            "skill_coverage": 0.60,
            "semantic_similarity": 0.20,
            "experience": 0.10,
            "education": 0.05,
            "location_work_mode": 0.05,
        },
        final_score=result.score,
        omitted_components=result.omitted_components,
        warnings=result.warnings,
    )

    return MatchResult(
        matched_skills=matched,
        missing_skills=missing,
        explanation=explanation,
        final_score=result.score,
        scoring_version=MATCHING_VERSION,
    )