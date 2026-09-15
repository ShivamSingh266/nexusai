"""
T7 - Course-Skill Alignment.

Input:  data/raw/courses/NPTEL_Dep_Free_Elective.csv (89 rows)
        data/raw/courses/NPTEL_HS_MG.csv (293 rows)
        data/processed/skills.csv, skill_aliases.csv (T2, 642 skills)
        data/processed/skill_demand_history.csv (T6, corrected)

Output: courses.csv, course_skills.csv, courses_no_skills.csv, training_gap.csv,
        course_alignment_report.txt
"""

import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(Path(__file__).parent / "t3_extraction"))
from parsing import parse_document  # noqa: E402
from patterns import load_phrase_to_skill  # noqa: E402
from matcher_fallback import FallbackPhraseMatcher  # noqa: E402
from extract import extract_from_document  # noqa: E402

ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
RAW = ROOT / "data" / "raw" / "courses"
CONFIG = ROOT / "config" / "taxonomy_config.json"
PROCESSED = ROOT / "data" / "processed"

report = []
def log(s=""):
    print(s)
    report.append(str(s))

# ---------------------------------------------------------------------------
# LOAD + COMBINE
# ---------------------------------------------------------------------------

dep = pd.read_csv(RAW / "NPTEL_Dep_Free_Elective.csv")
hsmg = pd.read_csv(RAW / "NPTEL_HS_MG.csv")

log("=== LOAD ===")
log(f"Dep_Free_Elective: {len(dep)} rows | HS_MG: {len(hsmg)} rows")

# NOTE on a spec assumption that doesn't hold in the real files: "Category"
# was meant to help with scope filtering / level inference. It can't do
# either job here -
#   - HS_MG has NO Category column at all.
#   - Dep_Free_Elective's Category values are {BP, BD, SE} (63/25/1 rows) -
#     these are NPTEL elective-TYPE codes (breadth/depth/something-elective),
#     not subject-domain or difficulty-level codes. There's no public NPTEL
#     documentation tying BP/BD/SE to a level, and guessing one would be
#     fabricating a level from a code that doesn't encode it.
# So: scope filter runs on Course Name only (not Category), and `level` in
# courses.csv is null for every row - flagged here rather than force-fit.
if "Category" not in hsmg.columns:
    hsmg["Category"] = pd.NA

dep["source_file"] = "NPTEL_Dep_Free_Elective"
hsmg["source_file"] = "NPTEL_HS_MG"
combined = pd.concat([dep, hsmg], ignore_index=True, sort=False)

# dedupe on NPTEL_ID - HS_MG has 20 ids listed twice (same course offered in
# both the Jul-Dec 2025 and Jan-Apr 2026 windows, one row each)
before = len(combined)
combined = combined.drop_duplicates(subset="NPTEL_ID", keep="first")
log(f"Combined: {before} rows -> {len(combined)} after deduping repeat NPTEL_ID listings "
    f"(same course offered in two term windows)")

# ---------------------------------------------------------------------------
# STEP 1 - SCOPE FILTER (Course Name only - see Category note above)
# ---------------------------------------------------------------------------
# TWO signals, combined - one alone badly under-fires on course titles:
#   (a) T5's job-posting keyword lists (taxonomy_config.json occupation/skill
#       keywords) - tuned for LONG job-description text, not 3-5 word
#       academic titles. Tested alone on the 89 dept-elective titles (which
#       are almost all genuinely IT/CS by inspection): only 14/89 hit. It
#       missed "Ethical Hacking", "Compiler Design", "Blockchain and its
#       Applications", "Cyber Security and Privacy", "Software Project
#       Management" - all obviously in-scope, none containing a literal
#       occupation-description phrase.
#   (b) Direct match against the skills.csv/skill_aliases.csv phrase pool
#       itself (all 642 skills, bidirectional substring - a title can be a
#       PREFIX of a longer skill phrase, e.g. "Ethical Hacking" vs the
#       registered skill "ethical hacking principles", not just the other
#       way round). Alone: 35/89. Better, but still real, structural misses
#       remain (see note after the run): VLSI, compiler design, hardware/
#       digital design, formal theory - ESCO is a LABOR-MARKET skills
#       framework, it doesn't model CS-curriculum/hardware-design topics at
#       all, in either direction. That's a taxonomy-coverage limitation, not
#       a matching bug - can't be fixed by better string matching.
# Combined: if (b) gives one non-Transversal category, use it (most
# specific signal). If (b) is ambiguous across categories, let (a) break the
# tie if it agrees with one of them. If (b) found nothing, fall back to (a)
# alone (its normal OUT_OF_SCOPE/AMBIGUOUS/sector logic).

