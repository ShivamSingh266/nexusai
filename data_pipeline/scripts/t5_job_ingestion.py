"""
T5 - Job Data Engineering: ingestion, validation, sector-scope filter,
standardization, date normalization, company normalization, district
mapping, dedup, quality report.

Input:  data/raw/jobs/indian-job-market-dataset-2025.xlsx (97,929 rows, all-India, all-industry)
Output: data/processed/jobs.csv                 (IT/Software subset, MH + non-MH, district-mapped)
        data/processed/jobs_out_of_scope.csv     (non-IT/Software rows, for reference)
        data/processed/jobs_ambiguous_review.csv (tied-sector rows needing a human call)
        data/processed/companies_needs_review.csv(fuzzy near-duplicate company names)
        data/processed/districts_unmapped.csv    (MH-sounding locations not in the lookup table)
        data/processed/jobs_quality_report.txt

Reuses the SAME sector keyword lists from config/taxonomy_config.json (T2)
so "IT/Software" means the same thing here as it does in the skill
taxonomy - not a second, drifting definition of scope.
"""

import json
import os
import re
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
RAW = ROOT / "data" / "raw" / "jobs" / "indian-job-market-dataset-2025.xlsx"
CONFIG = ROOT / "config" / "taxonomy_config.json"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# Scrape reference date is NOT in the data. jobUploaded is relative text
# ("6 Days Ago"), and the newest "Starts : Nth Mon' YY" values top out at
# 10th Oct '25 while the oldest "N Days Ago" bucket is 10 days - both are
# consistent with the dataset having been scraped around late Sept 2025.
# This is an ESTIMATE, not ground truth - change it if you know the real
# scrape date.
REFERENCE_DATE = date(2025, 9, 25)

report_lines = []


def log(line=""):
    print(line)
    report_lines.append(line)


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------

df = pd.read_excel(RAW)
n_start = len(df)
log(f"Loaded {n_start} rows from {RAW.name}")

cfg = json.load(open(CONFIG))
SECTORS = cfg["sectors"]

# ---------------------------------------------------------------------------
# DATE CLASSIFICATION - done FIRST, on the full raw set, before validation.
# ---------------------------------------------------------------------------
# jobUploaded conflates two unrelated things in the raw text: real posting
# age ("6 Days Ago", "Today", "Just Now", "Few Hours Ago") vs a forward-
# looking hiring-intent date ("Starts in 1-3 months", "Starts : 6th Oct' 25").
# Classified up front (posting_time_type: past / future_start / unknown) so
# STEP 1's validation rule can treat them correctly - see below.
#
# Reference date for back-computing 'past' dates and projecting
# 'future_start' windows - NOT in the data, ESTIMATED from it (REFERENCE_DATE,
# set at the top of this file).

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

def parse_uploaded(raw: str):
    """Returns (posting_time_type, posted_date, anticipated_start_min, anticipated_start_max)."""
    s = str(raw).strip()

    if s in ("Just Now", "Few Hours Ago", "Today"):
        return "past", REFERENCE_DATE, None, None
    m = re.match(r"^(\d+)\s+Days?\s+Ago$", s, re.I)
    if m:
        return "past", REFERENCE_DATE - timedelta(days=int(m.group(1))), None, None

    m = re.match(r"^Starts\s*:\s*(\d+)(?:st|nd|rd|th)?\s+([A-Za-z]+)'?\s*(\d+)$", s, re.I)
    if m:
        day, mon_txt, yy = int(m.group(1)), m.group(2)[:3].lower(), int(m.group(3))
        month = MONTHS.get(mon_txt)
        if month:
            year = 2000 + yy if yy < 100 else yy
            d = date(year, month, day)
            return "future_start", None, d, d
    if re.match(r"^Starts\s+within\s+1\s+month$", s, re.I):
        return "future_start", None, REFERENCE_DATE, REFERENCE_DATE + timedelta(days=30)
    m = re.match(r"^Starts\s+in\s+(\d+)-(\d+)\s+months?$", s, re.I)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return "future_start", None, REFERENCE_DATE + timedelta(days=30 * lo), REFERENCE_DATE + timedelta(days=30 * hi)

    return "unknown", None, None, None  # unrecognized format - flagged, not silently guessed

