"""
T7 SUPPLEMENT - Append 20 manually-sourced (non-NPTEL) courses to close
practitioner-tool training gaps that NPTEL structurally doesn't cover.

Inputs (unmodified):
  skills.csv, skill_aliases.csv   (T2 - same 642-skill taxonomy, no new skills)
  courses.csv, course_skills.csv  (T7 - freshly regenerated after the T2
                                    must_include category fix)
  skill_demand_history.csv        (T6)

Outputs (overwritten):
  courses.csv          - +20 rows, + 'source' and 'needs_manual_url' columns
                          on ALL 66 rows (existing 46 backfilled source='NPTEL')
  course_skills.csv    - +N rows, coverage_level='manual_supplement', conf=0.75
  training_gap.csv     - recomputed against the 66-course set
  manual_course_supplement_report.txt - full audit trail: every mapping
                          decision, every flagged/unmapped case, before/after
                          gap numbers.

Non-fabrication rules followed throughout (per spec):
  - no source_url invented -> null + needs_manual_url=True
  - no skill_id force-matched -> unmapped skill_category text is reported,
    not silently tagged
  - no new skill_id namespace collision with real NPTEL ids -> see ID NOTE

RESOLVED-BY-TERM, NOT HARDCODED skill_id (important, found via T8):
  This script originally hardcoded literal skill_id constants (SKILL_0317
  for Cisco, etc.). T8's --reset rebuild proved that wrong: skill_id is
  only stable when an existing skills.csv is present for T2 to carry IDs
  forward from (by esco_uri). A genuine from-scratch rebuild has no such
  file to inherit from, so it mints a fresh, internally self-consistent,
  but DIFFERENT id<->skill mapping (verified deterministic across repeated
  from-scratch runs - see chat/T8 report - just not equal to the old,
  incrementally-built mapping). Under the old hardcoded version, a --reset
  run silently mis-tagged courses (e.g. the Cisco course landed on
  whatever skill SKILL_0317 happened to be that run, which was NOT Cisco).
  Fixed by resolving each course's skill(s) by NAME/ALIAS TEXT against
  whatever skills.csv/skill_aliases.csv currently contains, every run -
  same matching policy as the original manual research (canonical exact
  match preferred, then alias exact match). If a term that used to resolve
  ever stops resolving (taxonomy scope changed under it), this is reported
  loudly as a WARNING rather than silently dropped or wrongly tagged.
"""

import os
from pathlib import Path
import pandas as pd

ROOT = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parent.parent))
PROCESSED = ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# 0. THE 20 COURSES, exactly as given, plus the mapping decided for each.
#    subcategory: one of the 5 IT/Software sectors, or None = UNMAPPED
#    skill_terms: canonical_name or alias TEXT to resolve against the LIVE
#                 taxonomy at run time (not a hardcoded skill_id - see
#                 module docstring for why). [] = no clean match (report,
#                 don't force).
#    note: the judgment call / flag for that row, shown to the user verbatim
# ---------------------------------------------------------------------------