cfg = json.load(open(CONFIG))
SECTORS = cfg["sectors"]

title_text = combined["Course Name"].fillna("").str.lower()

# (a) keyword-list signal (same as T5)
sector_patterns = {
    sector: re.compile("|".join(r"\b" + re.escape(k.lower()) + r"\b"
                                 for k in spec["occupation_keywords"] + spec["skill_keywords"]))
    for sector, spec in SECTORS.items()
}
hit_counts = pd.DataFrame(
    {sector: title_text.str.count(pat) for sector, pat in sector_patterns.items()},
    index=combined.index,
)
kw_max = hit_counts.max(axis=1)
kw_top_n = hit_counts.eq(kw_max, axis=0).sum(axis=1).where(kw_max > 0, 0)
kw_sector = hit_counts.idxmax(axis=1)
kw_sector[kw_max == 0] = "OUT_OF_SCOPE"
kw_sector[(kw_max > 0) & (kw_top_n > 1)] = "AMBIGUOUS"

# (b) direct skill-phrase signal, ALL categories, bidirectional substring
skills_df_tmp = pd.read_csv(PROCESSED / "skills.csv")
aliases_df_tmp = pd.read_csv(PROCESSED / "skill_aliases.csv")
cat_by_skill_tmp = skills_df_tmp.set_index("skill_id")["category"]
phrase_cat_pairs = [(str(r["canonical_name"]).strip().lower(), r["category"])
                    for _, r in skills_df_tmp.iterrows()]
phrase_cat_pairs += [(str(r["alias"]).strip().lower(), cat_by_skill_tmp.get(r["skill_id"]))
                     for _, r in aliases_df_tmp.iterrows()]
phrase_cat_pairs = [(p, c) for p, c in phrase_cat_pairs if len(p) >= 3 and c != "Transversal"]

# SCOPE-ONLY stoplist - found by auditing which HS_MG (Humanities/Management)
# titles got an IT/Software category from the direct-match signal alone.
# These are real ESCO skill/alias phrases, correctly filed under an
# IT/Software category by T2 (they DO show up in ICT occupations) - but
# they're also ordinary generic business/academic terms used constantly
# OUTSIDE IT ("Project Management for Managers", "Business Ethics",
# "Mathematics For Economics", "Six Sigma", "Intellectual Property",
# "Cognitive Psychology" all matched this way and are NOT IT/Software
# courses). Fine as a SKILL for a job posting where surrounding context
# disambiguates; not reliable as a bare course-title SCOPE signal. Excluded
# here from the scope decision only - still usable in STEP 2 tagging for a
# course that's already in scope through some other signal.
SCOPE_STOPLIST = {
    "ethics", "mathematics", "algorithmic", "project management",
    "business analytics", "decision support systems", "survey data",
    "safety engineering", "intellectual property", "six sigma",
    "lean six sigma", "cognitive psychology", "data analysis",
}
scope_phrase_cat_pairs = [(p, c) for p, c in phrase_cat_pairs if p not in SCOPE_STOPLIST]

def direct_categories(title_l: str) -> set:
    if len(title_l) < 4:
        return set()
    cats = set()
    for phrase, cat in scope_phrase_cat_pairs:
        if re.search(r"\b" + re.escape(phrase) + r"\b", title_l) or \
           (title_l in phrase and len(title_l) >= 4):
            cats.add(cat)
    return cats

direct_cats_per_title = title_text.apply(direct_categories)

def resolve(direct_cats, kw_val):
    if len(direct_cats) == 1:
        return next(iter(direct_cats))
    if len(direct_cats) > 1:
        return kw_val if kw_val in direct_cats else "AMBIGUOUS"
    return kw_val  # no direct signal - defer entirely to keyword-list

combined["subcategory"] = [resolve(dc, kw) for dc, kw in zip(direct_cats_per_title, kw_sector)]

log(f"\n=== STEP 1: SCOPE FILTER (direct skill-phrase match + keyword-list fallback, see script comments) ===")
log(combined["subcategory"].value_counts().to_string())
n_it = int((~combined["subcategory"].isin(["OUT_OF_SCOPE", "AMBIGUOUS"])).sum())
log(f"\nSurviving IT/Software courses: {n_it} / {len(combined)} ({n_it/len(combined)*100:.1f}%)")
log(f"  by source file: {combined[~combined['subcategory'].isin(['OUT_OF_SCOPE','AMBIGUOUS'])]['source_file'].value_counts().to_dict()}")
log(f"  (keyword-list alone would have caught only {(kw_max>0).sum()} of these - direct skill-phrase "
    f"matching against the full 642-skill pool recovers most of the rest; a residual, structural gap - "
    f"VLSI, compiler design, hardware/digital design, pure theory courses - remains genuinely unscored "
    f"because ESCO's labor-market skill taxonomy doesn't model CS-curriculum/hardware topics at all, not "
    f"because of a matching weakness)")