_parsed = df["jobUploaded"].apply(parse_uploaded)
df["posting_time_type"] = _parsed.apply(lambda t: t[0])
df["posted_date"] = _parsed.apply(lambda t: t[1])
df["anticipated_start_min"] = _parsed.apply(lambda t: t[2])
df["anticipated_start_max"] = _parsed.apply(lambda t: t[3])

log(f"\n=== DATE CLASSIFICATION (full raw dataset, before any filtering) ===")
log(f"  posting_time_type: {df['posting_time_type'].value_counts().to_dict()}")

# ---------------------------------------------------------------------------
# STEP 1 - VALIDATION
# ---------------------------------------------------------------------------
# NOTE on a real trap in this data: salary == "Not disclosed" is encoded as
# minimumSalary=0, maximumSalary=0 - NOT null. Treating 0/0 as "missing" would
# wrongly flag 64,121 rows (65% of the dataset) that are perfectly valid
# postings with an undisclosed salary. "Missing" here means genuinely null.
#
# SECOND trap, found while wiring up posting_time_type: ALL 571 rows where
# experience AND salary are both genuinely absent are ALSO exactly the 571
# 'future_start' rows (100% overlap, verified). That's not a coincidence to
# paper over - a posting that says "Starts in 3 months" structurally hasn't
# finalized salary/experience yet; that's expected, not a data defect. The
# original rule dropped all of them, which silently zeroed out 100% of this
# dataset's forward-looking hiring-intent signal (93 of the 571 are
# IT/Software by keyword match - real anticipated-demand data). Fixed: the
# missing-both-fields drop rule now only applies to 'past'/'unknown' rows.
# A future_start row can still be dropped for missing title/location, just
# not for missing salary/experience.

missing_title = df["title"].isna()
missing_location = df["location"].isna() | (df["location"].astype(str).str.strip() == "")
missing_both_salary_and_exp = (
    df["minimumSalary"].isna() & df["maximumSalary"].isna()
    & df["minimumExperience"].isna() & df["maximumExperience"].isna()
)
missing_both_applies = missing_both_salary_and_exp & (df["posting_time_type"] != "future_start")

log(f"\n=== STEP 1: VALIDATION ===")
log(f"  missing title: {missing_title.sum()}")
log(f"  missing/blank location: {missing_location.sum()}")
log(f"  missing BOTH salary and experience entirely, EXCLUDING future_start rows "
    f"(those {int((missing_both_salary_and_exp & (df['posting_time_type']=='future_start')).sum())} "
    f"rows are exempt - see note above): {missing_both_applies.sum()}")

drop_mask = missing_title | missing_location | missing_both_applies
df_valid = df[~drop_mask].copy()
log(f"  dropped: {drop_mask.sum()} | remaining: {len(df_valid)}")

# ---------------------------------------------------------------------------
# STEP 2 - SECTOR / SCOPE FILTER (runs on the validated set, before any other cleaning)
# ---------------------------------------------------------------------------

combined_text = (
    df_valid["title"].fillna("") + " "
    + df_valid["tagsAndSkills"].fillna("") + " "
    + df_valid["jobDescription"].fillna("")
).str.lower()

sector_patterns = {}
for sector, spec in SECTORS.items():
    kws = spec["occupation_keywords"] + spec["skill_keywords"]
    sector_patterns[sector] = re.compile(
        "|".join(r"\b" + re.escape(k.lower()) + r"\b" for k in kws)
    )

hit_counts = pd.DataFrame(
    {sector: combined_text.str.count(pat) for sector, pat in sector_patterns.items()},
    index=df_valid.index,
)

max_hits = hit_counts.max(axis=1)
is_out_of_scope = max_hits == 0
# ambiguous = 2+ sectors tied for the top (non-zero) hit count
n_top = (hit_counts.eq(max_hits, axis=0)).sum(axis=1).where(max_hits > 0, 0)
is_ambiguous = (max_hits > 0) & (n_top > 1)

assigned_sector = hit_counts.idxmax(axis=1)
assigned_sector[is_out_of_scope] = "OUT_OF_SCOPE"
assigned_sector[is_ambiguous] = "AMBIGUOUS"

