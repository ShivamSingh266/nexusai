from app.core import representations as reps
from app.core.matching import match

from tests.conftest import CAND, JOB, SKILL_PY, SKILL_DL


def test_skill_coverage_is_importance_weighted(db):
    candidate = reps.candidate_profile(db, CAND)
    target = reps.job_target_profile(db, JOB)
    # use_semantic=False: keep this test hermetic/offline (no model download)
    result = match(candidate, target, use_semantic=False)

    # Candidate covers Python (importance 0.9) but not ML (1.0) or DL (0.8).
    # coverage = 0.9 / (0.9+1.0+0.8) = 0.3333...
    assert abs(result.components["skill_coverage"] - (0.9 / 2.7)) < 1e-4


def test_missing_optional_components_are_renormalized(db):
    """Candidate profile has no experience_years/education_level set, so
    those two components must drop out and the remaining weights (skill
    coverage, semantic, location) must renormalize to sum to 1.0."""
    candidate = reps.candidate_profile(db, CAND)  # experience_years=None
    target = reps.job_target_profile(db, JOB)     # job.exp=2, so target HAS experience
    result = match(candidate, target, use_semantic=False)

    # experience_fit needs BOTH sides; candidate side is None -> dropped
    assert "experience" not in result.weights_used
    assert abs(sum(result.weights_used.values()) - 1.0) < 1e-6


def test_missing_skill_shows_up_in_missing_list(db):
    candidate = reps.candidate_profile(db, CAND)
    target = reps.job_target_profile(db, JOB)
    result = match(candidate, target, use_semantic=False)
    missing_ids = {m["skill_id"] for m in result.missing_skills}
    assert SKILL_DL in missing_ids
    assert SKILL_PY not in missing_ids
