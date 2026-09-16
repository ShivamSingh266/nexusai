"""Deterministic candidate/job matching calculations."""

from dataclasses import dataclass

from app.core.representations import SkillProfile
from app.core.semantic import skill_text_similarity
from app.models.job import Job


MATCHING_VERSION = "matching-v1"

MATCHING_WEIGHTS = {
    "skill_coverage": 0.60,
    "semantic_similarity": 0.20,
    "experience": 0.10,
    "education": 0.05,
    "location_work_mode": 0.05,
}


class MatchingError(Exception):
    """Base error for an unusable matching input."""


class NoUsableJobSkillsError(MatchingError):
    """The job has no canonical JobSkill requirements."""


@dataclass(frozen=True)
class MatchingResult:
    score: float
    component_scores: dict[str, float]
    available_components: tuple[str, ...]
    omitted_components: tuple[str, ...]
    explanation: str
    warnings: tuple[str, ...]


def _experience_score(
    candidate: SkillProfile,
    job: Job,
) -> float | None:
    """Score candidate experience against the job's experience range."""
    if candidate.experience_years is None:
        return None

    if job.experience_min is None and job.experience_max is None:
        return None

    if (
        job.experience_min is not None
        and candidate.experience_years < float(job.experience_min)
    ):
        return 0.0

    if (
        job.experience_max is not None
        and candidate.experience_years > float(job.experience_max)
    ):
        return 0.0

    return 1.0


def _education_score(
    candidate: SkillProfile,
    job: Job,
) -> float | None:
    """Score education using deterministic case-insensitive containment."""
    if not candidate.education or not job.education_requirement:
        return None

    candidate_education = candidate.education.casefold().strip()
    requirement = job.education_requirement.casefold().strip()
    if not candidate_education or not requirement:
        return None

    return (
        1.0
        if (
            requirement in candidate_education
            or candidate_education in requirement
        )
        else 0.0
    )

def _location_work_mode_score(
    candidate: SkillProfile,
    job: Job,
) -> float | None:
    """Score location/work-mode compatibility deterministically."""
    normalized_districts = [
        district.casefold().strip()
        for district in job.districts
        if district.strip()
    ]

    if (
        not candidate.location
        and not job.location
        and not normalized_districts
        and not job.work_mode
    ):
        return None

    if not candidate.location:
        return None

    if (
        not job.location
        and not normalized_districts
        and not job.work_mode
    ):
        return None

    candidate_location = candidate.location.casefold().strip()

    if not candidate_location:
        return None

    if job.work_mode and job.work_mode.casefold().strip() == "remote":
        return 1.0

    if "remote" in candidate_location:
        return 1.0

    if not job.location and not normalized_districts:
        return None

    job_locations = normalized_districts

    if job.location:
        job_locations.append(job.location.casefold().strip())

    if any(
        candidate_location == job_location
        or candidate_location in job_location
        or job_location in candidate_location
        for job_location in job_locations
    ):
        return 1.0

    return 0.0

def _semantic_similarity_score(
    candidate: SkillProfile,
    job: Job,
) -> float | None:
    """Calculate semantic similarity when both candidate and job text exist."""
    candidate_text = candidate.semantic_text

    job_parts = [
        job.title,
        job.description,
    ]

    job_text = " ".join(
        part.strip()
        for part in job_parts
        if part and part.strip()
    )

    if not candidate_text or not job_text:
        return None

    return skill_text_similarity(
        candidate_text,
        job_text,
    )


def match_candidate_to_job(
    candidate: SkillProfile,
    job: Job,
) -> MatchingResult:
    """Calculate a deterministic match score for one candidate/job pair."""
    job_skills = [
        job_skill
        for job_skill in job.job_skills
        if job_skill.skill_id
    ]

    if not job_skills:
        raise NoUsableJobSkillsError(
            f"Job has no usable canonical skills: {job.id}"
        )

    if any(
        skill.taxonomy_version != candidate.taxonomy_version
        for skill in job_skills
    ):
        raise MatchingError(
            f"Taxonomy version mismatch for job: {job.id}"
        )

    candidate_ids = {
        skill.skill_id
        for skill in candidate.skills
    }

    total_importance = sum(
        float(skill.role_importance)
        for skill in job_skills
    )

    matched_importance = sum(
        float(skill.role_importance)
        for skill in job_skills
        if skill.skill_id in candidate_ids
    )

    skill_coverage = (
        matched_importance / total_importance
        if total_importance > 0
        else 0.0
    )

    component_scores: dict[str, float] = {
        "skill_coverage": skill_coverage,
    }

    available = ["skill_coverage"]
    warnings: list[str] = []

    semantic_similarity = _semantic_similarity_score(
        candidate,
        job,
    )

    if semantic_similarity is not None:
        component_scores["semantic_similarity"] = semantic_similarity
        available.append("semantic_similarity")
    else:
        warnings.append(
            "Semantic similarity is unavailable because candidate "
            "or job text is missing."
        )

    optional_components = {
        "experience": _experience_score(candidate, job),
        "education": _education_score(candidate, job),
        "location_work_mode": _location_work_mode_score(
            candidate,
            job,
        ),
    }

    for name, value in optional_components.items():
        if value is not None:
            component_scores[name] = value
            available.append(name)

    omitted = [
        name
        for name in MATCHING_WEIGHTS
        if name not in component_scores
    ]

    available_weight = sum(
        MATCHING_WEIGHTS[name]
        for name in available
    )

    score = (
        sum(
            component_scores[name] * MATCHING_WEIGHTS[name]
            for name in available
        )
        / available_weight
        if available_weight > 0
        else 0.0
    )

    component_details = ", ".join(
        f"{name}={component_scores[name]:.4f}"
        for name in available
    )

    explanation = (
        f"Components: {component_details}. "
        f"Omitted: {', '.join(omitted) if omitted else 'none'}. "
        f"Final score={score:.4f}. "
        f"Scoring version={MATCHING_VERSION}."
    )

    return MatchingResult(
        score=score,
        component_scores=component_scores,
        available_components=tuple(available),
        omitted_components=tuple(omitted),
        explanation=explanation,
        warnings=tuple(warnings),
    )
