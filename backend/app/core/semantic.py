"""
Task 03 — Semantic similarity, added carefully.

Rule from Final V2: "taxonomy matches must remain authoritative." Meaning:
- If a candidate skill_id exactly equals a required skill_id (after alias
  resolution against `skills.aliases`, which is Member 4's job upstream),
  that is coverage = 1.0, full stop. No embedding ever overrides that.
- Semantic similarity ONLY kicks in for skills the candidate does NOT hold
  under any canonical id/alias, to give partial credit for adjacent skills
  (e.g. candidate has "PyTorch", job wants "Deep Learning Frameworks") —
  and it is capped, never allowed to fully substitute for a missing skill.

This keeps semantic_score an independent, smaller component of the final
match (see config.W_SEMANTIC = 0.20), rather than silently rewriting the
skill_coverage component.
"""
from functools import lru_cache

import numpy as np

from app.core.representations import SkillProfile

# Cap on how much credit an embedding-similar-but-not-canonical skill can earn.
# Prevents semantic drift from ever looking like an exact taxonomy match.
SEMANTIC_CREDIT_CAP = 0.7
SEMANTIC_MATCH_THRESHOLD = 0.55  # below this, treat as unrelated (0 credit)


@lru_cache(maxsize=1)
def _get_model():
    # Loaded lazily so unit tests that don't touch semantic scoring stay fast
    # and don't require the model weights to be present.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def _embed(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return np.array(model.encode(texts, normalize_embeddings=True))


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def semantic_component(
    candidate_profile: SkillProfile,
    target_profile: SkillProfile,
    skill_name_lookup: dict[str, str],
    missing_skill_ids: list[str],
) -> tuple[float, dict]:
    """Returns (semantic_score in 0..1, explanation dict).

    Only runs over `missing_skill_ids` — skills the taxonomy pass already
    determined the candidate does NOT canonically hold. Exact matches never
    pass through here.
    """
    if not missing_skill_ids or not candidate_profile.skills:
        return 0.0, {"note": "no missing skills or empty candidate profile"}

    candidate_ids = list(candidate_profile.skills.keys())
    candidate_names = [skill_name_lookup.get(sid, sid) for sid in candidate_ids]
    missing_names = [skill_name_lookup.get(sid, sid) for sid in missing_skill_ids]

    cand_emb = _embed(candidate_names)
    miss_emb = _embed(missing_names)

    per_skill_best = []
    for i, mid in enumerate(missing_skill_ids):
        sims = [_cosine(miss_emb[i], cand_emb[j]) for j in range(len(candidate_ids))]
        best_idx = int(np.argmax(sims)) if sims else -1
        best_sim = sims[best_idx] if sims else 0.0
        credit = 0.0
        if best_sim >= SEMANTIC_MATCH_THRESHOLD:
            credit = min(best_sim, SEMANTIC_CREDIT_CAP)
        per_skill_best.append({
            "target_skill": missing_names[i],
            "closest_candidate_skill": candidate_names[best_idx] if best_idx >= 0 else None,
            "similarity": round(best_sim, 4),
            "credit": round(credit, 4),
        })

    avg_credit = sum(x["credit"] for x in per_skill_best) / len(per_skill_best)
    return avg_credit, {"per_skill": per_skill_best, "cap": SEMANTIC_CREDIT_CAP,
                         "threshold": SEMANTIC_MATCH_THRESHOLD}
