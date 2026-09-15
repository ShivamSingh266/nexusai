# Data contract: Member 4 → Member 5 (skills + demand)

Member 5's code (`backend/app/core/gap.py`, `matching.py`) reads directly
from these tables. If the shape changes, these are the two files to check.

## 1. `skills` table
| column | type | notes |
|---|---|---|
| id | string (uuid) | stable — never change once referenced |
| canonical_name | string | unique |
| category | string | |
| aliases | JSON array of strings | e.g. `["ReactJS", "React.js"]` for `"React"` |
| source | string | |
| version | string | |

**Resolve aliases before writing `candidate_skills`/`job_skills`/`role_skills`.**
Member 5's matcher does exact `skill_id` equality — it assumes every skill
reference already points at the canonical id.

## 2. `skill_demand_history`
| column | type | notes |
|---|---|---|
| skill_id | string (uuid) | FK -> skills.id |
| district_id | string | |
| sector | string | |
| period | string | e.g. `"2026-Q3"` — sortable, most recent wins |
| posting_count | int | raw count, informational |
| demand_score | float | **must be normalized 0–1** — fed directly into the gap-priority formula |

Confirm with Member 5 which normalization method you used (min-max per
sector? per district? global?) — it changes what "high priority" means
downstream.

## 3. `skill_forecasts` (Member 6, listed here since Member 4 often owns the pipeline that feeds it)
| column | type | notes |
|---|---|---|
| skill_id | string (uuid) | FK -> skills.id |
| trend | float | **multiplier**, e.g. `1.3` = growing 30%. NOT a raw score. |

If any of these tables are empty for a skill, Member 5's code defaults to
neutral (`demand=1.0`, `trend=1.0`) rather than failing — so partial data
is fine, just won't affect priority ranking until it's filled in.