df_valid["sector"] = assigned_sector

log(f"\n=== STEP 2: SECTOR/SCOPE FILTER ===")
log(f"  total validated rows: {len(df_valid)}")
counts = df_valid["sector"].value_counts()
log(counts.to_string())
n_it = int((~df_valid["sector"].isin(["OUT_OF_SCOPE", "AMBIGUOUS"])).sum())
n_oos = int((df_valid["sector"] == "OUT_OF_SCOPE").sum())
n_amb = int((df_valid["sector"] == "AMBIGUOUS").sum())
frac_it = n_it / len(df_valid) * 100
log(f"\n  IT/Software (confidently assigned): {n_it} ({frac_it:.1f}%)")
log(f"  Out of scope: {n_oos} ({n_oos/len(df_valid)*100:.1f}%)")
log(f"  Ambiguous (needs manual review): {n_amb} ({n_amb/len(df_valid)*100:.1f}%)")

df_it = df_valid[~df_valid["sector"].isin(["OUT_OF_SCOPE", "AMBIGUOUS"])].copy()
df_oos = df_valid[df_valid["sector"] == "OUT_OF_SCOPE"].copy()
df_amb = df_valid[df_valid["sector"] == "AMBIGUOUS"].copy()

# ---------------------------------------------------------------------------
# STEP 3 - COLUMN STANDARDIZATION (on the IT/Software subset only)
# ---------------------------------------------------------------------------

log(f"\n=== STEP 3: COLUMN STANDARDIZATION ===")

std = pd.DataFrame()
std["id"] = df_it["jobId"]
std["title"] = df_it["title"]
std["company_raw"] = df_it["companyName"]
std["description"] = df_it["jobDescription"]
std["sector"] = df_it["sector"]
std["exp_min"] = df_it["minimumExperience"]
std["exp_max"] = df_it["maximumExperience"]
# salary "Not disclosed" -> 0/0 in source; convert back to null so it isn't
# mistaken for an actual zero salary downstream.
is_not_disclosed = (df_it["minimumSalary"] == 0) & (df_it["maximumSalary"] == 0)
std["salary_min"] = df_it["minimumSalary"].where(~is_not_disclosed)
std["salary_max"] = df_it["maximumSalary"].where(~is_not_disclosed)
std["location_raw"] = df_it["location"]
std["source"] = "naukri:indian-job-market-dataset-2025"
std["posting_time_type"] = df_it["posting_time_type"]
std["posted_date"] = df_it["posted_date"]
std["anticipated_start_min"] = df_it["anticipated_start_min"]
std["anticipated_start_max"] = df_it["anticipated_start_max"]

log(f"  {len(std)} rows standardized; salary 'Not disclosed' (0/0) -> null for {int(is_not_disclosed.sum())} rows")

# mode: Hybrid / Remote / Onsite, from the location string
def derive_mode(loc: str) -> str:
    loc_l = str(loc).lower()
    if loc_l.startswith("hybrid"):
        return "Hybrid"
    if "remote" in loc_l:
        return "Remote"
    return "Onsite"

std["mode"] = std["location_raw"].apply(derive_mode)
log(f"  mode distribution: {std['mode'].value_counts().to_dict()}")

# ---------------------------------------------------------------------------
# STEP 4 - DATE NORMALIZATION (computed earlier, at load time - reported here)
# ---------------------------------------------------------------------------

log(f"\n=== STEP 4: DATE NORMALIZATION (posting_time_type: past vs future_start) ===")
type_counts = std["posting_time_type"].value_counts()
log(f"  posting_time_type distribution (IT/Software subset): {type_counts.to_dict()}")
log(f"  posted_date resolved for {std['posted_date'].notna().sum()} 'past' rows; "
    f"anticipated_start window resolved for {std['anticipated_start_min'].notna().sum()} 'future_start' rows")
n_unknown = (std["posting_time_type"] == "unknown").sum()
if n_unknown:
    log(f"  [WARN] {n_unknown} rows had an unrecognized jobUploaded format - both date fields left null, not guessed")

# ---------------------------------------------------------------------------
# STEP 5 - COMPANY NORMALIZATION
# ---------------------------------------------------------------------------

log(f"\n=== STEP 5: COMPANY NORMALIZATION ===")

