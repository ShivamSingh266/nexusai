"""
T4 - Skill Normalization: sentence-transformers embedder (PRIMARY - use in
your real dev environment; requires `pip install sentence-transformers`,
which downloads the model from huggingface.co on first use).

NOT executed in the sandbox this was written in: sentence-transformers and
torch both fail to install (no matching distribution - same PyPI
restriction as spaCy in T3), AND huggingface.co is explicitly blocked at
the network egress policy level (403, confirmed via curl - not a proxy
hiccup, an org policy denial), so even a pre-installed copy couldn't
download the model here. This is real, correct sentence-transformers
usage - swap the import in t4_run_normalization.py once you have a normal
network. Same call interface as embedder_fallback.py's TfidfFallbackEmbedder,
so normalize.py's resolve_mentions() doesn't change either way.

MODEL CHOICE: all-MiniLM-L6-v2 is a reasonable default here and I would
NOT switch it for this vocabulary size. Reasoning, not just agreement:
  - Your vocab is small (209 skills currently, up to ~700 if you widen
    T2's scope) - encoding a few hundred short phrases takes well under a
    second even on CPU with a much bigger model, so speed is not the
    deciding factor between MiniLM-L6 and something heavier.
  - MiniLM-L6-v2 is specifically validated on STS (semantic textual
    similarity) benchmarks, which is closer to "is this mention the same
    skill as this canonical name" than a generic embedding model.
  - The real risk is domain vocabulary, not model size: skill names lean
    heavily on acronyms and rare technical tokens (AS400, SPARQL, PL/I,
    N1QL - see the alias audit from T3/T2). A general-purpose STS model's
    training data is mostly natural sentences, not tech acronyms, so THESE
    are the highest-risk category for poor embeddings - not something a
    bigger model necessarily fixes. Spend your 30-60 min validation
    budget specifically checking acronym/jargon mentions, not average
    ones - see the threshold-tuning section in the chat reply.
  - If validation shows genuinely poor separation, the natural upgrade is
    all-mpnet-base-v2 (higher quality, still fast enough at this vocab
    size) - not a smaller/faster model, since speed was never the
    bottleneck here.

IMPORTANT: raw cosine similarity from these models is not intuitively
calibrated - two unrelated short phrases often still score 0.2-0.4, not
near 0, and genuine paraphrase matches often land around 0.6-0.85, rarely
close to 1.0 unless near-identical text. Don't assume a "0.75 means 75%
confident" reading - calibrate empirically (see chat).
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


class STEmbedder:
    def __init__(self, skills_csv: Path, aliases_csv: Path, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

        skills = pd.read_csv(skills_csv)
        aliases = pd.read_csv(aliases_csv)

        phrases, skill_ids = [], []
        for _, row in skills.iterrows():
            phrases.append(str(row["canonical_name"]))
            skill_ids.append(row["skill_id"])
        for _, row in aliases.iterrows():
            phrases.append(str(row["alias"]))
            skill_ids.append(row["skill_id"])

        self.phrases = phrases
        self.skill_ids = np.array(skill_ids)
        # normalize_embeddings=True -> dot product IS cosine similarity,
        # avoids a separate normalization step at query time
        self.vocab_embeddings = self.model.encode(
            phrases, normalize_embeddings=True, show_progress_bar=False, batch_size=64
        )

    def __call__(self, queries: list[str]):
        """Returns list of (best_skill_id, best_cosine_similarity), one per query."""
        if not queries:
            return []
        q_emb = self.model.encode(queries, normalize_embeddings=True, show_progress_bar=False, batch_size=64)
        sims = q_emb @ self.vocab_embeddings.T
        best_idx = sims.argmax(axis=1)
        best_scores = sims[np.arange(len(queries)), best_idx]
        best_skill_ids = self.skill_ids[best_idx]
        return list(zip(best_skill_ids, best_scores))
