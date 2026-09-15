"""
Task 07 — Shortlist top-N ranking.

Reuses the SAME match() output from matching.py — no separate recruiter
scoring model. When two candidates tie on `score` (rounded), we break the
tie deterministically and in this fixed order so re-running on identical
data always reproduces the same ranking (required by the testing
checklist: "critical outputs are deterministic when the seeded demo data
is used"):
    1. required-skill coverage (skill_coverage component, descending)
    2. experience fit (descending)
    3. candidate_id (ascending) — final deterministic tie-break
"""
from dataclasses import dataclass

from app.core.matching import MatchResult


@dataclass
class RankedCandidate:
    candidate_id: str
    rank: int
    match_result: MatchResult


def rank_shortlist(candidate_matches: list[tuple[str, MatchResult]], top_n: int | None = None) -> list[RankedCandidate]:
    def sort_key(item):
        candidate_id, m = item
        return (
            -round(m.score, 4),
            -round(m.components.get("skill_coverage") or 0.0, 4),
            -round(m.components.get("experience") or 0.0, 4),
            candidate_id,
        )

    ordered = sorted(candidate_matches, key=sort_key)
    if top_n is not None:
        ordered = ordered[:top_n]

    return [
        RankedCandidate(candidate_id=cid, rank=i + 1, match_result=m)
        for i, (cid, m) in enumerate(ordered)
    ]
