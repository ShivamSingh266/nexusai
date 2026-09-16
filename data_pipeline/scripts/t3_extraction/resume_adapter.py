"""
M3 <-> M4 resume extraction adapter.

This is the ONE entry point M3's backend should call. It composes the
existing T3 (extract.py, parsing.py, matcher_fallback.py/matcher_spacy.py)
and T4 (normalize.py, embedder_fallback.py/embedder_sentence_transformers.py)
modules — no new NLP logic — but fixes two real gaps found when writing
this contract against the actual code:

  1. ResolvedMention (normalize.py) does NOT carry raw_start_char/
     raw_end_char forward from MentionRecord — it only keeps the
     normalized-text offsets. Those are useless to a UI trying to
     highlight the original uploaded document. This adapter re-attaches
     them by keeping the source MentionRecord alongside its resolution.
  2. Neither MentionRecord nor ResolvedMention carries taxonomy_version
     or an extractor/pipeline version. Both are added here at the
     batch level (one value for the whole call — see CONTRACT doc
     section 4 for why per-skill doesn't make sense).

Usage (call once at process startup, reuse across requests):

    engine = ExtractionEngine.load(
        skills_csv=PROCESSED / "skills.csv",
        aliases_csv=PROCESSED / "skill_aliases.csv",
        taxonomy_version="v1.2.1",
    )

    results = engine.extract_skills_from_resume(
        resume_id="12345",
        file_path=Path("/tmp/uploaded_resume.pdf"),
    )
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from parsing import parse_file, parse_document
from patterns import load_phrase_to_skill
from matcher_fallback import FallbackPhraseMatcher
from extract import extract_from_document

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "t4_normalization"))
from normalize import build_exact_index, build_alias_index, resolve_mentions  # noqa: E402
from embedder_fallback import TfidfFallbackEmbedder  # noqa: E402

class ResumeExtractionError(Exception):
    """Base class for every application-level error this module raises.
    NEVER raise a raw pypdf/python-docx/OS exception across this module's
    boundary — catch it internally and re-raise as one of the subclasses
    below instead, so the API layer always gets a stable, documented shape.

    `code` is a class attribute (not per-instance) precisely so it can't
    drift between call sites — it is the one thing the frontend is meant
    to switch on, and it will NOT change across future revisions of this
    module without a version bump being called out explicitly. `message`
    is safe to show a user. `detail` is for your own logs only — it may
    contain the original library exception text and should never reach
    the frontend.
    """
    code: str = "RESUME_EXTRACTION_FAILED"

    def __init__(self, message: str, *, resume_id: Optional[str] = None, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.resume_id = resume_id
        self.detail = detail

    def to_response(self) -> dict:
        """What the API layer should serialize back to the client.
        Deliberately excludes `detail` — log that separately server-side."""
        return {"error_code": self.code, "message": self.message, "resume_id": self.resume_id}


class UnsupportedFileTypeError(ResumeExtractionError):
    """File extension isn't one this module will attempt to parse.
    Raised BEFORE any parsing is attempted."""
    code = "RESUME_UNSUPPORTED_FILE_TYPE"


class ResumeParseFailedError(ResumeExtractionError):
    """The file has a supported extension but the underlying parser
    (pypdf / python-docx) could not read it — corrupt file, password-
    protected PDF, truncated upload, etc. The original exception is
    preserved in `.detail` for your logs, never in `.message`."""
    code = "RESUME_PARSE_FAILED"


class NoExtractableTextError(ResumeExtractionError):
    """Parsing succeeded (no exception) but produced no usable text at
    all — e.g. a scanned/image-only PDF with nothing for pypdf to
    extract. Distinct from "parsed fine, zero skills mentioned": that
    case returns an empty list normally (see CONTRACT section 6) and is
    NOT an error. This one means the document itself was unreadable as
    text, so a caller should tell the user to re-upload a text-based
    file rather than reporting "0 skills found"."""
    code = "RESUME_NO_EXTRACTABLE_TEXT"


SUPPORTED_RESUME_EXTENSIONS = {".pdf", ".docx", ".txt"}

EXTRACTOR_VERSION = "t3-fallback+t4-tfidf-fallback@1"
# Bump this string any time the matcher backend (spaCy vs fallback), the
# embedder backend (sentence-transformers vs TF-IDF fallback), or the
# similarity threshold changes. It is NOT the taxonomy_version — this
# identifies the CODE/MODEL, taxonomy_version identifies the DATA.
# Current value reflects what's actually wired in t3_run_extraction.py /
# t4_run_normalization.py today (spaCy and sentence-transformers are the
# intended production backends per matcher_spacy.py / embedder_sentence_
# transformers.py, but neither installs in this sandbox — see their file
# headers). Whoever swaps in the production backends should rename this.

RESOLUTION_THRESHOLD = 0.65  # must match t4_run_normalization.py's THRESHOLD


@dataclass
class ExtractedSkillResult:
    """The one row shape M3 persists into ApplicantSkill (after filtering
    out UNKNOWN_SKILL — see should_persist())."""
    skill_id: str                    # "SKILL_XXXX" or literal "UNKNOWN_SKILL"
    canonical_name: Optional[str]    # None when skill_id == "UNKNOWN_SKILL"
    taxonomy_version: str            # one value for the whole extraction call
    matched_via: str                 # "exact" | "alias" | "embedding" | "unresolved"
    confidence: float                # 1.0 exact, alias's stored confidence, or embedding similarity score
    mention_text: str                # verbatim text as it appeared in the resume (original casing)
    raw_start_char: Optional[int]    # offset into the ORIGINAL resume text (None if unmappable)
    raw_end_char: Optional[int]
    extractor_version: str           # code/model identity — see EXTRACTOR_VERSION comment above

    @property
    def is_unknown(self) -> bool:
        return self.skill_id == "UNKNOWN_SKILL"

    def should_persist_as_applicant_skill(self) -> bool:
        """False for UNKNOWN_SKILL rows — canonical_skills.skill_id has a
        DB-level CHECK (skill_id ~ '^SKILL_[0-9]{4}$'), so writing
        "UNKNOWN_SKILL" there would violate the constraint, not just be
        semantically wrong."""
        return not self.is_unknown


class ExtractionEngine:
    """Holds the loaded taxonomy + fitted matcher/embedder so per-request
    calls don't reload skills.csv or refit TF-IDF every time. Build ONE
    instance at app startup; extract_skills_from_resume() is safe to call
    repeatedly against it."""

    def __init__(self, matcher: FallbackPhraseMatcher, embedder: TfidfFallbackEmbedder,
                 exact_index: dict, alias_index: dict, canonical_names: dict,
                 taxonomy_version: str):
        self._matcher = matcher
        self._embedder = embedder
        self._exact_index = exact_index
        self._alias_index = alias_index
        self._canonical_names = canonical_names  # skill_id -> canonical_name
        self.taxonomy_version = taxonomy_version

    @classmethod
    def load(cls, skills_csv: Path, aliases_csv: Path, taxonomy_version: str) -> "ExtractionEngine":
        skills_df = pd.read_csv(skills_csv)
        aliases_df = pd.read_csv(aliases_csv)

        found_versions = set(skills_df["taxonomy_version"].dropna().unique())
        if found_versions and found_versions != {taxonomy_version}:
            raise ValueError(
                f"taxonomy_version mismatch: caller expects {taxonomy_version!r}, "
                f"{skills_csv} actually contains {sorted(found_versions)}. "
                f"Refusing to load — see CONTRACT section 4 (taxonomy mismatch handling)."
            )

        phrase_to_skill = load_phrase_to_skill(skills_csv, aliases_csv)
        matcher = FallbackPhraseMatcher(phrase_to_skill)
        embedder = TfidfFallbackEmbedder(skills_csv, aliases_csv)
        exact_index = build_exact_index(skills_df)
        alias_index = build_alias_index(aliases_df)
        canonical_names = dict(zip(skills_df["skill_id"], skills_df["canonical_name"]))

        return cls(matcher, embedder, exact_index, alias_index, canonical_names, taxonomy_version)

    def extract_skills_from_resume(self, resume_id: str, file_path: Path) -> list[ExtractedSkillResult]:
        """Raises one of the ResumeExtractionError subclasses above on
        failure — never a raw pypdf/python-docx/OS exception. M3's caller
        catches ResumeExtractionError, calls .to_response() for the
        client payload, and logs .detail server-side. This function does
        not know about HTTP; mapping error_code -> status code is the
        API layer's job (e.g. all three codes above -> 422 is a
        reasonable default, but that's your call, not this module's)."""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_RESUME_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported resume file type {suffix!r}. Supported: "
                f"{', '.join(sorted(SUPPORTED_RESUME_EXTENSIONS))}.",
                resume_id=resume_id,
            )

        try:
            doc = parse_file("resume", resume_id, file_path)
        except Exception as exc:
            raise ResumeParseFailedError(
                "Could not read this resume file. It may be corrupted, "
                "password-protected, or truncated.",
                resume_id=resume_id, detail=repr(exc),
            ) from exc

        if not doc.normalized_text or not doc.normalized_text.strip():
            raise NoExtractableTextError(
                "No readable text was found in this resume (it may be a "
                "scanned image with no text layer). Please upload a "
                "text-based file.",
                resume_id=resume_id,
            )

        mentions = extract_from_document(doc, self._matcher.find_matches)

        resolve_input = [{"source_type": m.source_type, "source_id": m.source_id,
                           "mention_text": m.mention_text,
                           "start_char": m.start_char, "end_char": m.end_char} for m in mentions]
        resolved = resolve_mentions(resolve_input, self._exact_index, self._alias_index,
                                     self._embedder, RESOLUTION_THRESHOLD)

        # Re-attach raw_start_char/raw_end_char by position — resolve_mentions()
        # preserves input order and never drops/reorders rows (1 mention in,
        # 1 resolution out), so zipping by index is safe here.
        results = []
        for mention, res in zip(mentions, resolved):
            results.append(ExtractedSkillResult(
                skill_id=res.skill_id,
                canonical_name=self._canonical_names.get(res.skill_id),
                taxonomy_version=self.taxonomy_version,
                matched_via=res.matched_via,
                confidence=res.confidence,
                mention_text=res.mention_text,
                raw_start_char=mention.raw_start_char,
                raw_end_char=mention.raw_end_char,
                extractor_version=EXTRACTOR_VERSION,
            ))
        return results

    def resolve_free_typed_skill(self, source_id: str, raw_skill_text: str) -> ExtractedSkillResult:
        """For a SINGLE already-isolated skill string (e.g. an applicant
        free-typing a skill into a profile field) — NOT for resume
        documents. This is the only path that can actually reach
        matched_via='embedding' or 'unresolved'/UNKNOWN_SKILL.

        Why: extract_skills_from_resume/_text run text through T3's
        closed-vocabulary PhraseMatcher first, which can only ever emit a
        mention that's already an exact skills.csv/skill_aliases.csv
        phrase — so anything that reaches T4 from that path is guaranteed
        to hit 'exact' or 'alias' and T4's embedding step is structurally
        unreachable (confirmed against t4_run_normalization.py's own
        docstring and reproduced below). A free-typed string has no such
        guarantee, so it goes straight to T4's resolve_mentions(),
        skipping T3 entirely — this is the same path t4_run_normalization.py
        exercises against 06_skills.csv, which is where the real
        embedding/UNKNOWN_SKILL rates come from."""
        resolve_input = [{"source_type": "resume_free_text", "source_id": source_id,
                           "mention_text": raw_skill_text, "start_char": 0, "end_char": len(raw_skill_text)}]
        resolved = resolve_mentions(resolve_input, self._exact_index, self._alias_index,
                                     self._embedder, RESOLUTION_THRESHOLD)[0]
        return ExtractedSkillResult(
            skill_id=resolved.skill_id,
            canonical_name=self._canonical_names.get(resolved.skill_id),
            taxonomy_version=self.taxonomy_version,
            matched_via=resolved.matched_via,
            confidence=resolved.confidence,
            mention_text=resolved.mention_text,
            raw_start_char=0,
            raw_end_char=len(raw_skill_text),
            extractor_version=EXTRACTOR_VERSION,
        )

    def extract_skills_from_text(self, source_id: str, text: str) -> list[ExtractedSkillResult]:
        """Same as extract_skills_from_resume but for already-extracted
        plain text (e.g. a resume field already stored as text, no file
        re-parse needed)."""
        doc = parse_document("resume", source_id, text)
        mentions = extract_from_document(doc, self._matcher.find_matches)
        resolve_input = [{"source_type": m.source_type, "source_id": m.source_id,
                           "mention_text": m.mention_text,
                           "start_char": m.start_char, "end_char": m.end_char} for m in mentions]
        resolved = resolve_mentions(resolve_input, self._exact_index, self._alias_index,
                                     self._embedder, RESOLUTION_THRESHOLD)
        results = []
        for mention, res in zip(mentions, resolved):
            results.append(ExtractedSkillResult(
                skill_id=res.skill_id,
                canonical_name=self._canonical_names.get(res.skill_id),
                taxonomy_version=self.taxonomy_version,
                matched_via=res.matched_via,
                confidence=res.confidence,
                mention_text=res.mention_text,
                raw_start_char=mention.raw_start_char,
                raw_end_char=mention.raw_end_char,
                extractor_version=EXTRACTOR_VERSION,
            ))
        return results
