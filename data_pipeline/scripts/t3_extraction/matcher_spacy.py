"""
T3 - Skill Extraction: spaCy matcher backend (PRIMARY - use this in your
real dev environment; requires `pip install spacy`, no model download
needed since PhraseMatcher/EntityRuler are rule-based, not statistical).

NOT executed in the sandbox this was written in (spaCy isn't installable
there - see chat). Structurally mirrors matcher_fallback.py's interface,
which WAS run against your real data, so swap the import in
t3_run_extraction.py once spaCy is available locally and the wiring script
does not change.

WHY PhraseMatcher for the main vocabulary:
  skills.csv/skill_aliases.csv are static phrase lists - exactly what
  PhraseMatcher is for. It matches on token sequences (not substrings),
  so "machine learning" as a 2-token pattern won't spuriously fire just
  because "machine" appears - and with attr="LOWER" it matches
  case-insensitively without you having to lowercase the document (so
  span.text below is the ORIGINAL-cased mention, i.e. real evidence).

WHEN YOU'D WANT EntityRuler INSTEAD (or alongside):
  PhraseMatcher can only match an exact, fixed token sequence per pattern -
  it has no concept of "optional token" or "any digit sequence here".
  EntityRuler (built on the same Matcher engine as PhraseMatcher, but
  accepting token-attribute patterns, not just phrases) can, e.g.:

      Python (computer programming) as ESCO has it, PLUS any version
      suffix your text actually contains ("Python 3", "Python 3.9",
      "Python2"), as ONE pattern instead of enumerating every version
      string as a separate alias:

          [{"LOWER": "python"},
           {"TEXT": {"REGEX": r"^\\d+(\\.\\d+)*$"}, "OP": "?"}]

  Use EntityRuler when a skill mention has a variable/optional token
  (version numbers, "Level 1/2/3", "certified" as an optional prefix) that
  you'd otherwise have to hand-enumerate as dozens of literal aliases.
  Don't reach for it as a blanket replacement for PhraseMatcher - most of
  your 209 skills are fixed phrases with no variable component, and
  PhraseMatcher is faster and simpler for those.

Overlap policy: spaCy's own spacy.util.filter_spans does exactly the
"prefer longest match" rule requested - no custom logic needed, unlike
the fallback backend which has to implement it by hand.
"""

from pathlib import Path

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from spacy.util import filter_spans

from patterns import load_phrase_to_skill


def build_matcher(skills_csv: Path, aliases_csv: Path, dropped_out: Path = None):
    nlp = spacy.blank("en")  # rule-based matching only - no need for a trained pipeline/model download
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")  # case-insensitive without lowercasing the doc

    phrase_to_skill = load_phrase_to_skill(skills_csv, aliases_csv, dropped_out=dropped_out)

    patterns_by_skill = {}
    for phrase, skill_id in phrase_to_skill.items():
        patterns_by_skill.setdefault(skill_id, []).append(phrase)

    for skill_id, phrases in patterns_by_skill.items():
        matcher.add(skill_id, [nlp.make_doc(p) for p in phrases])

    return nlp, matcher


def find_matches(nlp, matcher, text: str):
    """Returns list of (start_char, end_char, skill_id, mention_text)."""
    doc = nlp.make_doc(text)
    raw_matches = matcher(doc)

    spans = [Span(doc, start, end, label=nlp.vocab.strings[match_id])
             for match_id, start, end in raw_matches]
    spans = filter_spans(spans)  # longest match wins on overlap

    return [(span.start_char, span.end_char, span.label_, span.text) for span in spans]


# ---------------------------------------------------------------------------
# EntityRuler example: versioned-skill patterns, added as extra match
# sources for the handful of skills that actually have a version component
# in your retained taxonomy (check skills.csv/skill_aliases.csv for which
# ones - Python is the obvious one; most of your 209 skills have none).
# This runs as a SEPARATE small pass, not merged into the PhraseMatcher
# call above - keep the two match sets distinct in your output (a
# "match_method" field, e.g.) since EntityRuler patterns are hand-written
# per-skill and deserve a lower default trust than a straight ESCO alias
# hit until you've eyeballed a sample.
# ---------------------------------------------------------------------------

def build_version_ruler(nlp, version_patterns: dict):
    """
    version_patterns: {skill_id: [[{token pattern dicts}], ...]}
    Example:
        {"SKILL_0100": [[{"LOWER": "python"},
                          {"TEXT": {"REGEX": r"^\\d+(\\.\\d+)*$"}, "OP": "?"}]]}
    """
    ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": False})
    for skill_id, patterns in version_patterns.items():
        for pattern in patterns:
            ruler.add_patterns([{"label": skill_id, "pattern": pattern}])
    return ruler
