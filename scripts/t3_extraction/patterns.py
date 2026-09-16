"""
T3 - Skill Extraction: shared pattern loading.

Loads skills.csv + skill_aliases.csv (from Task 2) into a phrase -> skill_id
lookup used by BOTH matcher backends (spaCy and the dependency-free
fallback), so pattern loading logic isn't duplicated/able to drift between
the two.
"""

from pathlib import Path

import pandas as pd


def load_phrase_to_skill(skills_csv: Path, aliases_csv: Path, dropped_out: Path = None) -> dict:
    """
    Builds phrase -> skill_id. A phrase genuinely registered against more
    than one skill_id (ESCO's own altLabels do this - e.g. "ICT security"
    is an altLabel for both "ICT safety" and "cyber security") is DROPPED
    from the returned dict entirely, not resolved by first-registration-
    wins - guessing which of two skills a bare phrase means is worse than
    not matching it at all, and T3 has no context to disambiguate with.
    If dropped_out is given, the full ambiguous-phrase list (phrase -> all
    candidate skill_ids) is written there for manual review/resolution.
    """
    skills = pd.read_csv(skills_csv)
    aliases = pd.read_csv(aliases_csv)

    for col in ("skill_id", "canonical_name"):
        if col not in skills.columns:
            raise ValueError(f"{skills_csv} is missing expected column {col!r}")
    for col in ("skill_id", "alias"):
        if col not in aliases.columns:
            raise ValueError(f"{aliases_csv} is missing expected column {col!r}")

    occurrences = {}  # phrase -> set of skill_ids
    for _, row in skills.iterrows():
        phrase = str(row["canonical_name"]).strip()
        occurrences.setdefault(phrase, set()).add(row["skill_id"])
    for _, row in aliases.iterrows():
        phrase = str(row["alias"]).strip()
        if not phrase:
            continue
        occurrences.setdefault(phrase, set()).add(row["skill_id"])

    ambiguous = {p: ids for p, ids in occurrences.items() if len(ids) > 1}
    phrase_to_skill = {p: next(iter(ids)) for p, ids in occurrences.items() if len(ids) == 1}

    if ambiguous:
        print(f"[WARN] {len(ambiguous)} phrase(s) map to more than one skill_id - dropped from "
              f"matching entirely (not guessed): {list(ambiguous.items())[:5]}"
              f"{' ...' if len(ambiguous) > 5 else ''}")
        if dropped_out:
            rows = [{"phrase": p, "candidate_skill_ids": ",".join(sorted(ids))} for p, ids in ambiguous.items()]
            pd.DataFrame(rows).to_csv(dropped_out, index=False)
            print(f"  full list -> {dropped_out}")

    return phrase_to_skill
