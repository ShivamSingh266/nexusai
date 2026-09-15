"""
T4 - Skill Normalization: wiring.

Runs the 3-step chain against TWO different inputs, deliberately:
  (a) Task 3's actual mention output (t3_mentions_sample.json)
  (b) a sample of RAW, unnormalized resume skill strings (06_skills.csv)

Why both - this is not incidental, see the chat reply: T3's mentions were
extracted by a closed-vocabulary PhraseMatcher, so by construction every
one of them already IS an exact skills.csv/skill_aliases.csv phrase - step
3 (embedding) can structurally never fire on that input. Input (b) is
genuinely messy free text with no such guarantee, so it's the only one of
the two that actually exercises the embedding step and produces a
meaningful UNKNOWN_SKILL statistic.
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "t4_normalization"))
from normalize import build_exact_index, build_alias_index, resolve_mentions, resolved_to_df  # noqa: E402
from embedder_fallback import TfidfFallbackEmbedder  # noqa: E402

ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"

THRESHOLD = 0.65  # calibrated via stratified spot-check (see chat) - 0.5 let too many
# wrong matches through (e.g. "IT management assistant" -> "security engineering").
# This is the fallback (TF-IDF char-ngram) scale, NOT a sentence-transformers threshold.
N_RESUME_SAMPLE = 800

skills_df = pd.read_csv(PROCESSED / "skills.csv")
aliases_df = pd.read_csv(PROCESSED / "skill_aliases.csv")

exact_index = build_exact_index(skills_df)
alias_index = build_alias_index(aliases_df)
embedder = TfidfFallbackEmbedder(PROCESSED / "skills.csv", PROCESSED / "skill_aliases.csv")

# ---------------------------------------------------------------------------
# (a) T3's actual mentions
# ---------------------------------------------------------------------------

t3_mentions = json.loads((PROCESSED / "t3_mentions_sample.json").read_text())
t3_input = [{"source_type": m["source_type"], "source_id": m["source_id"],
             "mention_text": m["mention_text"], "start_char": m["start_char"], "end_char": m["end_char"]}
            for m in t3_mentions]

t3_resolved = resolve_mentions(t3_input, exact_index, alias_index, embedder, THRESHOLD)
t3_df = resolved_to_df(t3_resolved)

print("=== (a) T3 mentions (closed-vocabulary extraction output) ===")
print(t3_df["matched_via"].value_counts())
print()

# ---------------------------------------------------------------------------
# (b) Raw resume skill strings - the real fuzzy-matching test
# ---------------------------------------------------------------------------

skills_raw = pd.read_csv(RAW / "resumes" / "06_skills.csv")
sample = skills_raw["skill"].dropna().drop_duplicates().sample(n=N_RESUME_SAMPLE, random_state=42)

resume_input = [{"source_type": "resume_raw_skill", "source_id": f"06_skills:{i}",
                  "mention_text": s, "start_char": 0, "end_char": len(str(s))}
                 for i, s in sample.items()]

resume_resolved = resolve_mentions(resume_input, exact_index, alias_index, embedder, THRESHOLD)
resume_df = resolved_to_df(resume_resolved)

print(f"=== (b) Raw resume skill strings (06_skills.csv, n={N_RESUME_SAMPLE}) ===")
print(resume_df["matched_via"].value_counts())
print(f"UNKNOWN_SKILL rate: {(resume_df['skill_id']=='UNKNOWN_SKILL').mean()*100:.1f}%")
print()

# ---------------------------------------------------------------------------
# WRITE combined output (per spec columns)
# ---------------------------------------------------------------------------

combined = pd.concat([t3_df, resume_df], ignore_index=True)
out_path = PROCESSED / "t4_resolved_skills.csv"
combined.to_csv(out_path, index=False)
print(f"Wrote {len(combined)} resolution rows -> {out_path}")

# ---------------------------------------------------------------------------
# THRESHOLD-TUNING aid: stratified sample by score band, for manual spot-check
# (this is what you'd eyeball for real - printed here as a worked example)
# ---------------------------------------------------------------------------

pending_scored = resume_df[resume_df["matched_via"].isin(["embedding", "unresolved"])].copy()
bands = [(0.8, 1.01), (0.65, 0.8), (0.5, 0.65), (0.35, 0.5), (0.0, 0.35)]

print("\n=== Stratified sample for threshold tuning (spot-check these by hand) ===")
skill_name = skills_df.set_index("skill_id")["canonical_name"]
for lo, hi in bands:
    band_rows = pending_scored[(pending_scored["confidence"] >= lo) & (pending_scored["confidence"] < hi)]
    print(f"\n--- score [{lo:.2f}, {hi:.2f}) : {len(band_rows)} candidates in this band ---")
    for _, row in band_rows.sample(n=min(5, len(band_rows)), random_state=1).iterrows():
        matched_name = skill_name.get(row["skill_id"], row["skill_id"])
        print(f"  {row['confidence']:.3f}  {row['mention_text']!r:50s} -> {matched_name!r}")