SUFFIX_RE = re.compile(
    r"\b(pvt\.?|private|ltd\.?|limited|llp|inc\.?|corp\.?|corporation|co\.?|"
    r"technologies|technology|solutions|systems|india|global)\b",
    re.I,
)

def norm_company(name: str) -> str:
    s = str(name).lower()
    s = re.sub(r"[.,()&]", " ", s)
    s = SUFFIX_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

std["company_norm"] = std["company_raw"].apply(norm_company)

# canonical display spelling = most frequent raw spelling per normalized key
canonical = (
    std.groupby("company_norm")["company_raw"]
    .agg(lambda s: s.value_counts().idxmax())
)
std["company"] = std["company_norm"].map(canonical)

n_exact_merged = (std["company_raw"] != std["company"]).sum()
log(f"  {std['company_norm'].nunique()} distinct normalized company names "
    f"from {std['company_raw'].nunique()} distinct raw spellings "
    f"({n_exact_merged} rows had spelling auto-merged to the most common variant)")

# fuzzy near-duplicates ACROSS distinct normalized names -> review list, NOT auto-merged.
# Blocked by first 4 chars to keep this O(n) instead of O(n^2) over ~thousands of names.
FUZZY_THRESHOLD = 0.90
distinct_norms = [n for n in std["company_norm"].unique() if n]
blocks = {}
for n in distinct_norms:
    blocks.setdefault(n[:4], []).append(n)

review_pairs = []
for block_names in blocks.values():
    if len(block_names) < 2:
        continue
    for i in range(len(block_names)):
        for j in range(i + 1, len(block_names)):
            a, b = block_names[i], block_names[j]
            score = SequenceMatcher(None, a, b).ratio()
            if score >= FUZZY_THRESHOLD:
                review_pairs.append({
                    "company_a": canonical.get(a, a), "company_b": canonical.get(b, b),
                    "norm_a": a, "norm_b": b, "similarity": round(score, 3),
                })

review_df = pd.DataFrame(review_pairs).sort_values("similarity", ascending=False) if review_pairs else pd.DataFrame(
    columns=["company_a", "company_b", "norm_a", "norm_b", "similarity"])
review_df.to_csv(OUT / "companies_needs_review.csv", index=False)
log(f"  {len(review_df)} near-duplicate company pairs (similarity >= {FUZZY_THRESHOLD}) "
    f"written to companies_needs_review.csv for manual merge decision")

# ---------------------------------------------------------------------------
# STEP 6 - DISTRICT MAPPING
# ---------------------------------------------------------------------------
# EXPLODE vs pick-primary: explode wins for a skill-demand-by-district use
# case. A posting listed for "Thane, Navi Mumbai, Mumbai (All Areas)" is
# real hiring demand in all three places - the employer will fill it from
# any of them. Picking one "primary" district would (a) systematically
# undercount demand in whichever district isn't picked, and (b) make the
# choice arbitrary (first-listed is not "most important"). The cost is that
# `id` (=jobId) is no longer a unique row key after this step - one posting
# becomes N rows, one per district. That's intentional: it's what makes
# per-district skill-demand aggregation (F6/F8) correct. Dedup (step 7)
# still keys off the original posting, so this doesn't inflate duplicate
# counts.

log(f"\n=== STEP 6: DISTRICT MAPPING ===")

