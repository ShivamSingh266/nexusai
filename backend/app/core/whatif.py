"""
Task 08 — Career What-If.

Final V2 requirement: this calls existing gap/match functions TWICE
(before/after a hypothetical skill addition) and introduces NO new ML
model. It's a pure aggregation layer over gap.py and matching.py.
"""
from dataclasses import dataclass, replace

from app.core.gap import analyze_gap, SkillGapResult
from app.core.matching import match, MatchResult
from app.core.representations import SkillProfile, SkillEntry


@dataclass
class WhatIfResult:
    baseline_match: MatchResult
    hypothetical_match: MatchResult
    baseline_gap_count: int
    hypothetical_gap_count: int
    score_delta: float
    gap_priority_removed: float
    resolved_skill_ids: list[str]


def evaluate_what_if(
    db,
    candidate_profile: SkillProfile,
    target_profile: SkillProfile,
    hypothetical_skills: dict[str, float],  # skill_id -> hypothetical proficiency
    skill_name_lookup: dict[str, str] | None = None,
    district_id: str = None,
    sector: str = None,
) -> WhatIfResult:
    """Call #1: baseline gap + match, as-is."""
    baseline_gaps = analyze_gap(db, candidate_profile, target_profile, district_id, sector)
    baseline_match_result = match(candidate_profile, target_profile, skill_name_lookup)

    """Call #2: same two functions again, against a hypothetical profile
    where the candidate has acquired `hypothetical_skills`. No new model —
    just a modified input to the existing functions."""
    hypothetical_skills_dict = dict(candidate_profile.skills)
    for skill_id, proficiency in hypothetical_skills.items():
        hypothetical_skills_dict[skill_id] = SkillEntry(skill_id=skill_id, proficiency=proficiency)
    hypothetical_profile = replace(candidate_profile, skills=hypothetical_skills_dict)

    hypothetical_gaps = analyze_gap(db, hypothetical_profile, target_profile, district_id, sector)
    hypothetical_match_result = match(hypothetical_profile, target_profile, skill_name_lookup)

    baseline_priority_by_skill = {g.skill_id: g.priority for g in baseline_gaps}
    resolved = [sid for sid in hypothetical_skills if sid in baseline_priority_by_skill
                and sid not in {g.skill_id for g in hypothetical_gaps}]
    priority_removed = sum(baseline_priority_by_skill.get(sid, 0.0) for sid in resolved)

    return WhatIfResult(
        baseline_match=baseline_match_result,
        hypothetical_match=hypothetical_match_result,
        baseline_gap_count=len(baseline_gaps),
        hypothetical_gap_count=len(hypothetical_gaps),
        score_delta=round(hypothetical_match_result.score - baseline_match_result.score, 4),
        gap_priority_removed=round(priority_removed, 4),
        resolved_skill_ids=resolved,
    )