COURSES = [
    dict(name="AI DevOps Analyst", provider="NASSCOM", skill_category="DevOps/AI",
         subcategory="IT/Software - IT Infrastructure & Networks", skill_terms=["DevOps"],
         note="Matched on 'DevOps' only. The 'AI' half of the category label has no match: "
              "this 642-skill taxonomy has no 'artificial intelligence' skill at all (checked "
              "canonical names and aliases, exact and substring - none exists), so it is left "
              "untagged rather than guessed at."),
    dict(name="AI – Data Engineering Analyst", provider="NASSCOM", skill_category="Data Engineering",
         subcategory="IT/Software - Data & AI", skill_terms=["data engineering"],
         note="Matched on 'Data Engineering'. Same 'AI' caveat as above - not tagged, no such "
              "skill exists in the taxonomy."),
    dict(name="IoT Security Analyst", provider="NASSCOM", skill_category="Cybersecurity/IoT",
         subcategory="IT/Software - Cybersecurity", skill_terms=["cybersecurity", "IoT"],
         note="Both halves matched cleanly: cyber security (via 'cybersecurity' alias) and "
              "Internet of Things (via 'IoT' alias). FLAG: the IoT skill's own taxonomy "
              "category is 'Software Development', not Cybersecurity - same kind of ESCO "
              "placement quirk as C#/PHP/Visual Basic sitting under 'Data & AI'. The course "
              "is filed under Cybersecurity (matches the role title and the explicit config "
              "keyword), the skill tag itself keeps its real category."),
    dict(name="Network Security Engineer", provider="NASSCOM", skill_category="Networking/Cybersecurity",
         subcategory="IT/Software - Cybersecurity", skill_terms=["network security engineering"],
         note="Matched via alias 'network security engineering' -> security engineering. Bare "
              "'networking'/'network' was deliberately NOT tagged - it substring-matches 10+ "
              "unrelated skills (and even the single-letter skill 'R', a false positive from "
              "naive substring matching) with no single clean winner."),
    dict(name="Cloud Infrastructure Analyst", provider="NASSCOM", skill_category="Cloud/IT Infrastructure",
         subcategory="IT/Software - IT Infrastructure & Networks", skill_terms=["cloud computing", "ICT infrastructure"],
         note="Matched: cloud technologies (via 'cloud computing' alias) and ICT infrastructure "
              "(canonical exact). FLAG: both skills' own taxonomy categories are 'Software "
              "Development' and 'Cybersecurity' respectively, not IT Infrastructure & Networks "
              "- another instance of the same ESCO-placement quirk noted above. Subcategory "
              "follows the config's explicit keyword mapping (cloud computing / ICT "
              "infrastructure -> that sector), not the individual skills' own category field."),
    dict(name="IT Technical Support Executive", provider="NASSCOM", skill_category="IT Support",
         subcategory=None, skill_terms=[],
         note="UNMAPPED, as you anticipated. 'IT support'/'technical support'/'customer "
              "support'/'helpdesk' have no canonical, alias, or substring match anywhere in "
              "the 642-skill taxonomy, and none of the 5 sector configs (occupation or skill "
              "keywords) mention IT support/service-desk work at all. Not forced into any "
              "of the 5 subcategories."),
    dict(name="Web Developer", provider="NASSCOM", skill_category="Web Development",
         subcategory="IT/Software - Software Development", skill_terms=["implement front-end website design"],
         note="Subcategory is a clean fit ('web developer' is an explicit occupation_keyword "
              "under Software Development). No skill exists for generic 'web development' or "
              "'web design' (checked exact + substring - nothing). Tagged with 'implement "
              "front-end website design' as the closest real component skill - flagged as a "
              "partial/component match, not a literal 'web development' skill."),
    dict(name="Software Product Developer", provider="NASSCOM", skill_category="Software Development",
         subcategory="IT/Software - Software Development", skill_terms=[],
         note="Subcategory is a clean fit (occupation keyword). NO skill match: bare "
              "'software development' only substring-hits compound aliases for unrelated "
              "skills (Assembly, Lisp, SAS, Agile development principles, etc.) - none of "
              "those is actually what this course teaches, so none is tagged. Reporting as "
              "unmapped at the skill level rather than guessing."),
    dict(name="Application Developer – Web & Mobile", provider="Skill India/partner",
         skill_category="Web & Mobile Development",
         subcategory="IT/Software - Software Development", skill_terms=[],
         note="Subcategory is a clean fit ('mobile application developer' + 'web developer' "
              "are both occupation_keywords under Software Development). NO skill match: no "
              "clean 'web development' or 'mobile development' skill exists (the only 'mobile' "
              "hits are 'mobile device management' and 'mobile operating systems', both about "
              "managing/running mobile devices, not building apps for them - tagging either "
              "would be a false positive, so left unmapped)."),
    dict(name="Python Programming", provider="Microsoft", skill_category="Python",
         subcategory="IT/Software - Software Development", skill_terms=["Python programming"],
         note="Clean exact match via the manual alias 'Python programming' -> Python "
              "(computer programming)."),
    dict(name="PRDV401: Introduction to JavaScript I", provider="Saylor University", skill_category="JavaScript",
         subcategory="IT/Software - Software Development", skill_terms=["JavaScript"],
         note="Clean canonical exact match: JavaScript."),
    dict(name="PRDV401: Introduction to JavaScript II", provider="Saylor University", skill_category="JavaScript",
         subcategory="IT/Software - Software Development", skill_terms=["JavaScript"],
         note="Clean canonical exact match: JavaScript (same as Part I)."),
    dict(name="Networking Basics", provider="Cisco Networking Academy", skill_category="Networking",
         subcategory="IT/Software - IT Infrastructure & Networks", skill_terms=[],
         note="Subcategory is a clean fit (network administration/architecture are explicit "
              "skill_keywords for this sector). NO skill match at the skill_id level: bare "
              "'networking' has no clean single-skill answer in this taxonomy (same false-"
              "positive-prone substring problem as course #4) - reporting unmapped rather "
              "than forcing 'ICT networking hardware' or similar onto a basics course."),
    dict(name="Introduction to Cybersecurity", provider="Cisco Networking Academy", skill_category="Cybersecurity",
         subcategory="IT/Software - Cybersecurity", skill_terms=["cybersecurity"],
         note="Clean alias exact match: cyber security."),
    dict(name="Operating System Basics", provider="Cisco Networking Academy", skill_category="Operating Systems",
         subcategory="IT/Software - IT Infrastructure & Networks", skill_terms=["operating systems"],
         note="Clean canonical exact match: operating systems - this is one of the 19 "
              "must_include skills, and its category was one of the two we corrected in the "
              "T2 bug fix (was miscategorized under Cybersecurity before that fix, now "
              "correctly IT Infrastructure & Networks)."),
    dict(name="Data Analytics Essentials", provider="Cisco Networking Academy", skill_category="Data Analytics",
         subcategory="IT/Software - Data & AI", skill_terms=["data analytics"],
         note="Clean canonical exact match: data analytics."),
    dict(name="Engaging Stakeholders for Success", provider="Cisco Networking Academy",
         skill_category="Project/Stakeholder Management",
         subcategory="IT/Software - Software Development", skill_terms=["engage with stakeholders", "project management"],
         note="JUDGMENT CALL, flagged: matched both 'engage with stakeholders' and 'project "
              "management' - the two skills sit in different taxonomy categories "
              "(Cybersecurity and Software Development respectively, another ESCO-placement "
              "quirk). Subcategory assigned as Software Development since that is where "
              "'project management' itself actually lives in this taxonomy; 'engage with "
              "stakeholders' keeps its own real category regardless."),
    dict(name="Getting Started with Cisco Packet Tracer", provider="Cisco Networking Academy",
         skill_category="Networking",
         subcategory="IT/Software - IT Infrastructure & Networks", skill_terms=["Cisco"],
         note="DEVIATION FLAGGED: matched via the course NAME ('Cisco Packet Tracer'), not "
              "the generic 'Networking' skill_category text - Cisco is an exact, unambiguous, "
              "high-confidence match, materially better than leaving this unmapped like the "
              "other bare-'Networking' courses (#13). Doing this only because the course "
              "title itself names the tool directly, not as a general practice of reading "
              "course names."),
    dict(name="Cybersecurity", provider="Tech Mahindra Foundation", skill_category="Cybersecurity",
         subcategory="IT/Software - Cybersecurity", skill_terms=["cybersecurity"],
         note="Clean alias exact match: cyber security."),
    dict(name="Project Management with Zoho", provider="Reliance Foundation Skilling Academy",
         skill_category="Project Management",
         subcategory="IT/Software - Software Development", skill_terms=["project management"],
         note="Clean canonical exact match: project management (this taxonomy places project "
              "management under Software Development, not a separate Transversal bucket)."),
]