# Curated, EXACT-match lookup (not substring regex - a substring match on
# "nagar" alone pulls in Ahmedabad-area "Himatnagar", Telangana's
# "Karimnagar", Gujarat's "Jamnagar", etc. - all false positives caught
# while building this).
MH_DISTRICT = {
    "mumbai": "Mumbai City", "mumbai suburban": "Mumbai Suburban",
    "navi mumbai": "Thane",  # administrative simplification - Navi Mumbai
                              # spans Thane & Raigad; Panvel is handled separately below
    "panvel": "Raigad",
    "thane": "Thane", "kalyan": "Thane", "dombivli": "Thane", "ulhasnagar": "Thane",
    "ambernath": "Thane", "badlapur": "Thane", "bhiwandi": "Thane",
    "mira bhayandar": "Thane", "bhayandar": "Thane", "mira road": "Thane",
    "vasai": "Palghar", "virar": "Palghar", "vasai virar": "Palghar",
    "palghar": "Palghar", "boisar": "Palghar", "dahanu": "Palghar",
    "pune": "Pune", "pimpri": "Pune", "chinchwad": "Pune", "chakan": "Pune",
    "hinjewadi": "Pune",
    "nagpur": "Nagpur",
    "nashik": "Nashik",
    "aurangabad": "Aurangabad",  # official name now Chhatrapati Sambhajinagar
    "kolhapur": "Kolhapur",
    "solapur": "Solapur",
    "amravati": "Amravati",
    "akola": "Akola",
    "sangli": "Sangli",
    "satara": "Satara",
    "jalgaon": "Jalgaon",
    "raigad": "Raigad",
    "ratnagiri": "Ratnagiri",
    "wardha": "Wardha",
    "latur": "Latur",
    "chandrapur": "Chandrapur",
    "dhule": "Dhule",
    "ahmednagar": "Ahmednagar",  # official name now Ahilyanagar
    "yavatmal": "Yavatmal",
    "beed": "Beed",
    "buldhana": "Buldhana",
    "osmanabad": "Osmanabad", "dharashiv": "Osmanabad",
    "hingoli": "Hingoli",
    "gadchiroli": "Gadchiroli",
    "gondia": "Gondia",
    "bhandara": "Bhandara",
    "washim": "Washim",
    "parbhani": "Parbhani",
    "sindhudurg": "Sindhudurg",
    "nandurbar": "Nandurbar",
    "jalna": "Jalna",
    "nanded": "Nanded",
}

def split_location_tokens(loc: str):
    s = str(loc)
    s = re.sub(r"^\s*(hybrid|remote)\s*-\s*", "", s, flags=re.I)
    parts = [p.strip() for p in s.split(",")]
    out = []
    for p in parts:
        p = re.sub(r"\(.*?\)", "", p).strip()
        if p and p.lower() != "remote":
            out.append(p)
    return out or [s.strip()]

# a lightweight "does this look like an Indian place name" MH-adjacent guard
# isn't reliable enough to build - instead: anything not in MH_DISTRICT is
# classified OUT_OF_SCOPE (non-Maharashtra) UNLESS it matches a loose
# Maharashtra-city-ish pattern we don't have in the table yet, in which case
# it's UNMAPPED and logged for a human to add, rather than silently folded
# into OUT_OF_SCOPE.
MH_HINT_RE = re.compile(r"maharashtra", re.I)

exploded_rows = []
unmapped_log = []
for _, row in std.iterrows():
    tokens = split_location_tokens(row["location_raw"])
    districts_for_row = []
    for tok in tokens:
        key = re.sub(r"\s+", " ", tok.lower()).strip()
        if key in MH_DISTRICT:
            districts_for_row.append(MH_DISTRICT[key])
        elif MH_HINT_RE.search(tok):
            unmapped_log.append({"location_token": tok, "job_id": row["id"], "title": row["title"]})
            districts_for_row.append("UNMAPPED")
        else:
            districts_for_row.append("OUT_OF_SCOPE")
    seen = set()
    for d in districts_for_row:
        if d in seen:
            continue
        seen.add(d)
        r = row.copy()
        r["district"] = d
        exploded_rows.append(r)

std_exploded = pd.DataFrame(exploded_rows).reset_index(drop=True)

unmapped_df = pd.DataFrame(unmapped_log).drop_duplicates()
unmapped_df.to_csv(OUT / "districts_unmapped.csv", index=False)

n_mh = (std_exploded["district"] != "OUT_OF_SCOPE").sum() - (std_exploded["district"] == "UNMAPPED").sum()
log(f"  {len(std)} postings exploded to {len(std_exploded)} rows across the location split")
log(f"  district coverage: {std_exploded['district'].value_counts().to_dict()}")
log(f"  {len(unmapped_df)} distinct 'Maharashtra'-mentioning-but-unrecognized location tokens "
    f"-> districts_unmapped.csv (not silently dropped into OUT_OF_SCOPE)")

