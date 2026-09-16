"""
T3 - Skill Extraction: wiring against real sample records from all three
dataset types, using the fallback matcher backend (spaCy unavailable in
this sandbox - see chat / matcher_spacy.py header for the swap point).

Produces:
  - data/processed/t3_mentions_sample.json   (all extracted mention records)
  - printed volume / false-negative read per source type (Task 3 item 4)
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "t3_extraction"))
from parsing import parse_document           # noqa: E402
from patterns import load_phrase_to_skill    # noqa: E402
from matcher_fallback import FallbackPhraseMatcher  # noqa: E402
from extract import extract_from_document, records_to_dicts  # noqa: E402

# Portable root: defaults to the project folder this script lives in
# (scripts/../), so copying the whole project anywhere just works. Override
# with the NEXUSAI_ROOT env var if you keep scripts/ and data/ apart.
ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

N_RESUME_SAMPLE = 300
N_JOB_SAMPLE = 300

# ---------------------------------------------------------------------------
# Build the matcher
# ---------------------------------------------------------------------------

phrase_to_skill = load_phrase_to_skill(PROCESSED / "skills.csv", PROCESSED / "skill_aliases.csv",
                                        dropped_out=PROCESSED / "ambiguous_phrases_dropped.csv")
matcher = FallbackPhraseMatcher(phrase_to_skill)
print(f"Matcher loaded: {matcher.n_patterns} phrase patterns "
      f"(from {pd.read_csv(PROCESSED/'skills.csv').shape[0]} skills)\n")


def run_source(source_type: str, records: list[tuple[str, str]]):
    """records: list of (source_id, text). Returns (all_mentions, per_record_stats)."""
    all_mentions = []
    per_record = []
    for source_id, text in records:
        if not text or not text.strip():
            per_record.append({"source_id": source_id, "text_len": 0, "n_mentions": 0, "n_distinct_skills": 0})
            continue
        doc = parse_document(source_type, source_id, text)
        recs = extract_from_document(doc, matcher.find_matches)
        all_mentions.extend(recs)
        per_record.append({
            "source_id": source_id,
            "text_len": len(doc.normalized_text),
            "n_mentions": len(recs),
            "n_distinct_skills": len({r.skill_id_candidate for r in recs}),
        })
    return all_mentions, per_record


# ---------------------------------------------------------------------------
# 1) COURSES - all 382 rows (89 + 293 - true count, see chat: Task 1's
#    wc -l based row count of 119/341 was wrong, inflated by embedded
#    newlines inside quoted CSV fields; pandas parses correctly) - cheap
#    enough to run in full rather than sampling
# ---------------------------------------------------------------------------

course_records = []
for fname in ["NPTEL_Dep_Free_Elective.csv", "NPTEL_HS_MG.csv"]:
    df = pd.read_csv(RAW / "courses" / fname)
    for _, row in df.iterrows():
        sid = f"{fname}:{row.get('NPTEL_ID', row.name)}"
        text = f"{row.get('Course Name', '')} {row.get('SME Name', '')}"
        course_records.append((sid, text))

course_mentions, course_stats = run_source("course", course_records)

# also run Course Name ALONE (no SME Name) to isolate what the instructor
# name field is actually contributing - expectation: ~nothing, it's a
# person's name, but check rather than assume
course_title_only_records = []
for fname in ["NPTEL_Dep_Free_Elective.csv", "NPTEL_HS_MG.csv"]:
    df = pd.read_csv(RAW / "courses" / fname)
    for _, row in df.iterrows():
        sid = f"{fname}:{row.get('NPTEL_ID', row.name)}"
        course_title_only_records.append((sid, str(row.get("Course Name", ""))))
course_title_only_mentions, course_title_only_stats = run_source("course_title_only", course_title_only_records)

# ---------------------------------------------------------------------------
# 2) RESUMES - sample N people, concatenate their abilities + experience titles
#    NOTE: 04_experience.csv has NO description column (title, firm, dates,
#    location only) - flagging now, see item 4 in the chat reply.
# ---------------------------------------------------------------------------

abilities = pd.read_csv(RAW / "resumes" / "02_abilities.csv")
experience = pd.read_csv(RAW / "resumes" / "04_experience.csv")

sample_person_ids = abilities["person_id"].drop_duplicates().sample(n=N_RESUME_SAMPLE, random_state=42)

resume_records = []
ab_by_person = abilities.groupby("person_id")["ability"].apply(list)
exp_by_person = experience.groupby("person_id")["title"].apply(list)
for pid in sample_person_ids:
    parts = []
    parts.extend(str(a) for a in ab_by_person.get(pid, []))
    parts.extend(str(t) for t in exp_by_person.get(pid, []))
    resume_records.append((str(pid), ". ".join(parts)))

resume_mentions, resume_stats = run_source("resume", resume_records)

# ---------------------------------------------------------------------------
# 3) JOBS - sample N rows, tagsAndSkills + jobDescription (HTML-stripped in parse_document)
# ---------------------------------------------------------------------------

jobs_df = pd.read_excel(RAW / "jobs" / "indian-job-market-dataset-2025.xlsx",
                         usecols=["jobId", "tagsAndSkills", "jobDescription"])
jobs_sample = jobs_df.sample(n=N_JOB_SAMPLE, random_state=42)

job_records = []
for _, row in jobs_sample.iterrows():
    text = f"{row.get('tagsAndSkills', '') or ''} {row.get('jobDescription', '') or ''}"
    job_records.append((str(row["jobId"]), text))

job_mentions, job_stats = run_source("job", job_records)

# ---------------------------------------------------------------------------
# WRITE mention records
# ---------------------------------------------------------------------------

all_records = course_mentions + resume_mentions + job_mentions
out_path = PROCESSED / "t3_mentions_sample.json"
out_path.write_text(json.dumps(records_to_dicts(all_records), indent=2))
print(f"Wrote {len(all_records)} mention records -> {out_path}\n")


# ---------------------------------------------------------------------------
# ITEM 4: realistic read
# ---------------------------------------------------------------------------

def summarize(name, stats, n_skills_total):
    df = pd.DataFrame(stats)
    zero = (df["n_mentions"] == 0).mean() * 100
    covered = set()
    print(f"--- {name} (n={len(df)}) ---")
    print(f"  mentions/record: mean={df['n_mentions'].mean():.2f}  median={df['n_mentions'].median():.0f}  "
          f"max={df['n_mentions'].max()}")
    print(f"  records with ZERO mentions: {zero:.0f}%")
    print(f"  median text length (chars): {df['text_len'].median():.0f}")
    print()


n_skills = pd.read_csv(PROCESSED / "skills.csv").shape[0]

summarize("RESUME (abilities + experience titles)", resume_stats, n_skills)
summarize("JOB (tagsAndSkills + jobDescription)", job_stats, n_skills)
summarize("COURSE (Course Name + SME Name)", course_stats, n_skills)
summarize("COURSE (Course Name ONLY, no SME Name)", course_title_only_stats, n_skills)

# distinct skills covered across the whole sample, per source
for name, mentions in [("resume", resume_mentions), ("job", job_mentions), ("course", course_mentions)]:
    distinct = {m.skill_id_candidate for m in mentions}
    print(f"{name}: {len(distinct)}/{n_skills} taxonomy skills ({100*len(distinct)/n_skills:.0f}%) "
          f"seen at least once across the sample")
