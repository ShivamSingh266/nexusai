"""
Task 09 — Version scoring weights and model outputs.

Every persisted row (skill_gaps.scoring_version, job_matches.scoring_version,
roadmaps.model_version) must point here so a score can always be traced back
to the exact weights/model that produced it. Bump the relevant constant
whenever weights or the embedding model change — never mutate scores in
place for old rows.
"""
from app.config import settings, MATCH_WEIGHTS

SCORING_VERSION = settings.SCORING_VERSION       # gap + match formula weights
SEMANTIC_MODEL_VERSION = "all-MiniLM-L6-v2"       # sentence-transformers model id
ROADMAP_MODEL_VERSION = f"roadmap-{SCORING_VERSION}"  # deterministic, no ML — versioned for traceability


def version_manifest() -> dict:
    """Returned by GET /api/v1/meta/versions — lets Members 1/2 and the UI
    display exactly what produced a given score."""
    return {
        "scoring_version": SCORING_VERSION,
        "semantic_model_version": SEMANTIC_MODEL_VERSION,
        "roadmap_model_version": ROADMAP_MODEL_VERSION,
        "match_weights": MATCH_WEIGHTS,
    }