assert len(COURSES) == 20

# ---------------------------------------------------------------------------
# 1. ID NAMESPACE - flagged deviation from the literal instruction
# ---------------------------------------------------------------------------
NEW_IDS = [f"MANUAL_{i:04d}" for i in range(1, len(COURSES) + 1)]

report_lines = []


def log(s=""):
    print(s)
    report_lines.append(s)


log("=" * 78)
log("T7 SUPPLEMENT - 20 manually-sourced courses")
log("=" * 78)
log("\n[ID NAMESPACE] courses.csv 'id' holds real external NPTEL catalogue numbers.")
log("Continuing that numeric sequence for non-NPTEL courses would mint IDs that look")
log("like genuine NPTEL IDs. Using a separate string namespace instead: MANUAL_0001..MANUAL_0020.")
log("This is a deliberate deviation from the literal 'continue the sequence' instruction.")

# ---------------------------------------------------------------------------
# 1b. Resolve each course's skill_terms against the LIVE taxonomy, every run
#     (see module docstring - this replaced hardcoded skill_id constants
#     after T8's --reset rebuild proved those unsafe across a real rebuild).
# ---------------------------------------------------------------------------
skills_ref = pd.read_csv(PROCESSED / "skills.csv")
skills_ref = skills_ref[skills_ref["status"] == "active"]
aliases_ref = pd.read_csv(PROCESSED / "skill_aliases.csv")

