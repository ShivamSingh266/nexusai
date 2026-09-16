"""
T6 prerequisite - NOT part of the original T3 deliverable, added because T6
can't be built without it. See the chat reply for why.

T3's original t3_run_extraction.py ran on a 300-job RANDOM SAMPLE pulled
straight from the raw xlsx (all industries, pre-T5). That was fine for
demonstrating the extractor. It is not fine as T6's join input: checked
against jobs.csv (T5's output), only 72 of those 300 sampled jobs survived
into the IT/Software set at all, and only 9 landed in a real Maharashtra
district. 9 jobs cannot support a skill x district x sector x month
aggregation.

Fix: re-run the SAME extraction + normalization logic (unchanged - same
matcher, same phrase list, same 3-step resolution chain) over every ACTIVE
row in jobs.csv (17,651 rows, all districts) instead of a 300-row sample.
Title + description text, same as before.

Output: job_skill_resolved.csv - job_id, skill_id, matched_via, confidence
(one row per resolved skill mention per job; UNKNOWN/unresolved dropped
here since T6 only needs known-skill demand, unlike T4's own deliverable
which had to keep UNKNOWN_SKILL visible for extraction-gap review).
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "t3_extraction"))
sys.path.insert(0, str(Path(__file__).parent / "t4_normalization"))

from parsing import parse_document  # noqa: E402
from patterns import load_phrase_to_skill  # noqa: E402
from matcher_fallback import FallbackPhraseMatcher  # noqa: E402
from extract import extract_from_document, records_to_dicts  # noqa: E402
from normalize import build_exact_index, build_alias_index, resolve_mentions, resolved_to_df  # noqa: E402
from embedder_fallback import TfidfFallbackEmbedder  # noqa: E402

ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
PROCESSED = ROOT / "data" / "processed"

t0 = time.time()

jobs = pd.read_csv(PROCESSED / "jobs.csv")
active = jobs[jobs["status"] == "active"].copy()
print(f"Extracting skills from {len(active)} active jobs.csv rows (all districts)")

phrase_to_skill = load_phrase_to_skill(PROCESSED / "skills.csv", PROCESSED / "skill_aliases.csv")
matcher = FallbackPhraseMatcher(phrase_to_skill)

all_records = []
for row in active.itertuples(index=False):
    text = f"{row.title}. {row.description}" if pd.notna(row.description) else str(row.title)
    doc = parse_document("job", str(row.id), text)
    records = extract_from_document(doc, matcher.find_matches)
    all_records.extend(records_to_dicts(records))

print(f"Extraction done in {time.time()-t0:.1f}s -> {len(all_records)} raw mentions "
      f"from {active['id'].nunique()} distinct jobs")

# Normalize (same 3-step chain as T4; closed-vocabulary input so this is
# mostly exact/alias resolution, embedding step is a no-op safety net - see
# T4's chat explanation for why)
skills_df = pd.read_csv(PROCESSED / "skills.csv")
aliases_df = pd.read_csv(PROCESSED / "skill_aliases.csv")
exact_index = build_exact_index(skills_df)
alias_index = build_alias_index(aliases_df)
embedder = TfidfFallbackEmbedder(PROCESSED / "skills.csv", PROCESSED / "skill_aliases.csv")

mention_input = [{"source_type": r["source_type"], "source_id": r["source_id"],
                   "mention_text": r["mention_text"], "start_char": r["start_char"], "end_char": r["end_char"]}
                  for r in all_records]
resolved = resolve_mentions(mention_input, exact_index, alias_index, embedder, threshold=0.65)
resolved_df = resolved_to_df(resolved)

print(resolved_df["matched_via"].value_counts().to_string())

out = resolved_df[resolved_df["skill_id"] != "UNKNOWN_SKILL"][
    ["source_id", "skill_id", "matched_via", "confidence"]
].rename(columns={"source_id": "job_id"})
out.to_csv(PROCESSED / "job_skill_resolved.csv", index=False)
print(f"\nWrote {len(out)} resolved (job_id, skill_id) mention rows -> job_skill_resolved.csv")
print(f"Distinct jobs with >=1 resolved skill: {out['job_id'].nunique()} / {active['id'].nunique()} "
      f"({out['job_id'].nunique()/active['id'].nunique()*100:.1f}%)")
print(f"Total time: {time.time()-t0:.1f}s")
