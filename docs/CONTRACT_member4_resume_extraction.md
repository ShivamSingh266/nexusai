# Data contract: Member 4 → Member 3 (resume → skill extraction)

Everything below is grounded in the actual code at
`data_pipeline/scripts/t3_extraction/` and `t4_normalization/` — verified
by running it, not inferred from the docstrings alone. Two real gaps in
that code were found while writing this contract and are fixed in a new
file this delivers: `data_pipeline/scripts/t3_extraction/resume_adapter.py`.
That file is the actual interface to call — everything else in T3/T4 is
internal implementation.

## 0. The one function you call

```python
from pathlib import Path
from resume_adapter import ExtractionEngine

# Once, at process startup — loading skills.csv/aliases.csv and fitting
# the matcher/embedder is not cheap, do not do this per-request.
engine = ExtractionEngine.load(
    skills_csv=Path("data/processed/skills.csv"),
    aliases_csv=Path("data/processed/skill_aliases.csv"),
    taxonomy_version="v1.2.1",
)

# Per resume upload:
results = engine.extract_skills_from_resume(resume_id="12345", file_path=Path("/tmp/resume.pdf"))

# Per free-typed skill field (NOT a resume document — see section 3):
result = engine.resolve_free_typed_skill(source_id="applicant_42_skill_1", raw_skill_text="MongoDB")
```

Both return `ExtractedSkillResult` (single instance from the second call,
a list from the first).

## 1. Extraction input

| What M3 provides | Required | Notes |
|---|---|---|
| `resume_id` | yes | Any string. Used only as an opaque tag on output rows (`source_id`) — not looked up or validated by M4's code. |
| file path (or bytes saved to a temp path) | yes, for `extract_skills_from_resume` | `.pdf`, `.docx`, or anything else (treated as plain text — see section 6, this is a real gap, not a feature). |
| raw text directly | alternative to file path | Use `extract_skills_from_text(source_id, text)` if you've already extracted text from the resume yourself (e.g. you already run PDF text extraction for display purposes and don't want to do it twice). |
| `applicant_id` | no | Not consumed by extraction at all — that's a persistence-layer concern on your side. Attach it when you write `ApplicantSkill` rows; extraction doesn't need it. |
| `taxonomy_version` | yes, once at startup | Passed to `ExtractionEngine.load()`, not per-call. See section 4 for why. |
| source identifier | yes | This is `resume_id`/`source_id` above — no separate field. |

## 2. Extraction output — `ExtractedSkillResult`

```python
@dataclass
class ExtractedSkillResult:
    skill_id: str                    # "SKILL_XXXX" or literal "UNKNOWN_SKILL"
    canonical_name: Optional[str]    # None when skill_id == "UNKNOWN_SKILL"
    taxonomy_version: str            # one value for the whole call, e.g. "v1.2.1"
    matched_via: str                 # "exact" | "alias" | "embedding" | "unresolved"
    confidence: float                # 1.0 for exact; alias's stored confidence (usually 0.90–1.0); embedding similarity score
    mention_text: str                # verbatim text as it appeared in the resume (original casing preserved)
    raw_start_char: Optional[int]    # character offset into the ORIGINAL resume text/file content
    raw_end_char: Optional[int]
    extractor_version: str           # code/model identity tag — see section 7
```

Answering your specific list:
- **confidence**: yes, always populated (never null) — see the table above for what it means per `matched_via`.
- **proficiency_level**: **no.** Not computed anywhere in T3/T4. These modules detect that a skill was *mentioned*, not how proficient the person is. If you need this, it's a separate feature to build (possibly NLP-adjacent — e.g. detecting "expert in" / "familiar with" qualifiers near a mention — but nothing today does this).
- **years_experience**: **no**, same reason. Not extracted.
- **evidence/span**: yes — `raw_start_char`/`raw_end_char` index into the original resume text. (Gap fixed for this contract: the underlying `ResolvedMention` dataclass in `normalize.py` drops these fields; `resume_adapter.py` re-attaches them from the paired `MentionRecord`.)
- **matched_via**: yes, one of exactly 4 string literals — `"exact"`, `"alias"`, `"embedding"`, `"unresolved"`.
- **extractor/pipeline version**: yes — added for this contract (`extractor_version`, see section 7). Did not exist in the code before.

