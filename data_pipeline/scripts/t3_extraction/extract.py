"""
T3 - Skill Extraction: ties parsing.py + a matcher backend together into
the record schema.

Output record schema (per spec):
    {source_type, source_id, mention_text, skill_id_candidate, start_char, end_char}

Two additions beyond the spec, both flagged rather than silently added:
  - raw_start_char / raw_end_char: without these, "evidence spans" only
    point into normalized_text, which nothing downstream of T3 ever sees -
    they wouldn't actually be usable as evidence against the source
    document. Included so a UI could highlight the exact original text.
  - skill_id_candidate is never actually null in this implementation -
    every match came from a known phrase pattern tied to a specific
    skill_id, so there's no "found something, don't know what" case here.
    The null case would only arise if this pipeline were extended with an
    open-vocabulary step (e.g. generic noun-phrase capture for candidate
    NEW skills not yet in skills.csv) - out of scope for what was asked,
    flagging so the schema's nullability isn't mistaken for "implemented".
"""

from dataclasses import asdict, dataclass
from typing import Callable, Optional

from parsing import ParsedDocument, map_span_to_raw


@dataclass
class MentionRecord:
    source_type: str
    source_id: str
    mention_text: str
    skill_id_candidate: Optional[str]
    start_char: int
    end_char: int
    raw_start_char: Optional[int]
    raw_end_char: Optional[int]


def extract_from_document(doc: ParsedDocument, find_matches_fn: Callable) -> list[MentionRecord]:
    """
    find_matches_fn(text) -> list of (start_char, end_char, skill_id, mention_text),
    matching either matcher_spacy.find_matches or matcher_fallback's
    FallbackPhraseMatcher.find_matches signature.
    """
    matches = find_matches_fn(doc.normalized_text)
    records = []
    for start_char, end_char, skill_id, mention_text in matches:
        raw_start, raw_end = map_span_to_raw(doc.offset_map, start_char, end_char)
        records.append(MentionRecord(
            source_type=doc.source_type,
            source_id=doc.source_id,
            mention_text=mention_text,
            skill_id_candidate=skill_id,
            start_char=start_char,
            end_char=end_char,
            raw_start_char=raw_start,
            raw_end_char=raw_end,
        ))
    return records


def records_to_dicts(records: list[MentionRecord]) -> list[dict]:
    return [asdict(r) for r in records]