canon_index = {str(n).strip().lower(): sid for sid, n in zip(skills_ref["skill_id"], skills_ref["canonical_name"])}
alias_index = {}
for sid, al in zip(aliases_ref["skill_id"], aliases_ref["alias"]):
    alias_index.setdefault(str(al).strip().lower(), []).append(sid)


def resolve_term(term: str):
    """canonical exact match wins; else alias exact match (first, if unambiguous).
    Returns (skill_id, canonical_name, how) or (None, None, reason) if it no
    longer resolves - loud WARNING, never a guess."""
    key = term.strip().lower()
    if key in canon_index:
        sid = canon_index[key]
        canon = skills_ref.loc[skills_ref["skill_id"] == sid, "canonical_name"].iloc[0]
        return sid, canon, "canonical_exact"
    if key in alias_index:
        candidates = set(alias_index[key])
        if len(candidates) == 1:
            sid = candidates.pop()
            canon = skills_ref.loc[skills_ref["skill_id"] == sid, "canonical_name"].iloc[0]
            return sid, canon, "alias_exact"
        else:
            return None, None, f"AMBIGUOUS: alias {term!r} now maps to {len(candidates)} different skill_ids {sorted(candidates)} - was unambiguous when this mapping was built"
    return None, None, f"NOT FOUND: {term!r} no longer matches any canonical_name or alias in the current taxonomy"


resolution_warnings = []
for c in COURSES:
    resolved = []
    for term in c["skill_terms"]:
        sid, canon, how = resolve_term(term)
        if sid is None:
            resolution_warnings.append((c["name"], term, how))
        else:
            resolved.append((sid, canon, how))
    c["_resolved"] = resolved

if resolution_warnings:
    log(f"\n[WARNING] {len(resolution_warnings)} skill_term(s) that this mapping expects no longer "
        f"resolve against the current taxonomy - taxonomy scope has drifted since this mapping was "
        f"written. These are DROPPED (not guessed at), same as a genuinely-unmapped course:")
    for cname, term, reason in resolution_warnings:
        log(f"  - {cname!r}: term {term!r} - {reason}")
else:
    log(f"\n[OK] All {sum(len(c['skill_terms']) for c in COURSES)} skill_terms across the 20 courses "
        f"resolved cleanly against the current taxonomy.")

# ---------------------------------------------------------------------------
# 2. courses.csv - append the 20 rows, add source + needs_manual_url to ALL
#
# IDEMPOTENCY: strip any manual_supplement rows already present before
# appending fresh ones. Without this, re-running this script against its
# OWN prior output (e.g. `t8_pipeline.py --from T7supp_manual_courses` to
# resume mid-pipeline) silently double-appends - courses.csv creeps to 86,
# 106, 126 rows on repeated runs instead of staying at 66. Caught exactly
# that way while testing T8's --from flag.
# ---------------------------------------------------------------------------
courses = pd.read_csv(PROCESSED / "courses.csv")
courses["id"] = courses["id"].astype(str)          # unify dtype before concat with MANUAL_ ids
n_before_strip = len(courses)
courses = courses[courses.get("source", pd.Series(dtype=str)) != "manual_supplement_2026"] \
    if "source" in courses.columns else courses
if len(courses) < n_before_strip:
    log(f"[IDEMPOTENT] Found {n_before_strip - len(courses)} manual_supplement row(s) already in "
        f"courses.csv from a prior run - stripped before re-appending, so re-running this script "
        f"never double-adds.")
