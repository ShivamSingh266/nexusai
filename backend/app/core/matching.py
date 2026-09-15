"""
Task 04 + 05 — F4 reusable matcher + explainable score components.

Hiring Manager requirement (Final V2): the SAME matcher serves both
applicant->job and recruiter->candidate. There is exactly one function,
match(), below. Both API endpoints (matching.py) call it with the two
SkillProfiles in different order/roles — no second scoring system.

Frozen baseline:
    score = 0.60*skill_coverage + 0.20*semantic + 0.10*experience
            + 0.05*education + 0.05*location
    -> renormalize over whatever components actually have data.
"""
from dataclasses import dataclass, field

from app.config import MATCH_WEIGHTS, settings
from app.core.representations import SkillProfile
from app.core import semantic as semantic_mod


@dataclass
class MatchResult:
    score: float
    components: dict          # component_name -> value in 0..1
    weights_used: dict        # component_name -> renormalized weight actually applied
    matched_skills: list
    missing_skills: list
    explanation: dict
    scoring_version: str = settings.SCORING_VERSION


def _skill_coverage(candidate: SkillProfile, target: SkillProfile):
    """Taxonomy-authoritative exact-id coverage against required min_proficiency."""
    if not target.skills:
        return 1.0, [], []
    matched, missing = [], []
    covered_weight = 0.0
    total_weight = 0.0
    for skill_id, req in target.skills.items():
        w = req.importance or 1.0
        total_weight += w
        cand_entry = candidate.skills.get(skill_id)
        if cand_entry and cand_entry.proficiency >= req.min_proficiency:
            covered_weight += w
            matched.append({
                "skill_id": skill_id,
                "required": req.min_proficiency,
                "candidate": cand_entry.proficiency,
            })
        else:
            missing.append({
                "skill_id": skill_id,
                "required": req.min_proficiency,
                "candidate": cand_entry.proficiency if cand_entry else 0.0,
            })
    coverage = covered_weight / total_weight if total_weight else 1.0
    return coverage, matched, missing


def _experience_fit(candidate: SkillProfile, target: SkillProfile):
    if target.experience_years is None or candidate.experience_years is None:
        return None
    if target.experience_years <= 0:
        return 1.0
    ratio = candidate.experience_years / target.experience_years
    return max(0.0, min(1.0, ratio))


def _education_fit(candidate: SkillProfile, target: SkillProfile):
    if candidate.education_level is None or target.education_level is None:
        return None
    return max(0.0, min(1.0, candidate.education_level / max(target.education_level, 1e-6)))


def _location_fit(candidate: SkillProfile, target: SkillProfile):
    if not target.district and not target.mode:
        return None
    score = 0.0
    parts = 0
    if target.mode:
        parts += 1
        if target.mode.lower() == "remote" or (candidate.mode and candidate.mode.lower() == target.mode.lower()):
            score += 1.0
    if target.district:
        parts += 1
        if candidate.district and candidate.district == target.district:
            score += 1.0
    return score / parts if parts else None


def match(
    candidate_profile: SkillProfile,
    target_profile: SkillProfile,
    skill_name_lookup: dict[str, str] | None = None,
    use_semantic: bool = True,
) -> MatchResult:
    """The single matcher. `candidate_profile` is whichever side has actual
    skills (the applicant, or the candidate in recruiter mode); `target_profile`
    is whichever side has requirements (the job, or — for recruiter->candidate
    scored against a job — the same job). Roles never need a second function."""

    coverage, matched, missing = _skill_coverage(candidate_profile, target_profile)

    semantic_score = 0.0
    semantic_explanation = {"skipped": True}
    if use_semantic and missing and skill_name_lookup:
        missing_ids = [m["skill_id"] for m in missing]
        semantic_score, semantic_explanation = semantic_mod.semantic_component(
            candidate_profile, target_profile, skill_name_lookup, missing_ids
        )

    experience = _experience_fit(candidate_profile, target_profile)
    education = _education_fit(candidate_profile, target_profile)
    location = _location_fit(candidate_profile, target_profile)

    raw_components = {
        "skill_coverage": coverage,
        "semantic": semantic_score,
        "experience": experience,
        "education": education,
        "location": location,
    }

    # Renormalize: drop components with no data (None), redistribute their
    # weight proportionally across the remaining components.
    available = {k: v for k, v in raw_components.items() if v is not None}
    weight_sum = sum(MATCH_WEIGHTS[k] for k in available)
    weights_used = {k: (MATCH_WEIGHTS[k] / weight_sum if weight_sum else 0.0) for k in available}

    score = sum(available[k] * weights_used[k] for k in available)

    return MatchResult(
        score=round(score, 4),
        components={k: (round(v, 4) if v is not None else None) for k, v in raw_components.items()},
        weights_used={k: round(v, 4) for k, v in weights_used.items()},
        matched_skills=matched,
        missing_skills=missing,
        explanation={
            "formula_baseline": "0.60*skill_coverage + 0.20*semantic + 0.10*experience + 0.05*education + 0.05*location",
            "renormalized_because_missing": [k for k in raw_components if raw_components[k] is None],
            "semantic": semantic_explanation,
        },
    )