## 3. UNKNOWN / unresolved skills

Represented as `skill_id == "UNKNOWN_SKILL"` (a literal string, never `None`/`null`) with `matched_via == "unresolved"` and `confidence` set to the similarity score that fell short of the threshold (kept, not discarded, so you can see how close it came).

**Confirmed: unresolved skills must NOT be persisted as `ApplicantSkill.skill_id`.** `should_persist_as_applicant_skill()` on the result object returns `False` for these — use it as your gate before writing. This isn't just a convention: `canonical_skills.skill_id` has a DB-level `CHECK (skill_id ~ '^SKILL_[0-9]{4}$')` constraint, so attempting to persist `"UNKNOWN_SKILL"` there would fail the insert outright, not just be semantically wrong.

**Important behavioral note, verified by running it:** `extract_skills_from_resume`/`extract_skills_from_text` will almost never produce `UNKNOWN_SKILL` in practice. Resume text goes through T3's closed-vocabulary phrase matcher first, which can only emit a mention that's already an exact `skills.csv`/`skill_aliases.csv` phrase — so by construction, everything reaching T4 from that path resolves via `"exact"` or `"alias"`, and T4's embedding/unresolved step is structurally unreachable there. `UNKNOWN_SKILL` only becomes real when you call `resolve_free_typed_skill()` on an already-isolated string that bypasses T3 (e.g. an applicant free-typing "MongoDB" into a profile skill field, as opposed to a skill parsed out of an uploaded resume). Tested just now against the real taxonomy:

```
'MongoDB'                     -> UNKNOWN_SKILL   (unresolved, confidence 0.345)
'Kubernetes'                  -> UNKNOWN_SKILL   (unresolved, confidence 0.337)
'Python'                      -> SKILL_0400      (alias, confidence 1.000)
```

MongoDB/Kubernetes come back unknown because the current 642-skill IT/Software taxonomy (ESCO-derived) genuinely doesn't cover those specific tools — that's a taxonomy coverage gap, not a bug, and it's exactly the kind of case `UNKNOWN_SKILL` exists to surface rather than silently mismatch.

## 4. Taxonomy