courses["source"] = "NPTEL"
courses["needs_manual_url"] = courses["source_url"].isna()

new_rows = []
for cid, c in zip(NEW_IDS, COURSES):
    new_rows.append(dict(
        id=cid,
        provider=c["provider"],
        name=c["name"],
        subcategory=c["subcategory"] if c["subcategory"] else "UNMAPPED",
        level=pd.NA,
        duration_weeks=pd.NA,
        credits=pd.NA,
        source_url=pd.NA,
        source="manual_supplement_2026",
        needs_manual_url=True,
    ))
new_courses_df = pd.DataFrame(new_rows)

courses_out = pd.concat([courses, new_courses_df], ignore_index=True)
courses_out.to_csv(PROCESSED / "courses.csv", index=False)

log(f"\n[courses.csv] {len(courses)} existing (source=NPTEL) + {len(new_courses_df)} new "
    f"(source=manual_supplement_2026) = {len(courses_out)} total rows written.")
log(f"needs_manual_url=True: {int(courses_out['needs_manual_url'].sum())} rows "
    f"(all 20 new ones - none of the existing 46 NPTEL rows were missing a source_url).")
n_unmapped_subcat = (new_courses_df["subcategory"] == "UNMAPPED").sum()
log(f"subcategory=UNMAPPED: {n_unmapped_subcat} of the 20 new rows (flagged, not forced).")

# ---------------------------------------------------------------------------
# 3. course_skills.csv - manual_supplement rows, confidence=0.75
# ---------------------------------------------------------------------------
cs = pd.read_csv(PROCESSED / "course_skills.csv")
cs["course_id"] = cs["course_id"].astype(str)
n_cs_before_strip = len(cs)
cs = cs[cs["coverage_level"] != "manual_supplement"]
if len(cs) < n_cs_before_strip:
    log(f"[IDEMPOTENT] Found {n_cs_before_strip - len(cs)} manual_supplement row(s) already in "
        f"course_skills.csv from a prior run - stripped before re-appending.")

new_cs_rows = []
unmapped_courses = []
for cid, c in zip(NEW_IDS, COURSES):
    if not c["_resolved"]:
        unmapped_courses.append((cid, c["name"], c["skill_category"]))
        continue
    for sid, canon, how in c["_resolved"]:
        new_cs_rows.append(dict(course_id=cid, skill_id=sid,
                                 coverage_level="manual_supplement", confidence=0.75))
new_cs_df = pd.DataFrame(new_cs_rows).drop_duplicates(["course_id", "skill_id"])
cs_out = pd.concat([cs, new_cs_df], ignore_index=True)
cs_out.to_csv(PROCESSED / "course_skills.csv", index=False)

log(f"\n[course_skills.csv] {len(new_cs_df)} new rows added (coverage_level=manual_supplement, "
    f"confidence=0.75) -> {len(cs_out)} total rows.")
log(f"\n[NOT TAGGED - reported per your instruction, not force-matched] "
    f"{len(unmapped_courses)} of the 20 courses got ZERO skill_id (their skill_category text "
    f"had no clean match in the 642-skill taxonomy):")
for cid, name, cat in unmapped_courses:
    log(f"  - {cid}  {name!r}  (skill_category: {cat!r})")

log("\n[Per-course mapping detail]")
for cid, c in zip(NEW_IDS, COURSES):
    log(f"\n{cid}  {c['name']}  ({c['provider']})")
    log(f"  skill_category as given : {c['skill_category']!r}")
    log(f"  subcategory assigned    : {c['subcategory'] or 'UNMAPPED'}")
    tagged = [f"{sid} ({canon!r}, {how})" for sid, canon, how in c["_resolved"]]
    log(f"  skill_id(s) tagged      : {tagged or '(none)'}")
    log(f"  note                    : {c['note']}")

# ---------------------------------------------------------------------------
# 4. Recompute training_gap.csv against the full course set
# ---------------------------------------------------------------------------
demand = pd.read_csv(PROCESSED / "skill_demand_history.csv")

