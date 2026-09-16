"""
T3 - Skill Extraction: dependency-free matcher backend.

Same interface and matching semantics as matcher_spacy.py:
  - tokenize on word boundaries (regex, not spaCy's tokenizer - see the
    known-gap note at the bottom for where this differs)
  - case-insensitive matching without lowercasing the actual text
  - multi-word phrases match as contiguous token sequences, not substrings
  - overlapping matches resolved by longest-span-wins (same algorithm as
    spaCy's spacy.util.filter_spans: sort by span length descending, then
    by start position, greedily keep non-overlapping)

Exists for two reasons: (1) spaCy is not installable in the sandbox this
was developed in, so this is what actually produced this task's numbers
against your real data, and (2) it's a legitimate stdlib-only fallback if
`pip install spacy` eats hackathon time on a fresh machine - same call
signature as the spaCy backend, so switching is a one-line change in
t3_run_extraction.py, not a rewrite.
"""

import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"\w+(?:[+#]+)?|\S")  # keeps "C++"/"C#" as one token; else 1 char/symbol


def tokenize(text: str):
    """Returns list of (token_text, start_char, end_char)."""
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


class FallbackPhraseMatcher:
    def __init__(self, phrase_to_skill: dict):
        # index patterns by their first token (lowercased) so lookup during
        # matching doesn't scan every pattern for every position
        self.by_first_token = {}
        n_patterns = 0
        for phrase, skill_id in phrase_to_skill.items():
            toks = [t.lower() for t, _, _ in tokenize(phrase)]
            if not toks:
                continue
            self.by_first_token.setdefault(toks[0], []).append((toks, skill_id, phrase))
            n_patterns += 1
        self.n_patterns = n_patterns

    def find_matches(self, text: str):
        """Returns list of (start_char, end_char, skill_id, mention_text)."""
        doc_tokens = tokenize(text)
        lower_toks = [t.lower() for t, _, _ in doc_tokens]
        raw_matches = []

        for i, lt in enumerate(lower_toks):
            candidates = self.by_first_token.get(lt)
            if not candidates:
                continue
            for pattern_toks, skill_id, phrase in candidates:
                plen = len(pattern_toks)
                if i + plen > len(lower_toks):
                    continue
                if lower_toks[i:i + plen] == pattern_toks:
                    start_char = doc_tokens[i][1]
                    end_char = doc_tokens[i + plen - 1][2]
                    raw_matches.append((start_char, end_char, skill_id, text[start_char:end_char]))

        return self._filter_overlaps(raw_matches)

    @staticmethod
    def _filter_overlaps(matches):
        """Longest-span-wins, same policy as spaCy's filter_spans."""
        matches = sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0]))
        kept = []
        occupied = []  # list of (start, end) already claimed
        for m in matches:
            start, end = m[0], m[1]
            if any(start < o_end and end > o_start for o_start, o_end in occupied):
                continue
            kept.append(m)
            occupied.append((start, end))
        return sorted(kept, key=lambda m: m[0])


# ---------------------------------------------------------------------------
# KNOWN GAP vs. real spaCy tokenization (flagging, not hiding):
#   spaCy's default English tokenizer has special-case rules this regex
#   does not: contractions ("don't" -> "do"+"n't"), some abbreviation
#   handling, infix rules around punctuation. For skill-phrase vocabulary
#   (mostly alnum words, plus a handful of symbol-bearing tech terms like
#   "C++"/"C#"/"CI/CD"), the practical difference is small - but a pattern
#   containing an apostrophe or unusual punctuation could tokenize
#   differently between this fallback and real spaCy. Re-validate any such
#   pattern against actual spaCy tokenization once it's installed.
# ---------------------------------------------------------------------------
