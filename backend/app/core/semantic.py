from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


_TOKEN_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Normalize text into deterministic lowercase tokens."""
    return _TOKEN_RE.findall(text.lower())


def _term_frequency(tokens: Iterable[str]) -> Counter[str]:
    counts = Counter(tokens)
    total = sum(counts.values())

    if total == 0:
        return Counter()

    return Counter(
    	{
        	token: count / total
        	for token, count in counts.items()
    	}
	)

def cosine_similarity(left: str, right: str) -> float:
    """
    Deterministic lexical semantic-similarity baseline.

    Returns a value in [0, 1].
    """
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)

    if not left_tokens or not right_tokens:
        return 0.0

    left_tf = _term_frequency(left_tokens)
    right_tf = _term_frequency(right_tokens)

    vocabulary = set(left_tf) | set(right_tf)

    dot = sum(left_tf[token] * right_tf[token] for token in vocabulary)
    left_norm = math.sqrt(sum(value * value for value in left_tf.values()))
    right_norm = math.sqrt(sum(value * value for value in right_tf.values()))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def skill_text_similarity(
    candidate_text: str,
    target_text: str,
) -> float:
    """
    Public semantic-similarity contract used by the matching engine.

    Kept separate from cosine_similarity so a future embedding implementation
    can replace the internal method without changing callers.
    """
    return cosine_similarity(candidate_text, target_text)