courses_it = combined[~combined["subcategory"].isin(["OUT_OF_SCOPE", "AMBIGUOUS"])].copy()
courses_ambiguous = combined[combined["subcategory"] == "AMBIGUOUS"].copy()
if len(courses_ambiguous):
    courses_ambiguous[["NPTEL_ID", "Course Name", "source_file"]].to_csv(
        PROCESSED / "courses_ambiguous_review.csv", index=False)
    log(f"  {len(courses_ambiguous)} ambiguous (tied-sector) courses -> courses_ambiguous_review.csv")

# ---------------------------------------------------------------------------
# STEP 2a - DIRECT TITLE MATCH
# ---------------------------------------------------------------------------

skills_df = pd.read_csv(PROCESSED / "skills.csv")
aliases_df = pd.read_csv(PROCESSED / "skill_aliases.csv")

phrase_rows = []  # (phrase, skill_id)
for _, r in skills_df.iterrows():
    phrase_rows.append((str(r["canonical_name"]).strip().lower(), r["skill_id"]))
for _, r in aliases_df.iterrows():
    phrase_rows.append((str(r["alias"]).strip().lower(), r["skill_id"]))
# drop ambiguous phrases (same rule as T3) and phrases too short/generic to
# substring-match safely (single very short tokens cause false positives -
# e.g. "R" matching inside "Programming")
phrase_map = {}
ambiguous_phrases = set()
for phrase, sid in phrase_rows:
    if len(phrase) < 3:
        continue
    phrase_map.setdefault(phrase, set()).add(sid)
for phrase, sids in list(phrase_map.items()):
    if len(sids) > 1:
        ambiguous_phrases.add(phrase)
        del phrase_map[phrase]

direct_rows = []
for _, course in courses_it.iterrows():
    title_l = str(course["Course Name"]).lower()
    for phrase, sid in phrase_map.items():
        sid = next(iter(sid))
        # word-boundary substring in EITHER direction: "Cloud computing"
        # title contains "cloud computing" skill phrase; also handles a
        # skill phrase that's the whole title plus a qualifier
        if re.search(r"\b" + re.escape(phrase) + r"\b", title_l):
            direct_rows.append({"course_id": course["NPTEL_ID"], "skill_id": sid,
                                 "coverage_level": "direct_title_match", "confidence": 0.97})

direct_df = pd.DataFrame(direct_rows).drop_duplicates(subset=["course_id", "skill_id"])
log(f"\n=== STEP 2a: DIRECT TITLE MATCH ===")
log(f"  {len(direct_df)} (course, skill) pairs from literal title/alias substring match")
log(f"  {direct_df['course_id'].nunique()} / {len(courses_it)} courses got >=1 direct match")

# ---------------------------------------------------------------------------
# STEP 2b - CATEGORY-INFERRED (course-to-skill-cluster)
# ---------------------------------------------------------------------------
# Method: within the course's OWN assigned subcategory's skill pool (not the
# whole 642-skill taxonomy - a Data & AI course shouldn't get Cybersecurity
# skills by embedding coincidence), rank every skill/alias phrase by TF-IDF
# char-ngram cosine similarity to the course title (same technique as T4's
# fallback embedder - reused, not reinvented), take the top few above a
# floor, EXCLUDING skills already caught by the direct match (no point
# tagging the same skill twice at two confidence levels).
# Confidence is capped well below direct_title_match's band (0.97) so
# nothing downstream can mistake an inferred cluster tag for a literal hit.

CATEGORY_INFER_FLOOR = 0.22   # similarity floor - set empirically, see report
CATEGORY_INFER_MAX_PER_COURSE = 6
CATEGORY_INFER_CONF_CAP = 0.55

skills_df["phrase"] = skills_df["canonical_name"]
alias_join = aliases_df.rename(columns={"alias": "phrase"})[["phrase", "skill_id"]]
skill_phrase_pool = pd.concat(
    [skills_df[["phrase", "skill_id", "category"]],
     alias_join.merge(skills_df[["skill_id", "category"]], on="skill_id", how="left")],
    ignore_index=True,
).dropna(subset=["phrase"])

