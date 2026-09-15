from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.core.gap import DemandSignal, SkillGap, analyze_gap
from app.core.matcher import MatchResult, match_profiles
from app.core.representations import SkillEntry, SkillProfile


@dataclass(frozen=True)
class WhatIfResult:
    baseline_match: MatchResult
    hypothetical_match: MatchResult
    baseline_gaps: list[SkillGap]
    hypothetical_gaps: list[SkillGap]
    added_skills: list[str]
    match_score_change: float
    gap_count_change: int


def _copy_profile(profile: SkillProfile) -> SkillProfile:
    copied = SkillProfile(
        owner_id=profile.owner_id,
        kind=profile.kind,
        experience_years=profile.experience_years,
        education_level=profile.education_level,
        location=profile.location,
        work_mode=profile.work_mode,
        text=profile.text,
    )

    for skill in profile.skills.values():
        copied.add_skill(skill)

    return copied


def career_what_if(
    candidate: SkillProfile,
    target: SkillProfile,
    added_skills: Mapping[str, SkillEntry],
    demand_signals: dict[str, DemandSignal] | None = None,
) -> WhatIfResult:
    """
    Compare the candidate's current career state with a hypothetical state.

    Existing gap-analysis and matching functions are reused for both states.
    No new ML model is introduced.
    """
    baseline_gaps = analyze_gap(
        candidate,
        target,
        demand_signals,
    )

    baseline_match = match_profiles(
        candidate,
        target,
    )

    hypothetical = _copy_profile(candidate)

    for skill_id, skill_entry in sorted(added_skills.items()):
        hypothetical.add_skill(skill_entry)

    hypothetical_gaps = analyze_gap(
        hypothetical,
        target,
        demand_signals,
    )

    hypothetical_match = match_profiles(
        hypothetical,
        target,
    )

    return WhatIfResult(
        baseline_match=baseline_match,
        hypothetical_match=hypothetical_match,
        baseline_gaps=baseline_gaps,
        hypothetical_gaps=hypothetical_gaps,
        added_skills=sorted(added_skills),
        match_score_change=(
            hypothetical_match.final_score
            - baseline_match.final_score
        ),
        gap_count_change=(
            len(hypothetical_gaps)
            - len(baseline_gaps)
        ),
    )