**One `taxonomy_version` per whole extraction result, not per skill.** The matcher and embedder are both built once from a specific `skills.csv`/`skill_aliases.csv` snapshot — every skill returned in a given call necessarily comes from that same snapshot, so per-skill versioning would be meaningless (they're always identical within one call).

**Mismatch handling**: `ExtractionEngine.load()` reads the `taxonomy_version` column out of `skills.csv` itself and compares it against the version you pass in. If they don't match, it raises `ValueError` immediately and refuses to build the engine — it will not silently extract against the wrong taxonomy. Verified:

```
ValueError: taxonomy_version mismatch: caller expects 'v9.9.9', skills.csv
actually contains ['v1.2.1']. Refusing to load.
```

Treat this as a startup-time check, not a per-request one — if your DB's `canonical_skills.taxonomy_version` ever diverges from the CSV `ExtractionEngine` is pointed at, that's a deploy-time data sync problem to fix, not something to catch per-resume.

## 5. Execution boundary

**In-process Python callable.** Not a separate service/API, not a CLI/subprocess. `ExtractionEngine` is a plain Python object — import it directly into your FastAPI process, build one instance at app startup (in whatever your app's equivalent of a startup hook is), and call its methods synchronously per request.

Rationale: the underlying models (a fitted TF-IDF vectorizer, or a loaded sentence-transformers model in the production backend — see section 8) are expensive to build/load but cheap to query once built. Standing up a separate microservice for this adds a network hop and a second deployment for no benefit at this scale (642 skills, single-digit-KB requests). Reconsider only if resume volume gets large enough that extraction becomes a CPU bottleneck on your API process — not a concern at hackathon/pilot scale.

## 6. Error contract

Honest answer: **today, error handling is minimal — this is a real gap, not a hidden feature.**

| Case | Actual current behavior |
|---|---|
| Invalid/unsupported resume file | `parse_file()` only branches on `.pdf`/`.docx` — anything else (including a genuinely corrupt file with a `.txt`-like extension) is read as plain text via `path.read_text(errors="ignore")`, which **will not raise** even on garbage input; it just extracts garbage. A truly malformed `.pdf`/`.docx` **can** raise from `pypdf`/`python-docx` internals — uncaught. **You must wrap calls to `extract_skills_from_resume()` in your own try/except** and decide the HTTP response (e.g. 422) yourself. |
| Extraction failure (matcher/embedder internals) | No known failure modes hit in testing, but nothing in `resume_adapter.py` catches exceptions from the matcher or embedder — same rule: wrap the call site. |
| Taxonomy mismatch | Raises `ValueError` at `ExtractionEngine.load()` time (see section 4) — this one **is** handled, deliberately, as a startup-time hard stop. |
| No skills found | Returns an empty list. This is a normal, valid outcome — not an error. Don't treat it as a failure case. |
| Unknown skills | Returned as rows with `skill_id="UNKNOWN_SKILL"` — not an error, a normal (if low-confidence) result. Filter with `should_persist_as_applicant_skill()`. |

If you want stronger error handling (specific exception types instead of raw `pypdf`/`python-docx` exceptions, a validated-file-type allowlist instead of silent plain-text fallback), tell me which behavior you want and I'll add it — I didn't want to guess your API's error-response shape.

## 7. Determinism/versioning

- **Deterministic given fixed inputs.** Same file + same taxonomy snapshot + same matcher/embedder backend + same threshold → same output, every time. No randomness anywhere in the matching or resolution logic.
- **NOT deterministic across backend swaps.** The fallback matcher (regex-based, currently wired) and the intended production matcher (spaCy `PhraseMatcher`) can tokenize edge cases differently (documented gap in `matcher_fallback.py`: contractions, punctuation-adjacent tokens). Bigger effect: the fallback embedder (TF-IDF character n-grams) and the intended production embedder (`sentence-transformers`, `all-MiniLM-L6-v2`) will give **different** `embedding`-matched results and different `UNKNOWN_SKILL` rates for the same input — TF-IDF catches spelling variants only, sentence-transformers catches semantic ones too (e.g. "ML" → "machine learning"). Whichever is deployed, don't mix them across environments and expect identical results.
- **`extractor_version`** is a new field (didn't exist before this contract) that tags every result with a string identifying which matcher+embedder backend combination produced it — currently `"t3-fallback+t4-tfidf-fallback@1"`. **Whoever swaps in the production backends (spaCy + sentence-transformers) needs to bump this string.** Store it alongside each `ApplicantSkill` row so you can tell which extraction run produced which data if the backend changes later.
- **Repeated extraction of the same resume produces equivalent results** as long as `extractor_version` and `taxonomy_version` are both unchanged. If either changes, expect (and don't be alarmed by) different results — that's the versioning working as intended, not corruption.

## 8. Dependencies

**Currently wired (what's actually running today):**
- `pypdf`, `python-docx`, `beautifulsoup4` — file parsing (T3)
- `pandas`, `numpy`, `scikit-learn` — matching/normalization (T3 fallback matcher, T4 fallback embedder)
- No network calls, no model downloads. Runs fully offline.

**Intended production backends (written, present in the repo, NOT currently exercised — see file headers in `matcher_spacy.py` / `embedder_sentence_transformers.py` for why):**
- `spacy` (no model download needed — rule-based `PhraseMatcher`, not a trained pipeline)
- `sentence-transformers` + `torch`, which downloads `all-MiniLM-L6-v2` from huggingface.co on first use

**Question back to you**: can your backend's runtime environment reach `huggingface.co`, and are you OK with `torch` as a dependency (larger install, slower cold start)? If not, the fallback (TF-IDF) backend already wired is a legitimate, tested option — just with the semantic-matching limitation in section 7. I don't know your deployment constraints, so I'm not picking this for you — tell me which one and I'll make sure `resume_adapter.py` is wired to it before you build against it.

**Runtime requirement either way**: whichever embedder you use, `ExtractionEngine.load()` must run once per process lifetime (app startup), not per-request — refitting a TF-IDF vectorizer or reloading a transformer model on every resume upload would be a serious performance problem.

## What ships with this contract

- `data_pipeline/scripts/t3_extraction/resume_adapter.py` — the actual interface described above, composing the existing T3/T4 modules with no new NLP logic, tested against the real taxonomy (`skills.csv`/`skill_aliases.csv`) end to end including the taxonomy-mismatch guard and the UNKNOWN_SKILL path.
