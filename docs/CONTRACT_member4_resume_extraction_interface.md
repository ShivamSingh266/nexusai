# M4 → M3 resume extraction: exact interface

Backend-consumption reference for `data_pipeline/scripts/t3_extraction/resume_adapter.py`.
This is the precise contract to code against — narrative rationale is in
`CONTRACT_member4_resume_extraction.md`; this doc is just the shapes and
behavior. All examples below are real output from running the actual code,
not hand-written samples.

## Setup (once per process, not per request)

```python
from pathlib import Path
from resume_adapter import ExtractionEngine

engine = ExtractionEngine.load(
    skills_csv=Path("data/processed/skills.csv"),
    aliases_csv=Path("data/processed/skill_aliases.csv"),
    taxonomy_version="v1.2.1",
)
```

**Raises `ValueError` immediately** if `taxonomy_version` doesn't match what's actually in `skills_csv`. Treat this as a startup fatal error, not a per-request condition — do not catch-and-continue.

---

## Entry point 1 — resume documents

```python
engine.extract_skills_from_resume(resume_id: str, file_path: Path) -> list[ExtractedSkillResult]
engine.extract_skills_from_text(source_id: str, text: str) -> list[ExtractedSkillResult]
```

**Input**

| field | type | required | notes |
|---|---|---|---|
| `resume_id` / `source_id` | `str` | yes | Opaque tag, not validated or looked up. Put your applicant/resume PK here. |
| `file_path` | `Path` | yes (for `extract_skills_from_resume`) | `.pdf`, `.docx` handled explicitly; anything else is read as plain text — no validation, no rejection. |
| `text` | `str` | yes (for `extract_skills_from_text`) | Use if you've already extracted text yourself. |

**Output**: `list[ExtractedSkillResult]` — zero or more rows, one per detected skill mention. Empty list is a normal, valid result (no skills found), not an error.

**Real example** — input text `"Experienced in Python, SQL, and Cybersecurity. Familiar with Data Mining and Cloud computing."`:

```json
[
  {
    "skill_id": "SKILL_0400",
    "canonical_name": "Python (computer programming)",
    "taxonomy_version": "v1.2.1",
    "matched_via": "alias",
    "confidence": 1.0,
    "mention_text": "Python",
    "raw_start_char": 15,
    "raw_end_char": 21,
    "extractor_version": "t3-fallback+t4-tfidf-fallback@1"
  },
  {
    "skill_id": "SKILL_0031",
    "canonical_name": "cyber security",
    "taxonomy_version": "v1.2.1",
    "matched_via": "alias",
    "confidence": 1.0,
    "mention_text": "Cybersecurity",
    "raw_start_char": 32,
    "raw_end_char": 45,
    "extractor_version": "t3-fallback+t4-tfidf-fallback@1"
  },
  {
    "skill_id": "SKILL_0180",
    "canonical_name": "data mining",
    "taxonomy_version": "v1.2.1",
    "matched_via": "exact",
    "confidence": 1.0,
    "mention_text": "Data Mining",
    "raw_start_char": 61,
    "raw_end_char": 72,
    "extractor_version": "t3-fallback+t4-tfidf-fallback@1"
  },
  {
    "skill_id": "SKILL_0431",
    "canonical_name": "cloud technologies",
    "taxonomy_version": "v1.2.1",
    "matched_via": "alias",
    "confidence": 1.0,
    "mention_text": "Cloud computing",
    "raw_start_char": 77,
    "raw_end_char": 92,
    "extractor_version": "t3-fallback+t4-tfidf-fallback@1"
  }
]
```

**Note the missing "SQL"**: it was in the input text but produces no row at all — not a miss, a deliberate policy. `"SQL"` is one of 33 phrases in the current taxonomy that maps to more than one `skill_id` (ambiguous between `SKILL_0149` and `SKILL_0446`); ambiguous phrases are dropped from matching entirely rather than guessed. This is silent at the API level — no row, no error, no warning in the output (only a console `[WARN]` at engine-load time listing all 33). If you want visibility into this at the per-request level, tell me and I'll add a way to surface it.

