from app.core.matching import MatchResult
from app.core.shortlist import rank_shortlist


def _mr(score, coverage, experience):
    return MatchResult(
        score=score,
        components={"skill_coverage": coverage, "semantic": 0.0, "experience": experience,
                    "education": None, "location": None},
        weights_used={}, matched_skills=[], missing_skills=[], explanation={},
    )


def test_tie_broken_by_skill_coverage_then_experience_then_id(db=None):
    matches = [
        ("cand-b", _mr(0.70, 0.60, 0.50)),
        ("cand-a", _mr(0.70, 0.60, 0.50)),  # identical to cand-b -> id tiebreak
        ("cand-c", _mr(0.70, 0.80, 0.10)),  # higher coverage should win despite lower experience
    ]
    ranked = rank_shortlist(matches)
    ordered_ids = [r.candidate_id for r in ranked]

    assert ordered_ids[0] == "cand-c"       # coverage wins first
    assert ordered_ids[1:] == ["cand-a", "cand-b"]  # then deterministic id order
    assert [r.rank for r in ranked] == [1, 2, 3]
