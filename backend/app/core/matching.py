"""Deterministic candidate/job matching calculations."""

from dataclasses import dataclass

from app.core.representations import SkillProfile
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


def _experience_score(candidate: SkillProfile, job: Job) -> float | None:
    if candidate.experience_years is None:
        return None
    if job.experience_min is None and job.experience_max is None:
        return None
    if job.experience_min is not None and candidate.experience_years < float(job.experience_min):
        return 0.0
    if job.experience_max is not None and candidate.experience_years > float(job.experience_max):
        return 0.0
    return 1.0


def _education_score(candidate: SkillProfile, job: Job) -> float | None:
    if not candidate.education or not job.education_requirement:
        return None
    candidate_education = candidate.education.casefold()
    requirement = job.education_requirement.casefold()
    return 1.0 if requirement in candidate_education or candidate_education in requirement else 0.0


def _location_work_mode_score(candidate: SkillProfile, job: Job) -> float | None:
    if not candidate.location and not job.location and not job.work_mode:
        return None
    if not candidate.location:
        return None
    if not job.location and not job.work_mode:
        return None
    cand_loc = candidate.location.casefold().strip()
    if job.work_mode and job.work_mode.casefold() == "remote":
        return 1.0
    if "remote" in cand_loc:
        return 1.0
    if not job.location:
        return None
    job_loc = job.location.casefold().strip()
    if cand_loc == job_loc or cand_loc in job_loc or job_loc in cand_loc:
        return 1.0
    job_tokens = [tok.strip() for tok in job_loc.replace("|", ",").split(",") if tok.strip()]
    if any(cand_loc == tok or tok in cand_loc for tok in job_tokens):
        return 1.0
    return 0.0


def match_candidate_to_job(candidate: SkillProfile, job: Job) -> MatchingResult:
    """Calculate a deterministic match score for one canonical candidate/job pair."""
    job_skills = [job_skill for job_skill in job.job_skills if job_skill.skill_id]
    if not job_skills:
        raise NoUsableJobSkillsError(f"Job has no usable canonical skills: {job.id}")
    if any(skill.taxonomy_version != candidate.taxonomy_version for skill in job_skills):
        raise MatchingError(f"Taxonomy version mismatch for job: {job.id}")

    candidate_ids = {skill.skill_id for skill in candidate.skills}
    total_importance = sum(float(skill.role_importance) for skill in job_skills)
    matched_importance = sum(
        float(skill.role_importance)
        for skill in job_skills
        if skill.skill_id in candidate_ids
    )
    component_scores: dict[str, float] = {
        "skill_coverage": matched_importance / total_importance
        if total_importance > 0
        else 0.0
    }
    available = ["skill_coverage"]
    warnings = ["Semantic similarity is unavailable; score was renormalized."]

    optional_components = {
        "experience": _experience_score(candidate, job),
        "education": _education_score(candidate, job),
        "location_work_mode": _location_work_mode_score(candidate, job),
    }
    for name, score in optional_components.items():
        if score is not None:
            component_scores[name] = score
            available.append(name)

    omitted = [name for name in MATCHING_WEIGHTS if name not in component_scores]
    available_weight = sum(MATCHING_WEIGHTS[name] for name in available)
    score = sum(component_scores[name] * MATCHING_WEIGHTS[name] for name in available)
    score = score / available_weight if available_weight else 0.0
    explanation = (
        f"Matched {matched_importance:g} of {total_importance:g} required skill importance; "
        f"scored {', '.join(available)} and omitted {', '.join(omitted) or 'none'}."
    )
    return MatchingResult(
        score=score,
        component_scores=component_scores,
        available_components=tuple(available),
        omitted_components=tuple(omitted),
        explanation=explanation,
        warnings=tuple(warnings),
    )