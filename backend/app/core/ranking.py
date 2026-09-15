from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.core.matcher import MatchResult, match_profiles
from app.core.representations import SkillProfile


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    match: MatchResult


def rank_candidates(
    job: SkillProfile,
    candidates: Sequence[SkillProfile],
) -> list[RankedCandidate]:
    """
    Rank candidates for a job using the shared matching engine.

    Deterministic tie-breakers:
    1. Higher final match score
    2. Higher skill coverage
    3. More matched skills
    4. Candidate ID ascending
    """
    ranked: list[RankedCandidate] = []

    for candidate in candidates:
        result = match_profiles(candidate, job)

        ranked.append(
            RankedCandidate(
                candidate_id=candidate.owner_id,
                match=result,
            )
        )

    ranked.sort(
        key=lambda item: (
            -item.match.final_score,
            -item.match.explanation.skill_score,
            -len(item.match.matched_skills),
            item.candidate_id,
        )
    )

    return ranked