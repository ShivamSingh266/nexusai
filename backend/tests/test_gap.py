from app.core import representations as reps
from app.core.gap import analyze_gap

from tests.conftest import CAND, ROLE, SKILL_PY, SKILL_ML, SKILL_DL


def test_met_skill_produces_no_gap(db):
    """Explicit overlap first: candidate already clears Python's bar, so it
    must never appear in the gap list, regardless of demand/trend."""
    candidate = reps.candidate_profile(db, CAND)
    target = reps.role_target_profile(db, ROLE)
    gaps = analyze_gap(db, candidate, target)
    gap_skill_ids = {g.skill_id for g in gaps}
    assert SKILL_PY not in gap_skill_ids


def test_high_demand_trend_raises_priority(db):
    candidate = reps.candidate_profile(db, CAND)
    target = reps.role_target_profile(db, ROLE)
    gaps = {g.skill_id: g for g in analyze_gap(db, candidate, target, district_id="Pune", sector="tech")}

    # Deep Learning has demand=0.9, trend=1.3 seeded; ML Fundamentals has
    # neutral defaults (no demand/forecast rows). Deep Learning's severity
    # (0.6, candidate has none) should out-rank ML's smaller severity (0.3)
    # once demand/trend multiply through.
    assert gaps[SKILL_DL].priority > gaps[SKILL_ML].priority


def test_candidate_with_no_skills_at_all_is_negative_case(db):
    """Negative case: candidate_id that has no candidate_skills rows at all.
    Must not error — every target skill becomes a full gap."""
    candidate = reps.candidate_profile(db, "cand-does-not-exist")
    target = reps.role_target_profile(db, ROLE)
    gaps = analyze_gap(db, candidate, target)
    assert len(gaps) == len(target.skills)
    for g in gaps:
        assert g.explanation["candidate_proficiency"] == 0.0
