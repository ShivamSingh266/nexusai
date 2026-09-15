"""
T2 - ESCO Taxonomy Import
Builds skills.csv: a sector-filtered subset of canonical ESCO skills.

GENERAL BY DESIGN - nothing dataset-specific is hardcoded in this file:
  - Which ESCO release/folder to read, and where to write output, are CLI
    args, not paths baked into the script.
  - Sectors, keyword lists, per-sector caps, and the must-include overrides
    all live in an external JSON config, not in this code. Change scope
    (add a sector, retune keywords, point at ESCO v1.3.0) by editing JSON.
  - Every input file is checked for existence AND for the specific columns
    this script actually reads, before any processing starts. If ESCO ever
    renames/drops a column, you get one clear error naming the file and
    the missing column - not a KeyError 400 lines into a pandas traceback.
  - The transversal-skills file is optional: if it's missing (e.g. an ESCO
    release that ships it under a different filename, or you're pointed at
    a non-ESCO taxonomy that has no such collection), the script degrades
    to "no transversal bucket" with a warning instead of crashing.

USAGE:
  python t2_build_skills_taxonomy.py \
      --raw-dir /path/to/esco/csvs \
      --out-dir /path/to/output \
      --config /path/to/taxonomy_config.json

STRATEGY (two-tier - see taxonomy_config.json comments / chat history for
why this replaces naive label-only keyword matching):

  Tier A (primary, higher precision) - occupation-anchored:
      Match each sector's occupation_keywords against occupationLabel in
      the occupation-skill relations file. Pull every skill (essential +
      optional) ESCO already links to matched occupations.

  Tier B (supplementary) - direct skill-label match:
      Match each sector's skill_keywords against preferredLabel + altLabels
      in the skills file. Catches sector tools/tech not tied to one named
      occupation. Deliberately NOT matched against `description` - that
      false-positives heavily.

  Within a sector, ranking is (priority, -match_count):
      priority    : A-occupation/essential(0) > A-occupation/optional(1) > B-label(2)
      match_count : distinct occupations in this sector linking to the skill -
                    without this tiebreak, ties fall back to arbitrary row
                    order, and well-known skills can lose to obscure ones.
      must_include: force-included regardless of rank (still counts against
                    the cap) - at a tight per-sector cap, automatic ranking
                    does not reliably keep "obviously must-have" skills.

  Transversal skills are pulled out of every sector bucket and handled once
  as their own category - otherwise they flood every sector's list.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Schema contract: the exact columns this script reads from each input file.
# Checked up front so a schema change fails loudly and early, not silently
# mid-pipeline.
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "skills": ["conceptUri", "preferredLabel", "altLabels", "status", "modifiedDate"],
    "occupation_skill_relations": ["occupationUri", "occupationLabel", "relationType", "skillUri"],
    "transversal": ["conceptUri", "preferredLabel"],
}


def require_columns(df: pd.DataFrame, required: list[str], file_label: str, path: Path):
    missing = set(required) - set(df.columns)
    if missing:
        sys.exit(
            f"[FATAL] {file_label} ({path}) is missing expected column(s): {sorted(missing)}.\n"
            f"        Columns found: {list(df.columns)}\n"
            f"        Either the input file's schema changed, or REQUIRED_COLUMNS in this "
            f"script needs updating to match a new source format."
        )


def load_csv(raw_dir: Path, filename: str, file_key: str, required: bool = True) -> pd.DataFrame | None:
    path = raw_dir / filename
    if not path.exists():
        if required:
            sys.exit(f"[FATAL] Required file not found: {path}\n"
                      f"        Check --raw-dir, or update files.{file_key} in your config JSON "
                      f"if this file has been renamed in a newer release.")
        print(f"[WARN] Optional file not found: {path} - continuing without it.")
        return None
    df = pd.read_csv(path)
    require_columns(df, REQUIRED_COLUMNS[file_key], file_key, path)
    return df


def normalize_name(s) -> str:
    """Same rule as T4's normalize_text() (t4_normalization/normalize.py) -
    kept identical on purpose so a persisted normalized_name here always
    matches what T4 computes on the fly. Persisted as a real column because
    Member 3 asked for one, rather than requiring every consumer to
    replicate this logic themselves."""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def word_match(keywords: list[str], text) -> bool:
    if pd.isna(text) or not keywords:
        return False
    text = str(text).lower()
    return any(re.search(rf"\b{re.escape(kw.lower())}\b", text) for kw in keywords)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", required=True, type=Path, help="Directory containing the ESCO (or equivalent) CSV files")
    ap.add_argument("--out-dir", required=True, type=Path, help="Directory to write skills.csv / skills_needs_review.csv")
    ap.add_argument("--config", required=True, type=Path, help="Path to taxonomy_config.json")
    args = ap.parse_args()

    if not args.config.exists():
        sys.exit(f"[FATAL] Config file not found: {args.config}")
    cfg = json.loads(args.config.read_text())

    for key in ("sectors", "files", "taxonomy_version", "min_per_sector", "max_per_sector",
                "total_min", "total_max"):
        if key not in cfg:
            sys.exit(f"[FATAL] Config is missing required key: {key!r}")

    SECTORS = cfg["sectors"]
    if not SECTORS:
        sys.exit("[FATAL] Config has no sectors defined - nothing to filter.")
    MUST_INCLUDE = cfg.get("must_include", {})
    MIN_PER_SECTOR = cfg["min_per_sector"]
    MAX_PER_SECTOR = cfg["max_per_sector"]
    TOTAL_MIN = cfg["total_min"]
    TOTAL_MAX = cfg["total_max"]
    INCLUDE_TRANSVERSAL = cfg.get("include_transversal", False)
    TRANSVERSAL_SKILLS = cfg.get("transversal_skills")  # None = include all
    TAXONOMY_VERSION = cfg["taxonomy_version"]

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # LOAD + VALIDATE
    # -----------------------------------------------------------------

    files_cfg = cfg["files"]
    skills = load_csv(args.raw_dir, files_cfg["skills"], "skills", required=True)
    occ_rel = load_csv(args.raw_dir, files_cfg["occupation_skill_relations"], "occupation_skill_relations", required=True)
    transversal = None
    if INCLUDE_TRANSVERSAL:
        transversal = load_csv(args.raw_dir, files_cfg.get("transversal", "transversalSkillsCollection_en.csv"),
                                "transversal", required=False)
        if transversal is None:
            print("[WARN] include_transversal=true but the transversal file wasn't found - disabling that bucket.")
            INCLUDE_TRANSVERSAL = False

    if "status" in skills.columns:
        released = skills["status"] == "released"
        if released.sum() == 0:
            print("[WARN] No rows have status=='released' - 'status' values may differ in this release; "
                  "not filtering on it.")
        else:
            skills = skills[released].copy()

    # de-duplicate on the concept URI, keeping the most recently modified copy.
    # (Checked against ESCO v1.2.1: 21 exact-duplicate conceptUri pairs existed,
    # differing only in modifiedDate. Left undeduped, these mint two different
    # skill_ids for the same skill and corrupt every downstream join. This
    # dedup is defensive for ANY release, not a one-off patch.)
    dupes = skills["conceptUri"].duplicated().sum()
    if dupes:
        print(f"[INFO] {dupes} duplicate conceptUri row(s) in the skills file - keeping most recently modified copy of each.")
    skills = (skills.sort_values("modifiedDate", ascending=False)
                     .drop_duplicates("conceptUri", keep="first"))

    transversal_uris = set(transversal["conceptUri"]) if transversal is not None else set()
    skills_by_uri = skills.set_index("conceptUri")
    label_to_uri = skills.reset_index(drop=True).drop_duplicates("preferredLabel", keep="first").set_index("preferredLabel")["conceptUri"]

    # -----------------------------------------------------------------
    # TIER A: occupation-anchored pull
    # -----------------------------------------------------------------

    matches = []
    for sector, sec_cfg in SECTORS.items():
        occ_kw = sec_cfg.get("occupation_keywords", [])
        if not occ_kw:
            continue
        mask = occ_rel["occupationLabel"].apply(lambda t: word_match(occ_kw, t))
        for _, row in occ_rel[mask].iterrows():
            uri = row["skillUri"]
            if uri in transversal_uris or uri not in skills_by_uri.index:
                continue
            matches.append({"skillUri": uri, "sector": sector, "tier": "A-occupation",
                             "relationType": row["relationType"], "matchedOn": row["occupationLabel"]})

    # -----------------------------------------------------------------
    # TIER B: direct skill-label match
    # -----------------------------------------------------------------

    for sector, sec_cfg in SECTORS.items():
        skill_kw = sec_cfg.get("skill_keywords", [])
        if not skill_kw:
            continue
        label_hit = skills["preferredLabel"].apply(lambda t: word_match(skill_kw, t))
        alt_hit = skills["altLabels"].apply(lambda t: word_match(skill_kw, t))
        for _, row in skills[label_hit | alt_hit].iterrows():
            uri = row["conceptUri"]
            if uri in transversal_uris:
                continue
            matches.append({"skillUri": uri, "sector": sector, "tier": "B-label",
                             "relationType": None, "matchedOn": row["preferredLabel"]})

    if not matches:
        sys.exit("[FATAL] No skills matched any sector's keywords at all. Check occupationLabel/"
                  "preferredLabel spellings in your config against the actual data (e.g. print "
                  "occ_rel['occupationLabel'].unique() and compare).")

    match_df = pd.DataFrame(matches)

    def rank(r):
        if r["tier"] == "A-occupation" and r["relationType"] == "essential":
            return 0
        if r["tier"] == "A-occupation" and r["relationType"] == "optional":
            return 1
        return 2

    match_df["priority"] = match_df.apply(rank, axis=1)
    match_df["match_count"] = match_df.groupby(["sector", "skillUri"])["skillUri"].transform("count")

    # -----------------------------------------------------------------
    # DEDUPE + CAP per sector (+ must-include overrides)
    # -----------------------------------------------------------------

    review_rows = []
    final_rows = []

    # Iterate sectors in the CONFIG's own declared order, not pandas'
    # default alphabetical groupby order. A skill matching more than one
    # sector's keywords is assigned to whichever sector is processed FIRST
    # (final_df.drop_duplicates("skillUri", keep="first") below) - alphabetical
    # order made that essentially arbitrary (Cybersecurity always won ties
    # simply because "C" sorts first), not a real priority decision.
    for sector in SECTORS.keys():
        group = match_df[match_df["sector"] == sector]
        if group.empty:
            continue
        group = (group.sort_values(["priority", "match_count"], ascending=[True, False])
                       .drop_duplicates("skillUri", keep="first"))

        must_uris = []
        for label in MUST_INCLUDE.get(sector, []):
            uri = label_to_uri.get(label)
            if uri is None:
                print(f"[WARN] must_include label {label!r} for sector {sector!r} not found in the "
                      f"skills file - check spelling against preferredLabel.")
                continue
            must_uris.append(uri)

        must_rows = group[group["skillUri"].isin(must_uris)]
        missing = set(must_uris) - set(must_rows["skillUri"])
        if missing:
            extra = skills.loc[skills["conceptUri"].isin(missing), ["conceptUri", "preferredLabel"]]
            extra_rows = pd.DataFrame([{"skillUri": u, "sector": sector, "tier": "must-include",
                                         "relationType": None, "matchedOn": "manual override",
                                         "priority": -1, "match_count": 0} for u in extra["conceptUri"]])
            must_rows = pd.concat([must_rows, extra_rows], ignore_index=True)

        rest = group[~group["skillUri"].isin(must_uris)]
        budget_left = max(MAX_PER_SECTOR - len(must_rows), 0)
        kept = pd.concat([must_rows, rest.head(budget_left)], ignore_index=True)
        overflow = rest.iloc[budget_left:]

        if len(kept) < MIN_PER_SECTOR:
            print(f"[WARN] {sector}: only {len(kept)} skills matched, below the configured "
                  f"min_per_sector={MIN_PER_SECTOR}. Widen this sector's keywords in the config.")
        if len(group) > MAX_PER_SECTOR:
            print(f"[INFO] {sector}: {len(group)} unique candidates matched, capped to {MAX_PER_SECTOR} "
                  f"({len(overflow)} pushed to skills_needs_review.csv for manual promotion).")

        for _, r in kept.iterrows():
            final_rows.append({"skillUri": r["skillUri"], "category": sector,
                                "tier": r["tier"], "relationType": r["relationType"]})
            if r["tier"] == "B-label" or r["relationType"] == "optional":
                review_rows.append({**r.to_dict(), "reason": "weak signal (label-only or optional-relation)"})
        for _, r in overflow.iterrows():
            review_rows.append({**r.to_dict(), "reason": "cut by per-sector cap - candidate for manual promotion"})

    final_df = pd.DataFrame(final_rows).drop_duplicates("skillUri", keep="first")

    # must_include GUARANTEE, part 2: config-order iteration (above) makes
    # collision resolution deterministic, but a must_include skill can still
    # lose a tie to an EARLIER-in-config-order sector it also happens to
    # match (e.g. "operating systems" is must_include for IT Infrastructure
    # & Networks, but also independently matches Cybersecurity, which is
    # earlier in the config). must_include should mean "categorized under
    # THIS sector", not just "exists somewhere" - so it's enforced here
    # unconditionally, overriding whatever the collision resolution picked.
    # Found by auditing all 19 must_include skills against their actual
    # final category: 4 were wrong before this fix (Python, Java, JavaScript
    # -> landed outside Software Development; operating systems -> landed in
    # Cybersecurity instead of IT Infrastructure & Networks).
    n_corrected = 0
    for sector, labels in MUST_INCLUDE.items():
        for label in labels:
            uri = label_to_uri.get(label)
            if uri is None:
                continue
            mask = final_df["skillUri"] == uri
            if mask.any() and (final_df.loc[mask, "category"] != sector).any():
                old_cat = final_df.loc[mask, "category"].iloc[0]
                final_df.loc[mask, "category"] = sector
                n_corrected += 1
                print(f"[MUST-INCLUDE FIX] {label!r}: was categorized {old_cat!r}, forced to declared "
                      f"sector {sector!r}")
    if n_corrected:
        print(f"[MUST-INCLUDE FIX] {n_corrected} must_include skill(s) had their category corrected "
              f"to match their config declaration.")

    skill_to_sectors = match_df.groupby("skillUri")["sector"].agg(lambda s: set(s))
    cross_sector_uris = {uri for uri, secs in skill_to_sectors.items() if len(secs) > 1}
    # sorted(): iterating the raw set here is PYTHONHASHSEED-dependent (randomized per
    # process for strings), which produced a DIFFERENT skills_needs_review.csv row order
    # on every from-scratch run even though the row CONTENTS were identical - caught by
    # T8's --reset x2 determinism check (byte-identical output was the bar, not just
    # "same rows in some order"). This is diagnostic-only output (doesn't feed any
    # downstream stage), but it should still rebuild byte-for-byte like everything else.
    for uri in sorted(cross_sector_uris):
        kept_sector = final_df.loc[final_df["skillUri"] == uri, "category"]
        kept_sector = kept_sector.iloc[0] if len(kept_sector) else None
        other_sectors = skill_to_sectors[uri] - {kept_sector}
        if other_sectors:
            label = skills_by_uri.loc[uri, "preferredLabel"] if uri in skills_by_uri.index else uri
            review_rows.append({"skillUri": uri, "sector": ",".join(sorted(other_sectors)),
                                 "tier": "cross-sector", "relationType": None, "matchedOn": label,
                                 "reason": f"also matched {sorted(other_sectors)}, kept under '{kept_sector}'"})

    # -----------------------------------------------------------------
    # TRANSVERSAL bucket
    # -----------------------------------------------------------------

    if INCLUDE_TRANSVERSAL:
        transversal[["conceptUri", "preferredLabel"]].to_csv(args.out_dir / "transversal_candidates.csv", index=False)
        chosen_uris = TRANSVERSAL_SKILLS if TRANSVERSAL_SKILLS else list(transversal_uris)
        tv_rows = pd.DataFrame([
            {"skillUri": uri, "category": "Transversal", "tier": "curated-collection", "relationType": None}
            for uri in chosen_uris
        ])
        final_df = pd.concat([final_df, tv_rows], ignore_index=True)

    # -----------------------------------------------------------------
    # BUILD skills.csv
    # -----------------------------------------------------------------

    final_df = final_df.merge(skills[["conceptUri", "preferredLabel"]],
                               left_on="skillUri", right_on="conceptUri", how="left")
    final_df = final_df.sort_values(["category", "preferredLabel"]).reset_index(drop=True)

    skills_out = final_df[["preferredLabel", "category", "skillUri"]].rename(
        columns={"preferredLabel": "canonical_name", "skillUri": "esco_uri"}
    )
    skills_out["source"] = "ESCO"
    skills_out["taxonomy_version"] = TAXONOMY_VERSION
    skills_out["confidence"] = 1.0
    skills_out["indian_alignment"] = pd.NA
    skills_out["nsqf_alignment"] = pd.NA
    skills_out["status"] = "active"
    skills_out["normalized_name"] = skills_out["canonical_name"].apply(normalize_name)

    # ---------------------------------------------------------------------
    # STABLE ID ASSIGNMENT - keyed on esco_uri, not row position.
    #
    # Previously, skill_id was `SKILL_{i+1:04d}` for i in range(len(final_df))
    # - purely positional. Every rebuild (this taxonomy has been widened 3x
    # already: 209 -> 488 -> 642 skills) reassigned EVERY skill_id from
    # scratch, because row order shifts whenever the candidate set size or
    # sort changes. Any foreign key another team member built against these
    # IDs (Member 3's JobSkill/ApplicantSkill) would silently point at the
    # wrong skill after the next rebuild. Fixed: if a previous skills.csv
    # exists at the output path, esco_uri -> skill_id is carried forward.
    # Only a genuinely NEW esco_uri gets a newly minted ID, continuing the
    # numbering from the highest ID ever issued (retired IDs are never
    # reused, same as a normal DB auto-increment column). A previously
    # active esco_uri that drops out of this run's candidate set is not
    # deleted - it's kept with status='deprecated', so an existing FK
    # reference resolves to a real (marked-inactive) row instead of nothing.
    # ---------------------------------------------------------------------

    out_path = args.out_dir / "skills.csv"
    previous_map = {}       # esco_uri -> skill_id
    previous_rows = {}      # esco_uri -> full previous row (dict), for deprecation carry-forward
    max_existing_num = 0
    if out_path.exists():
        prev = pd.read_csv(out_path)
        if "esco_uri" in prev.columns and "skill_id" in prev.columns:
            for _, r in prev.iterrows():
                previous_map[r["esco_uri"]] = r["skill_id"]
                previous_rows[r["esco_uri"]] = r.to_dict()
                m = re.match(r"SKILL_(\d+)$", str(r["skill_id"]))
                if m:
                    max_existing_num = max(max_existing_num, int(m.group(1)))
        else:
            print(f"[WARN] existing {out_path.name} has no esco_uri/skill_id columns - cannot carry "
                  f"forward stable IDs, starting fresh (this should only happen once, on first migration "
                  f"to stable IDs).")

    next_num = max_existing_num
    assigned_ids = []
    for uri in skills_out["esco_uri"]:
        if uri in previous_map:
            assigned_ids.append(previous_map[uri])
        else:
            next_num += 1
            assigned_ids.append(f"SKILL_{next_num:04d}")
    skills_out["skill_id"] = assigned_ids

    n_reused = sum(1 for u in skills_out["esco_uri"] if u in previous_map)
    n_new = len(skills_out) - n_reused
    print(f"\n[ID STABILITY] {n_reused} skill_id(s) carried forward unchanged from the previous "
          f"skills.csv, {n_new} newly minted (next available: SKILL_{next_num:04d})")

    # deprecate: esco_uris present in the PREVIOUS file but absent from this run
    current_uris = set(skills_out["esco_uri"])
    deprecated_uris = set(previous_map) - current_uris
    if deprecated_uris:
        dep_rows = []
        for uri in deprecated_uris:
            row = dict(previous_rows[uri])
            row["status"] = "deprecated"
            dep_rows.append(row)
        dep_df = pd.DataFrame(dep_rows)
        print(f"[ID STABILITY] {len(dep_df)} previously active skill(s) not in this run's candidate "
              f"set - kept as status='deprecated' (not deleted): {sorted(deprecated_uris)[:5]}"
              f"{'...' if len(deprecated_uris) > 5 else ''}")
        skills_out = pd.concat([skills_out, dep_df], ignore_index=True)

    skills_out = skills_out[["skill_id", "canonical_name", "normalized_name", "category", "source",
                              "taxonomy_version", "confidence", "indian_alignment", "nsqf_alignment",
                              "status", "esco_uri"]]
    skills_out = skills_out.sort_values(["status", "category", "canonical_name"], ascending=[False, True, True])

    skills_out.to_csv(out_path, index=False)

    review_df = pd.DataFrame(review_rows)
    if not review_df.empty:
        review_df.to_csv(args.out_dir / "skills_needs_review.csv", index=False)

    sector_total = (skills_out["category"] != "Transversal").sum()
    print(f"\nskills.csv: {len(skills_out)} rows -> {args.out_dir / 'skills.csv'} "
          f"({sector_total} sector skills + {len(skills_out) - sector_total} transversal)")
    print(skills_out["category"].value_counts())
    if sector_total < TOTAL_MIN:
        print(f"\n[WARN] sector total {sector_total} is BELOW target range {TOTAL_MIN}-{TOTAL_MAX}.")
    elif sector_total > TOTAL_MAX:
        print(f"\n[WARN] sector total {sector_total} is ABOVE target range {TOTAL_MIN}-{TOTAL_MAX}.")
    if not review_df.empty:
        print(f"\nskills_needs_review.csv: {len(review_df)} flagged rows -> {args.out_dir / 'skills_needs_review.csv'}")


if __name__ == "__main__":
    main()
