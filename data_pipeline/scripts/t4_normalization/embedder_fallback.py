"""
T4 - Skill Normalization: dependency-free-ish fallback embedder (sklearn
is already installed; no network, no model download).

Uses TF-IDF over CHARACTER n-grams (not words), cosine similarity - this is
a real, established technique for exactly this problem (fuzzy string
matching a messy user-typed value against a controlled vocabulary), not a
toy stand-in. It's what actually produced every number in this task's
chat reply, since sentence-transformers/torch can't be installed and
huggingface.co is blocked in this sandbox (see embedder_sentence_transformers.py
header).

KNOWN LIMITATION vs. real sentence embeddings, stated plainly: character
n-gram similarity catches SPELLING/TOKEN variants ("Mongo DB-3.2" close to
"MongoDB") but has NO semantic understanding - it will NOT connect "ML" to
"machine learning" or "IC" to "integrated circuit", because those pairs
share almost no characters. Sentence-transformers embeddings (once
installed in your real environment) would catch some of these; this
fallback structurally cannot. Treat this backend's UNKNOWN_SKILL numbers
as an UPPER BOUND on what real embeddings would leave unresolved, not an
exact prediction - semantic matching should do somewhat better on
abbreviation-style misses, but won't close the gap driven by taxonomy
vocabulary size (see the item-4 answer in chat).
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TfidfFallbackEmbedder:
    def __init__(self, skills_csv: Path, aliases_csv: Path):
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
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, lowercase=True)
        self.vocab_matrix = self.vectorizer.fit_transform(phrases)

    def __call__(self, queries: list[str]):
        if not queries:
            return []
        q_matrix = self.vectorizer.transform(queries)
        sims = cosine_similarity(q_matrix, self.vocab_matrix)
        best_idx = sims.argmax(axis=1)
        best_scores = sims[np.arange(len(queries)), best_idx]
        best_skill_ids = self.skill_ids[best_idx]
        return list(zip(best_skill_ids, best_scores))
