from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.core.matcher import MatchResult, match_candidate_job
from app.core.representations import SkillProfile
from app.models.job import Job


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: int
    match: MatchResult


def rank_candidates(
    job: Job,
    candidates: Sequence[tuple[int, SkillProfile]],
) -> list[RankedCandidate]:
    """
    Rank persisted candidates for a persisted job.

    Deterministic tie-breakers:
    1. Higher final score
    2. Higher skill coverage
    3. More matched skills
    4. Candidate ID ascending
    """
    ranked: list[RankedCandidate] = []

    for candidate_id, candidate in candidates:
        result = match_candidate_job(candidate, job)

        ranked.append(
            RankedCandidate(
                candidate_id=candidate_id,
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