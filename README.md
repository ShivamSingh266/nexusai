# NexusAI — T2-T8 Data Pipeline

Rebuilds the whole skill-taxonomy / job-demand / course-alignment pipeline
from raw sources with one command. This zip has the code only (~350KB) —
the raw datasets (~210MB, mostly the resume dataset) exceed what can be
sent through this chat, and you already have them from when you originally
sourced them for the project. Drop them into the folder structure below.

## 1. Prerequisites

- Python 3.9+
- `pip install -r requirements.txt` (pandas, numpy, scikit-learn, openpyxl)

## 2. Folder layout — drop your raw files into the placeholders

```
nexusai/
├── scripts/           t2-t8 pipeline scripts + t3_extraction/, t4_normalization/ helper modules  (included)
├── config/
│   └── taxonomy_config.json                                                                       (included)
└── data/
    ├── raw/
    │   ├── esco/       <- put the full ESCO v1.2.1 bulk-download CSVs here (18 files -
    │   │                  skills_en.csv, occupationSkillRelations_en.csv, skillsHierarchy_en.csv,
    │   │                  skillGroups_en.csv, broaderRelationsSkillPillar_en.csv, etc. - whatever
    │   │                  came in the bulk zip)
    │   ├── jobs/       <- indian-job-market-dataset-2025.xlsx (the 97,929-row Naukri dataset)
    │   ├── courses/    <- NPTEL_Dep_Free_Elective.csv, NPTEL_HS_MG.csv
    │   └── resumes/    <- 01_people.csv, 02_abilities.csv, 03_education.csv, 04_experience.csv,
    │                      05_person_skills.csv, 06_skills.csv
    └── processed/      (empty — pipeline output goes here)
```

Each `data/raw/<x>/` folder has a `PUT_FILES_HERE.txt` placeholder — delete
it once you've dropped the real files in (it doesn't hurt anything if you
forget, it's just a stray text file the pipeline ignores).

Every script auto-detects `nexusai/` as its root from its own file location
(`scripts/..`), so this whole folder runs from anywhere — Desktop, an
external drive, wherever — with zero path editing. Only set the
`NEXUSAI_ROOT` environment variable if you ever split `scripts/` and
`data/` apart from each other.

## 3. Run it

```bash
cd nexusai/scripts
python3 t8_pipeline.py --reset
```

Takes ~2 minutes. `--reset` wipes `data/processed/` first for a genuine
from-scratch rebuild (it prints a warning about skill_id renumbering — see
the caveat at the bottom of this file). Leave off `--reset` for a plain
rerun that carries existing IDs forward unchanged.

Other useful commands:
```bash
python3 t8_pipeline.py --list                       # show the 9 stages, run nothing
python3 t8_pipeline.py --from T5_job_ingestion       # resume partway through
```

## 4. Expected output

Console prints each of the 9 stages in order (`T2a_taxonomy` →
`T2b_aliases` → `T3_extraction_sample` → `T4_normalization` →
`T5_job_ingestion` → `T6prep_full_extraction` → `T6_demand_aggregation` →
`T7_course_alignment` → `T7supp_manual_courses`), each ending with an
`[OK] <stage> - <seconds>s - <output files + row counts>` line. A failure
prints `[FAIL]` and stops the pipeline immediately — no later stage runs on
top of a broken one.

Final lines look like:
```
[T8 COMPLETE] 9 stages, ~120s total
Manifest written to .../data/processed/pipeline_manifest.json (23 files fingerprinted)
```

`data/processed/` will then contain (reference numbers from this handoff —
yours should match exactly, verified deterministic and verified portable by
running this exact code from a fresh, differently-named folder):

| file | rows | what it is |
|---|---|---|
| `skills.csv` | 642 | canonical IT/Software skill taxonomy (5 sub-categories) |
| `skill_aliases.csv` | 2,887 | alias → skill_id lookup |
| `jobs.csv` | 27,824 | cleaned/deduped Naukri postings, IT/Software scope |
| `job_skill_resolved.csv` | 53,529 | job × skill mention pairs |
| `skill_demand_history.csv` | 1,130 | skill × district × sector × month demand |
| `courses.csv` | 66 | 46 NPTEL + 20 manually-sourced supplement courses |
| `course_skills.csv` | 316 | course × skill coverage pairs |
| `training_gap.csv` | 194 | HIGH/MEDIUM-demand skills, gap_flag per skill |

Plus QA/review side-files (`*_needs_review.csv`, `*_ambiguous_review.csv`,
`*_quality_report.txt`, `*_summary.txt`) and per-stage logs under
`logs/t8_run_<timestamp>/`.

Spot-check once it finishes:
```bash
cd ../data/processed
python3 -c "
import pandas as pd
g = pd.read_csv('training_gap.csv')
print(g['gap_flag'].sum(), '/', len(g), 'HIGH/MEDIUM-demand skills still gapped')
"
```
Expect `120 / 194`.

## 5. One rule to know before you run `--reset` again later

`--reset` mints a fresh `skill_id` numbering for all 642 skills from
scratch (internally consistent, but different numbers than whatever was
there before — skill_id values are not semantically meaningful, just
foreign keys). That's harmless before anyone downstream depends on
specific IDs. Once Member 3's DB (or anything else) has actually ingested
specific `skill_id` values, don't run `--reset` again — use a plain rerun
(no flag) or `--from <stage>` instead, both of which carry every existing
ID forward unchanged. The script prints a loud warning if you `--reset`
over an existing `skills.csv`, precisely so this isn't easy to do by
accident.
