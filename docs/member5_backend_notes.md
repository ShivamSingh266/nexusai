# NexusAI · SIH26134 — Member 5 module
Gap, Matching, Roadmap & Shortlist Engine — branch `feature/gap-matching-roadmap`

Built directly against the Final V2 amendments. Every frozen formula lives in
`app/config.py` and nowhere else — if the amendments change again, that's the
only file that should need editing.

## What's implemented (maps to the 9 tasks)

| Task | File | Notes |
|---|---|---|
| 01 Representations | `app/core/representations.py` | `SkillProfile` — the one shape both applicant and job/role sides get converted into |
| 02 Gap analyzer (F3) | `app/core/gap.py` | explicit overlap first, then `demand × trend × severity × importance` |
| 03 Semantic similarity | `app/core/semantic.py` | only scores skills NOT already covered by taxonomy/alias; capped, can't fake an exact match |
| 04+05 Matcher (F4) + explainability | `app/core/matching.py` | **one** `match()` function, used both directions |
| 06 Roadmap DAG (F5) | `app/core/roadmap.py` | Kahn's algorithm; raises `RoadmapCycleError` (→ HTTP 422) instead of hanging/dropping data on a cycle |
| 07 Shortlist | `app/core/shortlist.py` | reuses `match()` output; deterministic 3-level tie-break |
| 08 Career What-If | `app/core/whatif.py` | calls `analyze_gap()` + `match()` twice, no new model |
| 09 Versioning | `app/core/versioning.py`, `app/config.py` | every persisted row carries `scoring_version` / `model_version` |

API routers in `app/api/` implement every row of the blueprint's endpoint
table (section 2) plus `POST /api/v1/whatif/evaluate` for the What-If screen
and `GET /api/v1/meta/versions` so Members 1/2 and the UI can display exactly
what produced a score.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Point at your Postgres instance (falls back to the default in config.py
# otherwise). For local dev without Postgres installed, sqlite works too:
export DATABASE_URL="postgresql://nexusai:nexusai@localhost:5432/nexusai"
# or: export DATABASE_URL="sqlite:///./dev.db"

python -m app.seed          # wipes + reloads deterministic demo data
uvicorn app.main:app --reload
```

Swagger UI: `http://localhost:8000/docs`

### One real dependency to watch: the semantic model download

`app/core/semantic.py` lazy-loads `sentence-transformers` (`all-MiniLM-L6-v2`)
on first use, not at import time — so gap analysis, roadmap generation,
and tests that don't touch semantic scoring never need it. But the first
call to a matching endpoint downloads the model from Hugging Face, which
needs outbound network access to `huggingface.co`. If your dev/CI sandbox
blocks that domain, either:
- pre-download the model once somewhere with access and point
  `SENTENCE_TRANSFORMERS_HOME` at the cache, or
- pass `use_semantic=False` when calling `match()` directly (already how
  the test suite stays hermetic).

## Tests

```bash
DATABASE_URL="sqlite:///:memory:" pytest tests/ -v
```

9 tests, all passing against an in-memory SQLite fixture DB (`tests/conftest.py`)
seeded with a small, realistic candidate/role/job/course graph. Covers:
- explicit-overlap gap suppression + demand/trend priority ordering
- a genuine negative case (candidate with zero skill rows)
- skill-coverage weighting math and optional-component renormalization
- prerequisite ordering AND a real cycle (`RoadmapCycleError`)
- deterministic shortlist tie-breaking

Still open against the blueprint's testing checklist: negative-input tests
for the API layer itself (malformed payloads), and a coverage pass once
Member 4's real taxonomy/alias data lands (right now `_skill_coverage`
assumes exact `skill_id` equality, which is correct once aliases are
resolved upstream, but untested against real alias collisions).

## API surface

```
POST /api/v1/gaps/analyze              -> ranked skill gaps + explanation
POST /api/v1/roadmaps/generate         -> ordered course/project steps (422 on prereq cycle)
POST /api/v1/matching/jobs             -> applicant -> job ranking
GET  /api/v1/jobs/{id}/candidates      -> recruiter -> candidate ranking (same match())
GET  /api/v1/jobs                      -> thin search (full CRUD lives with Member 3/6)
POST /api/v1/shortlists                -> ranked shortlist + persisted decision rows
POST /api/v1/whatif/evaluate           -> before/after score delta for a hypothetical skill set
GET  /api/v1/meta/versions             -> current scoring_version / model versions / weights
```

## Integration notes (from the blueprint's dependency list)

- **Member 4** (canonical skills + demand/trend): `representations.py` and
  `gap.py` already read from `skills`, `skill_demand_history`, and
  `skill_forecasts` — demand/trend default to neutral (`1.0`) when no row
  exists yet, so this module runs standalone until that data lands (the
  "thin vertical slice" rule).
- **Member 3** (service/API interface): routers are plain FastAPI, easy to
  mount behind whatever gateway/auth layer they own.
- **Member 6** (forecast signal): `SkillForecast.trend` is the only field
  this module reads from that table — swap in real values any time.
- **Members 1/2** (score explanations): every response includes a
  `explanation` block plus `scoring_version`; `GET /api/v1/meta/versions`
  gives the full weight manifest for UI display.

## Suggested order to keep building

1. Wire a real Postgres instance + Alembic migration from `app/models.py`
   (not included yet — straightforward `alembic init` + autogenerate once
   you confirm the schema against Member 3's actual DB).
2. Swap `Skill.aliases` resolution into `_skill_coverage()` in
   `matching.py` once Member 4 publishes the alias format — right now it's
   exact `skill_id` match only.
3. Add negative-path API tests (bad UUIDs, missing role, empty candidate).
4. Confirm `sentence-transformers` model caching in whatever CI/deploy
   environment you're using — see the note above.