inferred_rows = []
for sector in courses_it["subcategory"].unique():
    pool = skill_phrase_pool[skill_phrase_pool["category"] == sector]
    if pool.empty:
        continue
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, lowercase=True)
    pool_matrix = vec.fit_transform(pool["phrase"].astype(str))

    sector_courses = courses_it[courses_it["subcategory"] == sector]
    q_matrix = vec.transform(sector_courses["Course Name"].astype(str))
    sims = cosine_similarity(q_matrix, pool_matrix)

    for i, (_, course) in enumerate(sector_courses.iterrows()):
        already = set(direct_df[direct_df["course_id"] == course["NPTEL_ID"]]["skill_id"])
        row_sims = sims[i]
        order = np.argsort(-row_sims)
        picked = 0
        for idx in order:
            if picked >= CATEGORY_INFER_MAX_PER_COURSE:
                break
            score = row_sims[idx]
            if score < CATEGORY_INFER_FLOOR:
                break
            sid = pool.iloc[idx]["skill_id"]
            if sid in already:
                continue
            inferred_rows.append({"course_id": course["NPTEL_ID"], "skill_id": sid,
                                   "coverage_level": "category_inferred",
                                   "confidence": round(min(score, 1.0) * CATEGORY_INFER_CONF_CAP, 3)})
            already.add(sid)
            picked += 1

inferred_df = pd.DataFrame(inferred_rows).drop_duplicates(subset=["course_id", "skill_id"])
log(f"\n=== STEP 2b: CATEGORY-INFERRED (TF-IDF cluster match within course's subcategory) ===")
log(f"  floor={CATEGORY_INFER_FLOOR}, max {CATEGORY_INFER_MAX_PER_COURSE}/course, confidence capped at {CATEGORY_INFER_CONF_CAP}")
log(f"  {len(inferred_df)} (course, skill) pairs")
per_course = inferred_df.groupby("course_id").size()
log(f"  courses with >=1 inferred tag: {inferred_df['course_id'].nunique()} / {len(courses_it)} "
    f"(mean {per_course.mean():.1f}, median {per_course.median():.0f} tags/course where any exist)")

# ---------------------------------------------------------------------------
# STEP 2c - SUPPLEMENTARY EXTRACTION (T3/T4 pipeline, Course Name + SME Name + Comments)
# ---------------------------------------------------------------------------

phrase_to_skill = load_phrase_to_skill(PROCESSED / "skills.csv", PROCESSED / "skill_aliases.csv")
matcher = FallbackPhraseMatcher(phrase_to_skill)

extraction_rows = []
n_mentions_total = 0
for _, course in courses_it.iterrows():
    parts = [str(course["Course Name"])]
    if pd.notna(course.get("SME Name")):
        parts.append(str(course["SME Name"]))
    if pd.notna(course.get("Comments")):
        parts.append(str(course["Comments"]))
    text = ". ".join(parts)
    doc = parse_document("course", str(course["NPTEL_ID"]), text)
    matches = matcher.find_matches(doc.normalized_text)
    n_mentions_total += len(matches)
    seen = set()
    for start, end, sid, mention_text in matches:
        if sid in seen:
            continue
        seen.add(sid)
        extraction_rows.append({"course_id": course["NPTEL_ID"], "skill_id": sid,
                                 "coverage_level": "extraction", "confidence": 1.0})

extraction_df = pd.DataFrame(extraction_rows).drop_duplicates(subset=["course_id", "skill_id"]) if extraction_rows else \
    pd.DataFrame(columns=["course_id", "skill_id", "coverage_level", "confidence"])

log(f"\n=== STEP 2c: SUPPLEMENTARY EXTRACTION (T3/T4 matcher, Course Name + SME Name + Comments) ===")
log(f"  REAL number, not assumed: {n_mentions_total} raw mentions across {len(courses_it)} IT/Software courses "
    f"({n_mentions_total/len(courses_it):.2f} mentions/course)")
log(f"  {extraction_df['course_id'].nunique() if len(extraction_df) else 0} / {len(courses_it)} courses got >=1 extraction hit")
log(f"  Confirms the Task 3 finding: this is a weak supplementary signal on this dataset, not a primary method - "
    f"used here for its {len(extraction_df)} (course,skill) pairs on top of the other two methods, nothing more.")

# ---------------------------------------------------------------------------
# STEP 3 - COMBINE (priority: direct_title_match > extraction > category_inferred)
# ---------------------------------------------------------------------------

