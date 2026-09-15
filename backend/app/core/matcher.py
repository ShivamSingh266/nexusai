from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.representations import SkillProfile
from app.core.scoring import ScoreComponents, calculate_weighted_score
from app.core.semantic import skill_text_similarity


SCORING_VERSION = "v1"


@dataclass(frozen=True)
class MatchExplanation:
    skill_score: float
    semantic_score: float
    experience_score: Optional[float]
    education_score: Optional[float]
    location_mode_score: Optional[float]
    weights: dict[str, float]
    final_score: float


@dataclass(frozen=True)
class MatchResult:
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: MatchExplanation
    final_score: float
    scoring_version: str


def _skill_coverage(
    candidate: SkillProfile,
    target: SkillProfile,
) -> tuple[float, list[str], list[str]]:
    if not target.skills:
        return 1.0, [], []

    matched: list[str] = []
    missing: list[str] = []

    for skill_id, required in target.skills.items():
        candidate_skill = candidate.skills.get(skill_id)

        if candidate_skill is None:
            missing.append(skill_id)
            continue

        if candidate_skill.proficiency >= required.min_proficiency:
            matched.append(skill_id)
        else:
            missing.append(skill_id)

    score = len(matched) / len(target.skills)

    return score, sorted(matched), sorted(missing)


def _experience_score(
    candidate: SkillProfile,
    target: SkillProfile,
) -> Optional[float]:
    if candidate.experience_years is None or target.experience_years is None:
        return None

    required = max(target.experience_years, 0.0)

    if required == 0:
        return 1.0

    return max(
        0.0,
        min(1.0, candidate.experience_years / required),
    )


def _education_score(
    candidate: SkillProfile,
    target: SkillProfile,
) -> Optional[float]:
    if candidate.education_level is None or target.education_level is None:
        return None

    return max(
        0.0,
        min(
            1.0,
            1.0 - abs(
                candidate.education_level - target.education_level
            ),
        ),
    )


def _location_mode_score(
    candidate: SkillProfile,
    target: SkillProfile,
) -> Optional[float]:
    if not any(
        (
            candidate.location,
            target.location,
            candidate.work_mode,
            target.work_mode,
        )
    ):
        return None

    checks: list[float] = []

    if candidate.location and target.location:
        checks.append(
            1.0
            if candidate.location.strip().lower()
            == target.location.strip().lower()
            else 0.0
        )

    if candidate.work_mode and target.work_mode:
        checks.append(
            1.0
            if candidate.work_mode.strip().lower()
            == target.work_mode.strip().lower()
            else 0.0
        )

    if not checks:
        return None

    return sum(checks) / len(checks)


def match_profiles(
    candidate: SkillProfile,
    target: SkillProfile,
) -> MatchResult:
    """
    Reusable matching engine.

    candidate -> target supports both applicant-to-job and recruiter-side
    candidate comparisons by reusing the same scoring implementation.
    """
    skill_score, matched, missing = _skill_coverage(
        candidate,
        target,
    )

    semantic_score = skill_text_similarity(
        candidate.text,
        target.text,
    )

    experience_score = _experience_score(
        candidate,
        target,
    )

    education_score = _education_score(
        candidate,
        target,
    )

    location_mode_score = _location_mode_score(
        candidate,
        target,
    )

    components = ScoreComponents(
        skill=skill_score,
        semantic=semantic_score,
        experience=experience_score,
        education=education_score,
        location_mode=location_mode_score,
    )

    final_score = calculate_weighted_score(components)

    weights = {
        "skill": 0.60,
        "semantic": 0.20,
        "experience": 0.10,
        "education": 0.05,
        "location_mode": 0.05,
    }

    explanation = MatchExplanation(
        skill_score=skill_score,
        semantic_score=semantic_score,
        experience_score=experience_score,
        education_score=education_score,
        location_mode_score=location_mode_score,
        weights=weights,
        final_score=final_score,
    )

    return MatchResult(
        matched_skills=matched,
        missing_skills=missing,
        explanation=explanation,
        final_score=final_score,
        scoring_version=SCORING_VERSION,
    )