demand_tier = (
    demand.groupby("skill_id")["strength_tier"]
    .apply(lambda s: "HIGH" if (s == "HIGH").any() else ("MEDIUM" if (s == "MEDIUM").any() else "OTHER"))
    .reset_index()
    .rename(columns={"strength_tier": "demand_strength_tier"})
)
demand_tier = demand_tier[demand_tier["demand_strength_tier"].isin(["HIGH", "MEDIUM"])]

course_counts = cs_out.groupby("skill_id")["course_id"].nunique().reset_index(name="course_count")

gap = demand_tier.merge(course_counts, on="skill_id", how="left")
gap["course_count"] = gap["course_count"].fillna(0).astype(int)
gap["gap_flag"] = gap["course_count"] == 0
gap = gap.sort_values(["demand_strength_tier", "skill_id"], ascending=[False, True])
gap.to_csv(PROCESSED / "training_gap.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Before/after comparison
# ---------------------------------------------------------------------------
prior_gap_path = PROCESSED / "training_gap_PRE_SUPPLEMENT_BACKUP.csv"
prior_gap = pd.read_csv(prior_gap_path) if prior_gap_path.exists() else None

log("\n" + "=" * 78)
log("STEP 4: GAP ANALYSIS - BEFORE vs AFTER the 20 manual courses")
log("=" * 78)

n_total = len(gap)
n_gapped_after = int(gap["gap_flag"].sum())
n_covered_after = n_total - n_gapped_after
log(f"\nAFTER  ({len(courses_out)} courses, {len(courses)} NPTEL + {len(new_courses_df)} manual_supplement):")
log(f"  {n_total} HIGH/MEDIUM demand skills total")
log(f"  {n_gapped_after} gapped ({n_gapped_after/n_total*100:.1f}%)")
log(f"  {n_covered_after} covered ({n_covered_after/n_total*100:.1f}%)")

if prior_gap is not None:
    n_before_gapped = int(prior_gap["gap_flag"].sum())
    n_before_total = len(prior_gap)
    log(f"\nBEFORE (NPTEL-only baseline, from {prior_gap_path.name}): "
        f"{n_before_gapped}/{n_before_total} gapped ({n_before_gapped/n_before_total*100:.1f}%)")
    moved = n_before_gapped - n_gapped_after
    log(f"  -> {moved} skill(s) moved from gapped to covered after adding the 20 manual courses "
        f"({moved}/{n_before_total} = {moved/n_before_total*100:.1f} percentage points of the total "
        f"HIGH/MEDIUM-demand skill space).")
else:
    log(f"\n(No {prior_gap_path.name} present this run - before/after comparison skipped. "
        f"Run t7_course_alignment.py alone first and copy training_gap.csv to that filename "
        f"if you want a before/after delta.)")

if prior_gap_path.exists():
    prior_gap_path.unlink()  # temp comparison snapshot, not a real pipeline deliverable

# named skills to specifically confirm - resolved by NAME, not hardcoded id,
# for the same reason as the course mapping above
watch_terms = {
    "DevOps": "DevOps", "Jenkins": "Jenkins", "Cisco": "Cisco",
    "JavaScript": "JavaScript", "PHP": "PHP", "C#": "C#",
    "Visual Basic": "Visual Basic", "risk management": "risk management",
}
log("\n[Named skills - explicit confirmation requested]")
for label, term in watch_terms.items():
    sid, canon, how = resolve_term(term)
    if sid is None:
        log(f"  {label:16s}: could not resolve ({how})")
        continue
    row = gap[gap["skill_id"] == sid]
    if row.empty:
        log(f"  {label:16s} ({sid} = {canon!r}): not in the HIGH/MEDIUM-demand skill set - N/A")
        continue
    r = row.iloc[0]
    status = "COVERED" if not r["gap_flag"] else "STILL GAPPED"
    log(f"  {label:16s} ({sid} = {canon!r}): demand={r['demand_strength_tier']}, "
        f"course_count={r['course_count']}  ->  {status}")

log(f"\nWrote courses.csv, course_skills.csv, training_gap.csv, "
    f"manual_course_supplement_report.txt")

(PROCESSED / "manual_course_supplement_report.txt").write_text("\n".join(report_lines))
