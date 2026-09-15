"""
T2 - ESCO Taxonomy Import (part 2)
Builds skill_aliases.csv for whatever is currently in skills.csv.

GENERAL BY DESIGN, same reasoning as t2_build_skills_taxonomy.py: paths and
the manual example-alias list are CLI/config, not hardcoded; the altLabels
column is checked for existence before use.

Source of aliases:
  1. The taxonomy source's own altLabels for each retained skill (checked
     against ESCO: newline-delimited within the field, e.g. "Python 3K\\n
     Python" for canonical "Python (computer programming)"). confidence = 1.0.
  2. A small set of manual example aliases, from config's "manual_aliases" -
     NOT a real alias list, just format examples. Real alias-mining is a
     separate manual pass.

USAGE:
  python t2_build_skill_aliases.py \
      --raw-dir /path/to/esco/csvs \
      --out-dir /path/to/output \
      --config /path/to/taxonomy_config.json
(Run t2_build_skills_taxonomy.py first - this reads its skills.csv output.)
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    args = ap.parse_args()

    skills_csv = args.out_dir / "skills.csv"
    if not skills_csv.exists():
        sys.exit(f"[FATAL] {skills_csv} not found - run t2_build_skills_taxonomy.py first.")
    skills_out = pd.read_csv(skills_csv)

    cfg = json.loads(args.config.read_text())
    skills_filename = cfg.get("files", {}).get("skills", "skills_en.csv")
    skills_path = args.raw_dir / skills_filename
    if not skills_path.exists():
        sys.exit(f"[FATAL] Skills source file not found: {skills_path}")

    skills_en = pd.read_csv(skills_path)
    for col in ("conceptUri", "preferredLabel"):
        if col not in skills_en.columns:
            sys.exit(f"[FATAL] {skills_path} is missing expected column {col!r}.")

    has_alt = "altLabels" in skills_en.columns
    if not has_alt:
        print(f"[WARN] {skills_path} has no 'altLabels' column - skipping ESCO-sourced aliases entirely, "
              f"only manual_aliases from config will be used. Check the file's exact column structure "
              f"if this is unexpected.")

    if "status" in skills_en.columns:
        skills_en = skills_en[skills_en["status"] == "released"].copy()
    if "modifiedDate" in skills_en.columns:
        skills_en = skills_en.sort_values("modifiedDate", ascending=False)
    skills_en = skills_en.drop_duplicates("conceptUri", keep="first")

    # ESCO's own altLabels sometimes register a bare, generic English word
    # as an alias for a transversal skill (e.g. "design" -> "think
    # creatively", found by inspecting a real false-positive match against
    # course data - see chat). These aren't ambiguous (they map to exactly
    # one skill_id) so load_phrase_to_skill's collision check won't catch
    # them - they're just too generic to serve as a reliable match cue on
    # their own. Configured blocklist, not a hardcoded guess.
    blocked = {b.strip().lower() for b in cfg.get("blocked_aliases", [])}
    n_blocked = 0

    alias_rows = []
    if has_alt:
        alt_by_uri = skills_en.set_index("conceptUri")["altLabels"]
        for _, row in skills_out.iterrows():
            raw_alt = alt_by_uri.get(row["esco_uri"])
            if pd.isna(raw_alt):
                continue
            for alt in str(raw_alt).split("\n"):
                alt = alt.strip()
                if not alt or alt.lower() == str(row["canonical_name"]).strip().lower():
                    continue
                if alt.lower() in blocked:
                    n_blocked += 1
                    continue
                alias_rows.append({"alias": alt, "skill_id": row["skill_id"], "confidence": 1.0})

    if n_blocked:
        print(f"[INFO] Dropped {n_blocked} blocked generic alias occurrence(s) (see blocked_aliases in config).")

    esco_alias_df = pd.DataFrame(alias_rows).drop_duplicates(["alias", "skill_id"]) if alias_rows else pd.DataFrame(columns=["alias", "skill_id", "confidence"])

    manual_rows = []
    for canonical, aliases in cfg.get("manual_aliases", {}).items():
        match = skills_out[skills_out["canonical_name"] == canonical]
        if match.empty:
            continue
        skill_id = match.iloc[0]["skill_id"]
        for alt in aliases:
            manual_rows.append({"alias": alt, "skill_id": skill_id, "confidence": 1.0})
    manual_alias_df = pd.DataFrame(manual_rows) if manual_rows else pd.DataFrame(columns=["alias", "skill_id", "confidence"])

    all_aliases = pd.concat([esco_alias_df, manual_alias_df], ignore_index=True)
    all_aliases = all_aliases.drop_duplicates(["alias", "skill_id"]).sort_values(["skill_id", "alias"])
    all_aliases.to_csv(args.out_dir / "skill_aliases.csv", index=False)

    print(f"skill_aliases.csv: {len(all_aliases)} rows -> {args.out_dir / 'skill_aliases.csv'}")
    print(f"  from source altLabels: {len(esco_alias_df)}")
    print(f"  manual examples:       {len(manual_alias_df)}")
    n_with_alias = all_aliases["skill_id"].nunique() if not all_aliases.empty else 0
    print(f"  {n_with_alias}/{len(skills_out)} retained skills have >=1 alias")


if __name__ == "__main__":
    main()