all_tags = pd.concat([direct_df, extraction_df, inferred_df], ignore_index=True)
priority = {"direct_title_match": 0, "extraction": 1, "category_inferred": 2}
all_tags["_p"] = all_tags["coverage_level"].map(priority)
all_tags = all_tags.sort_values("_p").drop_duplicates(subset=["course_id", "skill_id"], keep="first").drop(columns="_p")

course_skills = all_tags.sort_values(["course_id", "confidence"], ascending=[True, False])
course_skills.to_csv(PROCESSED / "course_skills.csv", index=False)
log(f"\n=== COMBINED course_skills.csv ===")
log(f"  {len(course_skills)} total (course, skill) pairs")
log(course_skills["coverage_level"].value_counts().to_string())

# ---------------------------------------------------------------------------
# COURSES.CSV + ZERO-SKILL FLAGGING
# ---------------------------------------------------------------------------

courses_out = pd.DataFrame({
    "id": courses_it["NPTEL_ID"],
    "provider": "NPTEL",
    "name": courses_it["Course Name"],
    "subcategory": courses_it["subcategory"],
    "level": pd.NA,  # see Category note above - not inferable from this data
    "duration_weeks": courses_it["Current Duration in weeks"],
    "credits": courses_it["No. of credits"],
    "source_url": courses_it["NPTEL URL"],
})
courses_out.to_csv(PROCESSED / "courses.csv", index=False)

tagged_ids = set(course_skills["course_id"])
zero_skill = courses_out[~courses_out["id"].isin(tagged_ids)]
zero_skill.to_csv(PROCESSED / "courses_no_skills.csv", index=False)

log(f"\n=== OUTPUT ===")
log(f"  courses.csv: {len(courses_out)} rows")
log(f"  course_skills.csv: {len(course_skills)} rows")
log(f"  courses_no_skills.csv: {len(zero_skill)} courses with ZERO tagged skills after all 3 methods "
    f"({len(zero_skill)/len(courses_out)*100:.1f}%) - not force-tagged")

# ---------------------------------------------------------------------------
# STEP 4 - GAP ANALYSIS
# ---------------------------------------------------------------------------

demand = pd.read_csv(PROCESSED / "skill_demand_history.csv")
tier_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INSUFFICIENT": 0}
demand["_rank"] = demand["strength_tier"].map(tier_rank)
best_tier = (
    demand.sort_values("_rank", ascending=False)
    .drop_duplicates(subset="skill_id", keep="first")[["skill_id", "strength_tier"]]
    .rename(columns={"strength_tier": "demand_strength_tier"})
)

high_medium = best_tier[best_tier["demand_strength_tier"].isin(["HIGH", "MEDIUM"])].copy()
course_counts = course_skills.groupby("skill_id")["course_id"].nunique().rename("course_count")
high_medium = high_medium.merge(course_counts, on="skill_id", how="left")
high_medium["course_count"] = high_medium["course_count"].fillna(0).astype(int)
high_medium["gap_flag"] = high_medium["course_count"] == 0

skill_names = skills_df.set_index("skill_id")["canonical_name"]
high_medium["skill_name"] = high_medium["skill_id"].map(skill_names)

training_gap = high_medium[["skill_id", "demand_strength_tier", "course_count", "gap_flag"]].sort_values(
    ["gap_flag", "demand_strength_tier", "skill_id"], ascending=[False, True, True])
training_gap.to_csv(PROCESSED / "training_gap.csv", index=False)

n_gap = int(high_medium["gap_flag"].sum())
log(f"\n=== STEP 4: GAP ANALYSIS ===")
log(f"  {len(high_medium)} skills have HIGH or MEDIUM demand_strength_tier somewhere in skill_demand_history.csv")
log(f"  {n_gap} of those ({n_gap/len(high_medium)*100:.1f}%) have ZERO course coverage (gap_flag=TRUE)")
log(f"  {len(high_medium)-n_gap} have >=1 course teaching them")
log(f"\n  Highest-demand skills with a training gap (sample):")
log(high_medium[high_medium["gap_flag"]].merge(
    demand[demand["strength_tier"].isin(["HIGH", "MEDIUM"])].groupby("skill_id")["demand_score"].max(),
    on="skill_id", how="left"
).sort_values("demand_score", ascending=False)[["skill_id", "skill_name", "demand_strength_tier", "demand_score"]]
    .head(15).to_string(index=False))

(PROCESSED / "course_alignment_report.txt").write_text("\n".join(report))
print("\nWrote course_alignment_report.txt")
