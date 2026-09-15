"""
T6 - Demand Aggregation, CORRECTED to split current vs anticipated demand.

Why: jobs.csv's posting_time_type (T5 fix) separates real posting-age rows
('past') from forward-looking hiring-intent rows ('future_start'). Mixing
them into one posted_date/period would contaminate month-bucketing and
recent_growth. This script keeps them as two metrics end to end.

Input:
  jobs.csv               (T5, corrected) - active, Maharashtra-mapped rows
  job_skill_resolved.csv (T6 prereq) - job_id -> skill_id, full coverage

Output:
  skill_demand_history.csv
  demand_strength_summary.txt
"""

import os
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
PROCESSED = ROOT / "data" / "processed"

jobs = pd.read_csv(PROCESSED / "jobs.csv")
mentions = pd.read_csv(PROCESSED / "job_skill_resolved.csv")
mentions["job_id"] = mentions["job_id"].astype(str)
mentions = mentions.drop_duplicates(subset=["job_id", "skill_id"])  # posting_count = postings, not raw mentions

mh_active = jobs[(jobs["status"] == "active") & (~jobs["district"].isin(["OUT_OF_SCOPE", "UNMAPPED"]))].copy()
mh_active["job_id"] = mh_active["id"].astype(str)

# ---------------------------------------------------------------------------
# STEP 1 - split current ('past', bucketed by ACTUAL posting month) vs
# anticipated ('future_start', bucketed by ANTICIPATED START month, i.e. the
# start of its window - the earliest point the hiring intent applies to)
# ---------------------------------------------------------------------------

past = mh_active[mh_active["posting_time_type"] == "past"].copy()
past["period"] = pd.to_datetime(past["posted_date"]).dt.strftime("%Y-%m")

future = mh_active[mh_active["posting_time_type"] == "future_start"].copy()
future["period"] = pd.to_datetime(future["anticipated_start_min"]).dt.strftime("%Y-%m")

print(f"Maharashtra active postings: {len(mh_active)} total | "
      f"{len(past)} 'past' (real posting-age) | {len(future)} 'future_start' (hiring intent)")

# ---------------------------------------------------------------------------
# STEP 2 - JOIN each side with resolved skills, independently
# ---------------------------------------------------------------------------

past_joined = mentions.merge(past[["job_id", "district", "sector", "period"]], on="job_id", how="inner")
future_joined = mentions.merge(future[["job_id", "district", "sector", "period"]], on="job_id", how="inner")

print(f"Current-demand join: {len(past_joined)} (job,skill,district,sector,month) rows "
      f"from {past_joined['job_id'].nunique()} distinct jobs")
print(f"Anticipated-demand join: {len(future_joined)} (job,skill,district,sector,month) rows "
      f"from {future_joined['job_id'].nunique()} distinct jobs")

# ---------------------------------------------------------------------------
# STEP 3 - AGGREGATE each side, keep separate bucket sizes (STRENGTH TIER
# per metric - a current_demand row and an anticipated_demand row for the
# same skill/district/sector/period do NOT share a confidence tier)
# ---------------------------------------------------------------------------

current_agg = (
    past_joined.groupby(["skill_id", "district", "sector", "period"])
    .agg(current_demand_count=("job_id", "nunique")).reset_index()
)
current_bucket = (
    past.groupby(["district", "sector", "period"])["job_id"].nunique()
    .reset_index(name="current_sample_size")
)
current_agg = current_agg.merge(current_bucket, on=["district", "sector", "period"], how="left")

anticipated_agg = (
    future_joined.groupby(["skill_id", "district", "sector", "period"])
    .agg(anticipated_demand_count=("job_id", "nunique")).reset_index()
)
anticipated_bucket = (
    future.groupby(["district", "sector", "period"])["job_id"].nunique()
    .reset_index(name="anticipated_sample_size")
)
anticipated_agg = anticipated_agg.merge(anticipated_bucket, on=["district", "sector", "period"], how="left")

# ---------------------------------------------------------------------------
# STEP 4 - combine. In THIS dataset current periods (2025-09) and
# anticipated periods (2025-10, 2025-12) never overlap, so a given output
# row is driven by exactly one side - but the merge is written to handle the
# general case where they do overlap in future data pulls.
# ---------------------------------------------------------------------------

combined = current_agg.merge(
    anticipated_agg, on=["skill_id", "district", "sector", "period"], how="outer"
)
combined["current_demand_count"] = combined["current_demand_count"].fillna(0).astype(int)
combined["anticipated_demand_count"] = combined["anticipated_demand_count"].fillna(0).astype(int)

# demand_score is derived from current_demand only (per spec) - share of
# CURRENT postings in this district+sector+month bucket mentioning the
# skill. Same method/reasoning as the original T6 design (see prior
# version's comments): robust to N, interpretable at any bucket size.
# Rows with no current_sample_size (pure-anticipated rows) get a null score,
# not a fabricated 0/0 - the skill just has no *current* signal to score.
combined["demand_score"] = (combined["current_demand_count"] / combined["current_sample_size"]).round(4)

