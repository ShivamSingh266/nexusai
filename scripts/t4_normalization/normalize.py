"""
T4 - Skill Normalization: the 3-step decision chain.

exact match -> alias match -> embedding similarity (only for what survives
both). Backend-agnostic: takes an `embed_fn` callable, so the same chain
runs against sentence-transformers OR the dependency-free fallback without
duplicating this logic (same reasoning as T3's matcher_spacy/matcher_fallback
split).

embed_fn signature: embed_fn(list[str]) -> list[(skill_id, similarity_score)]
  one (best-matching skill_id, its score) per input string, in order.
"""

import re
from dataclasses import asdict, dataclass
from typing import Callable, Optional

import pandas as pd


def normalize_text(s) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


def build_exact_index(skills_df: pd.DataFrame) -> dict:
    idx = {}
    for row in skills_df.itertuples(index=False):
        idx[normalize_text(row.canonical_name)] = row.skill_id
    return idx


def build_alias_index(aliases_df: pd.DataFrame) -> dict:
    has_confidence = "confidence" in aliases_df.columns
    idx = {}
    for row in aliases_df.itertuples(index=False):
        conf = getattr(row, "confidence", None) if has_confidence else None
        conf = 0.9 if conf is None or pd.isna(conf) else float(conf)
        idx[normalize_text(row.alias)] = (row.skill_id, conf)
    return idx


@dataclass
class ResolvedMention:
    skill_id: str
    source_type: str
    source_id: str
    mention_text: str
    matched_via: str        # exact | alias | embedding | unresolved
    confidence: float
    start_char: Optional[int]
    end_char: Optional[int]


def resolve_mentions(
    mentions: list[dict],          # each: {source_type, source_id, mention_text, start_char, end_char}
    exact_index: dict,
    alias_index: dict,
    embed_fn: Callable,
    threshold: float,
) -> list[ResolvedMention]:
    resolved = []
    pending = []  # mentions that survive steps 1-2, need embedding

    for m in mentions:
        norm = normalize_text(m["mention_text"])

        if norm in exact_index:
            resolved.append(ResolvedMention(
                skill_id=exact_index[norm], source_type=m["source_type"], source_id=m["source_id"],
                mention_text=m["mention_text"], matched_via="exact", confidence=1.0,
                start_char=m.get("start_char"), end_char=m.get("end_char"),
            ))
            continue

        if norm in alias_index:
            skill_id, conf = alias_index[norm]
            resolved.append(ResolvedMention(
                skill_id=skill_id, source_type=m["source_type"], source_id=m["source_id"],
                mention_text=m["mention_text"], matched_via="alias", confidence=conf,
                start_char=m.get("start_char"), end_char=m.get("end_char"),
            ))
            continue

        pending.append(m)

    if pending:
        queries = [normalize_text(m["mention_text"]) for m in pending]
        embed_results = embed_fn(queries)  # list of (skill_id, score), same order
        for m, (best_skill_id, score) in zip(pending, embed_results):
            score = float(score)
            if score >= threshold:
                resolved.append(ResolvedMention(
                    skill_id=best_skill_id, source_type=m["source_type"], source_id=m["source_id"],
                    mention_text=m["mention_text"], matched_via="embedding", confidence=score,
                    start_char=m.get("start_char"), end_char=m.get("end_char"),
                ))
            else:
                # UNKNOWN_SKILL rows are NOT dropped - score is kept (even
                # though it's below threshold) so a reviewer can see how
                # close the nearest candidate was, not just that it failed.
                resolved.append(ResolvedMention(
                    skill_id="UNKNOWN_SKILL", source_type=m["source_type"], source_id=m["source_id"],
                    mention_text=m["mention_text"], matched_via="unresolved", confidence=score,
                    start_char=m.get("start_char"), end_char=m.get("end_char"),
                ))

    return resolved


def resolved_to_df(resolved: list[ResolvedMention]) -> pd.DataFrame:
    cols = ["skill_id", "source_type", "source_id", "mention_text", "matched_via",
            "confidence", "start_char", "end_char"]
    return pd.DataFrame([asdict(r) for r in resolved])[cols]
