from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from app.core.gap import (
    MissingSkill,
    MatchedSkill,
    analyze_gap,
)
from app.core.matcher import MatchResult, match_candidate_job
from app.core.representations import SkillProfile, SkillProfileSkill
from app.models.job import Job


@dataclass(frozen=True)
class WhatIfResult:
    baseline_match: MatchResult
    hypothetical_match: MatchResult
    baseline_gaps: list[MissingSkill]
    hypothetical_gaps: list[MissingSkill]
    baseline_matched: list[MatchedSkill]
    hypothetical_matched: list[MatchedSkill]
    added_skills: list[str]
    match_score_change: float
    gap_count_change: int
    warnings: list[str]


def _copy_candidate(
    candidate: SkillProfile,
    skills: Sequence[SkillProfileSkill],
) -> SkillProfile:
    return SkillProfile(
        subject_id=candidate.subject_id,
        subject_type=candidate.subject_type,
        taxonomy_version=candidate.taxonomy_version,
        skills=tuple(skills),
        location=candidate.location,
        education=candidate.education,
        experience_years=candidate.experience_years,
    )


def career_what_if(
    candidate: SkillProfile,
    job: Job,
    added_skills: Mapping[str, SkillProfileSkill],
) -> WhatIfResult:
    """
    Compare current and hypothetical candidate states.

    Existing matching and gap-analysis functions are reused.
    No additional ML model is introduced.
    """
    required_skills = tuple(
        (
            job_skill.skill_id,
            float(job_skill.role_importance),
        )
        for job_skill in job.job_skills
        if job_skill.skill_id
    )

    baseline_matched, baseline_gaps, baseline_warnings = analyze_gap(
        candidate=candidate,
        required_skills=required_skills,
        district_id=None,
        sector=None,
    )

    baseline_match = match_candidate_job(
        candidate,
        job,
    )

    existing_skills = {
        skill.skill_id: skill
        for skill in candidate.skills
    }

    for skill_id, skill in sorted(added_skills.items()):
        existing_skills[skill_id] = skill

    hypothetical = _copy_candidate(
        candidate,
        [
            existing_skills[skill_id]
            for skill_id in sorted(existing_skills)
        ],
    )

    hypothetical_matched, hypothetical_gaps, hypothetical_warnings = analyze_gap(
        candidate=hypothetical,
        required_skills=required_skills,
        district_id=None,
        sector=None,
    )

    hypothetical_match = match_candidate_job(
        hypothetical,
        job,
    )

    return WhatIfResult(
        baseline_match=baseline_match,
        hypothetical_match=hypothetical_match,
        baseline_gaps=baseline_gaps,
        hypothetical_gaps=hypothetical_gaps,
        baseline_matched=baseline_matched,
        hypothetical_matched=hypothetical_matched,
        added_skills=sorted(added_skills),
        match_score_change=(
            hypothetical_match.final_score
            - baseline_match.final_score
        ),
        gap_count_change=(
            len(hypothetical_gaps)
            - len(baseline_gaps)
        ),
        warnings=sorted(
            set(baseline_warnings + hypothetical_warnings)
        ),
    )