**On this path, `matched_via` will practically always be `"exact"` or `"alias"`, and `skill_id` will practically never be `"UNKNOWN_SKILL"`** — see the note in the main contract doc for why (T3's closed-vocabulary matcher can't hand T4 anything that isn't already a taxonomy phrase). Don't build UI/logic on this path expecting to see unresolved rows regularly.

---

## Entry point 2 — a single free-typed skill string

```python
engine.resolve_free_typed_skill(source_id: str, raw_skill_text: str) -> ExtractedSkillResult
```

Use this for a profile "add a skill" field or similar — **not** for resume documents (use entry point 1 for those). This is the only path that meaningfully exercises `matched_via == "embedding"` and produces real `UNKNOWN_SKILL` results.

**Input**

| field | type | required |
|---|---|---|
| `source_id` | `str` | yes — opaque tag |
| `raw_skill_text` | `str` | yes — the exact string the user typed |

**Output**: single `ExtractedSkillResult` (not a list).

**Real examples:**

```json
{
  "skill_id": "UNKNOWN_SKILL",
  "canonical_name": null,
  "taxonomy_version": "v1.2.1",
  "matched_via": "unresolved",
  "confidence": 0.34530290224399807,
  "mention_text": "MongoDB",
  "raw_start_char": 0,
  "raw_end_char": 7,
  "extractor_version": "t3-fallback+t4-tfidf-fallback@1"
}
```

```json
{
  "skill_id": "SKILL_0400",
  "canonical_name": "Python (computer programming)",
  "taxonomy_version": "v1.2.1",
  "matched_via": "alias",
  "confidence": 1.0,
  "mention_text": "Python",
  "raw_start_char": 0,
  "raw_end_char": 6,
  "extractor_version": "t3-fallback+t4-tfidf-fallback@1"
}
```

---

## `ExtractedSkillResult` — field-by-field

| field | type | nullable | meaning |
|---|---|---|---|
| `skill_id` | `str` | no | `"SKILL_XXXX"` (matches your DB's `CHECK` constraint format) or the literal string `"UNKNOWN_SKILL"`. Never `null`, never any other sentinel. |
| `canonical_name` | `str` | **yes** — `null` iff `skill_id == "UNKNOWN_SKILL"` | Otherwise always populated, sourced from `skills.csv` at load time. |
| `taxonomy_version` | `str` | no | Same value for every result from one `ExtractionEngine` instance. Matches `skills.csv`'s own `taxonomy_version` column (checked at load time). |
| `matched_via` | `str` (enum) | no | Exactly one of `"exact"`, `"alias"`, `"embedding"`, `"unresolved"`. No other values possible. |
| `confidence` | `float` | no | `1.0` for `exact`; the alias's stored confidence (typically 0.90–1.0) for `alias`; the raw similarity score for `embedding`/`unresolved` (can be any value in `[0, 1)` below the 0.65 threshold for `unresolved`). Always populated, including for `unresolved` — that's deliberate, so you can see how close the nearest candidate was. |
| `mention_text` | `str` | no | Verbatim substring as it appeared in the source (original casing, not lowercased). |
| `raw_start_char` / `raw_end_char` | `int` | **yes** — `null` if the offset couldn't be mapped back to the original text | Character offsets into the original document/string you supplied. Use for evidence highlighting. |
| `extractor_version` | `str` | no | Identifies the matcher+embedder backend combination. Currently `"t3-fallback+t4-tfidf-fallback@1"` — **this string changes if the backend changes** (e.g. switching to spaCy + sentence-transformers). Store it per row so historical extractions remain attributable to the code that produced them. |

**Persistence gate — use this, don't reimplement the check:**

```python
if result.should_persist_as_applicant_skill():   # False iff skill_id == "UNKNOWN_SKILL"
    # write ApplicantSkill(skill_id=result.skill_id, taxonomy_version=result.taxonomy_version, ...)
```

---

## Error/UNKNOWN_SKILL behavior — summary table

| Condition | What happens | What you should do |
|---|---|---|
| No skills found in text | Returns `[]` (entry point 1) | Treat as success, zero skills. Not an error. |
| Skill resolved normally | `skill_id` = real `SKILL_XXXX`, `matched_via` in `{exact, alias, embedding}` | Persist it. |
| Skill unresolved | `skill_id == "UNKNOWN_SKILL"`, `matched_via == "unresolved"` | **Do not persist as `ApplicantSkill.skill_id`** — would violate your DB `CHECK` constraint. Optionally log/store elsewhere (e.g. an audit table) for taxonomy-gap tracking. |
| Taxonomy version mismatch | `ValueError` raised at `ExtractionEngine.load()` | Fatal at startup — fix the data sync, don't catch per-request. |
| Unsupported file extension | Raises `UnsupportedFileTypeError` (`error_code: "RESUME_UNSUPPORTED_FILE_TYPE"`) — checked BEFORE any parsing is attempted | Map to a 4xx. Extension allowlist is `.pdf`, `.docx`, `.txt`. |
| Corrupt/unreadable file (bad PDF stream, non-zip/corrupt DOCX, password-protected, truncated upload) | Raises `ResumeParseFailedError` (`error_code: "RESUME_PARSE_FAILED"`) — the original `pypdf`/`python-docx` exception is caught internally and never reaches you; it's preserved in `.detail` for server-side logs only | Map to a 4xx. Show the user `.message`, log `.detail`, never expose `.detail` to the client. |
| File parses but has no extractable text (e.g. scanned/image-only PDF with no text layer) | Raises `NoExtractableTextError` (`error_code: "RESUME_NO_EXTRACTABLE_TEXT"`) | Distinct from "0 skills found" — tell the user to re-upload a text-based file, don't report an empty skill list. |

**Error contract details** — all three are subclasses of `ResumeExtractionError`, importable from `resume_adapter`:

```python
from resume_adapter import (
    ResumeExtractionError,       # base class — catch this if you want one handler for all three
    UnsupportedFileTypeError,    # error_code = "RESUME_UNSUPPORTED_FILE_TYPE"
    ResumeParseFailedError,      # error_code = "RESUME_PARSE_FAILED"
    NoExtractableTextError,      # error_code = "RESUME_NO_EXTRACTABLE_TEXT"
)

try:
    results = engine.extract_skills_from_resume(resume_id, file_path)
except ResumeExtractionError as e:
    return JSONResponse(status_code=422, content=e.to_response())
    # e.to_response() == {"error_code": "...", "message": "...", "resume_id": "..."}
    # e.detail (NOT included in to_response()) — log this server-side, never send to the client
```

`error_code` values are stable across future revisions of this module — safe for the frontend to switch on. Verified against real failure cases: a garbage-bytes `.pdf`, a garbage-bytes `.docx`, an unsupported extension, and a validly-parsed-but-empty `.docx`, all producing the correct code with the original library exception fully contained server-side.

Raw `pypdf`/`python-docx` exceptions never cross this module's boundary anymore — this replaces the "you must wrap it yourself" gap noted in the first version of this doc.

---

## Open items I need from you (not blocking, but affects `extractor_version`/dependency wiring later)

1. Which embedder backend you'll deploy (TF-IDF fallback, currently wired, vs. sentence-transformers) — once you confirm, I'll retag `extractor_version` accordingly so it's never ambiguous which backend produced a given row.
2. Whether you want a real exception type for malformed files, or the current "wrap it yourself" behavior is fine for your error-handling style.