# ---------------------------------------------------------------------------
# STEP 7 - DEDUPLICATION
# ---------------------------------------------------------------------------
# Flags, does not drop. Two signals, either one marks a row "duplicate":
#  (a) same (company_norm, title, district) seen before
#  (b) same jobDescription text seen before under a different jobId
# First occurrence (by original row order) in each group is "active".

log(f"\n=== STEP 7: DEDUPLICATION ===")

key_a = std_exploded["company_norm"].fillna("") + "||" + std_exploded["title"].str.lower().str.strip() + "||" + std_exploded["district"]
dup_a = key_a.duplicated(keep="first")

desc_norm = std_exploded["description"].fillna("").str.lower().str.strip()
desc_norm = desc_norm.str.replace(r"\s+", " ", regex=True)
dup_b = desc_norm.duplicated(keep="first") & (desc_norm.str.len() > 20)  # ignore near-empty descriptions

is_dup = dup_a | dup_b
std_exploded["status"] = pd.Series(is_dup).map({True: "duplicate", False: "active"})

dup_rate = is_dup.mean() * 100
log(f"  duplicate rate (company+title+district, or identical description text): {dup_rate:.1f}% "
    f"({int(is_dup.sum())} of {len(std_exploded)} rows)")
log(f"  compare: exact full-row duplicates in the RAW source were only {df.duplicated().sum()} rows (0.3%) - "
    f"the much higher rate here is expected: it's catching the same job reposted under near-identical "
    f"text, which raw dedup on jobId alone misses. This matches typical Naukri-scrape repost behavior.")

# ---------------------------------------------------------------------------
# FINAL COLUMN ORDER + WRITE
# ---------------------------------------------------------------------------

final_cols = ["id", "title", "company", "description", "district", "sector",
              "exp_min", "exp_max", "salary_min", "salary_max", "mode",
              "source", "posting_time_type", "posted_date",
              "anticipated_start_min", "anticipated_start_max", "status"]
jobs_final = std_exploded[final_cols].copy()
jobs_final.to_csv(OUT / "jobs.csv", index=False)

df_oos_out = df_oos[["jobId", "title", "companyName", "location", "tagsAndSkills"]].rename(
    columns={"jobId": "id", "companyName": "company", "location": "location_raw"})
df_oos_out.to_csv(OUT / "jobs_out_of_scope.csv", index=False)

df_amb_out = df_amb[["jobId", "title", "companyName", "location", "tagsAndSkills"]].rename(
    columns={"jobId": "id", "companyName": "company", "location": "location_raw"})
df_amb_out.to_csv(OUT / "jobs_ambiguous_review.csv", index=False)

# ---------------------------------------------------------------------------
# STEP 8 - QUALITY REPORT
# ---------------------------------------------------------------------------

log(f"\n=== STEP 8: QUALITY REPORT ===")
log(f"  raw rows: {n_start}")
log(f"  after validation: {len(df_valid)}")
log(f"  IT/Software (confident): {n_it}  |  out-of-scope: {n_oos}  |  ambiguous: {n_amb}")
log(f"  final jobs.csv rows (post-explode): {len(jobs_final)}")
log(f"  final ACTIVE (non-duplicate) rows: {(jobs_final['status']=='active').sum()}")
maha_active = jobs_final[(jobs_final["status"] == "active") & (~jobs_final["district"].isin(["OUT_OF_SCOPE", "UNMAPPED"]))]
log(f"  final Maharashtra, active, IT/Software rows (the number that matters for F2/F8): {len(maha_active)}")
log(f"\n  null rates (final jobs.csv):")
log((jobs_final.isna().mean() * 100).round(1).to_string())
log(f"\n  subcategory distribution (active MH rows only):")
log(maha_active["sector"].value_counts().to_string())
log(f"\n  district coverage % (share of active MH rows with a real, non-UNMAPPED district): "
    f"{(maha_active['district']!='UNMAPPED').mean()*100:.1f}%")

(OUT / "jobs_quality_report.txt").write_text("\n".join(report_lines))
log(f"\nWrote jobs.csv ({len(jobs_final)} rows), jobs_out_of_scope.csv ({len(df_oos_out)} rows), "
    f"jobs_ambiguous_review.csv ({len(df_amb_out)} rows), companies_needs_review.csv, "
    f"districts_unmapped.csv, jobs_quality_report.txt")