# sample_size / strength_tier: use whichever side actually produced this
# row's data. Since the two sides don't overlap in period here, this is
# unambiguous; where they would overlap, current_demand's bucket takes
# precedence (it's the "live" number this pipeline's other consumers
# expect strength_tier to describe first).
combined["sample_size"] = combined["current_sample_size"].where(
    combined["current_sample_size"].notna(), combined["anticipated_sample_size"]
).fillna(0).astype(int)


def strength_tier(n):
    if n >= 100:
        return "HIGH"
    if n >= 30:
        return "MEDIUM"
    if n >= 10:
        return "LOW"
    return "INSUFFICIENT"


combined["strength_tier"] = combined["sample_size"].apply(strength_tier)

# ---------------------------------------------------------------------------
# recent_growth - unchanged mechanics, computed on current_demand_count only
# (anticipated_demand has no "growth" concept yet - one snapshot of intent,
# not a time series). Kept nullable/optional per spec, NOT a headline metric.
# ---------------------------------------------------------------------------

combined = combined.sort_values(["skill_id", "district", "sector", "period"])
grp = combined.groupby(["skill_id", "district", "sector"])
n_periods_for_key = grp["period"].transform("nunique")
prior = grp["current_demand_count"].shift(1)
combined["recent_growth"] = ((combined["current_demand_count"] - prior) / prior).round(4)
combined.loc[n_periods_for_key < 2, "recent_growth"] = pd.NA
# also null where there's no current demand at all this period (growth of
# nothing isn't meaningful, even if the key has other periods)
combined.loc[combined["current_demand_count"] == 0, "recent_growth"] = pd.NA

n_current_periods = past["period"].nunique()
n_anticipated_periods = future["period"].nunique()
print(f"\nDistinct CURRENT (posting) months: {n_current_periods} ({sorted(past['period'].unique())})")
print(f"Distinct ANTICIPATED (start) months: {n_anticipated_periods} ({sorted(future['period'].unique())})")
print(f"recent_growth non-null rows: {combined['recent_growth'].notna().sum()} / {len(combined)}")
print("Answer to 'is the date spread wide enough now': NO - even with future-start noise removed,")
print("the remaining 'past' posting dates still span only 11 days, all inside a single calendar")
print("month (2025-09). recent_growth is mechanically null for every row here, same conclusion as")
print("before the fix - the fix corrected WHAT gets called a 'posting date', it didn't create")
print("history that doesn't exist. demand_score + strength_tier remain the entire current-demand")
print("story; anticipated_demand_count is a new, separate, small but real story on its own.")

combined["source"] = "naukri:indian-job-market-dataset-2025"
combined = combined.rename(columns={"district": "district_id"})

final_cols = ["skill_id", "district_id", "sector", "period", "current_demand_count",
              "anticipated_demand_count", "demand_score", "strength_tier", "sample_size",
              "recent_growth", "source"]
out = combined[final_cols].sort_values(
    ["district_id", "sector", "period", "current_demand_count", "anticipated_demand_count"],
    ascending=[True, True, True, False, False],
)
out.to_csv(PROCESSED / "skill_demand_history.csv", index=False)
print(f"\nWrote {len(out)} rows -> skill_demand_history.csv")

# ---------------------------------------------------------------------------
# SUMMARY REPORT
# ---------------------------------------------------------------------------

lines = []
def log(s=""):
    print(s)
    lines.append(s)

log("\n=== STRENGTH TIER SUMMARY (skill x sector x month rows, by district) ===")
pivot = out.pivot_table(index="district_id", columns="strength_tier", values="skill_id",
                         aggfunc="count", fill_value=0)
for col in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]:
    if col not in pivot.columns:
        pivot[col] = 0
pivot = pivot[["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]]
pivot["TOTAL"] = pivot.sum(axis=1)
pivot = pivot.sort_values("TOTAL", ascending=False)
log(pivot.to_string())

log("\n=== OVERALL ===")
overall = out["strength_tier"].value_counts()
for tier in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]:
    n = int(overall.get(tier, 0))
    log(f"  {tier}: {n} rows ({n/len(out)*100:.1f}%)")

log("\n=== ANTICIPATED DEMAND (forward-looking hiring intent - new in this correction) ===")
anticipated_only = out[out["anticipated_demand_count"] > 0]
log(f"  {len(anticipated_only)} skill x district x sector x month rows carry any anticipated_demand_count "
    f"(from {future['job_id'].nunique()} anticipated-start MH postings total)")
by_district = anticipated_only.groupby("district_id")["anticipated_demand_count"].sum().sort_values(ascending=False)
log("\n  anticipated_demand_count summed by district:")
log(by_district.to_string())
by_sector = anticipated_only.groupby("sector")["anticipated_demand_count"].sum().sort_values(ascending=False)
log("\n  anticipated_demand_count summed by sector:")
log(by_sector.to_string())
log(f"\n  strength_tier of these rows: {anticipated_only['strength_tier'].value_counts().to_dict()} "
    f"- expected to be almost entirely INSUFFICIENT given only {len(future)} anticipated-start postings "
    f"exist in the whole MH IT/Software dataset. Real, non-zero signal - just don't overstate its confidence.")

(PROCESSED / "demand_strength_summary.txt").write_text("\n".join(lines))
print("\nWrote demand_strength_summary.txt")
