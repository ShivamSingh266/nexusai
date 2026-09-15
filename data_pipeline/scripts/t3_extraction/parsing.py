"""
T3 - Skill Extraction: text extraction + normalization layer.

Accepts PDF, DOCX, and plain text/CSV-cell input; returns a consistent
internal representation regardless of source format:

    ParsedDocument(source_type, source_id, raw_text, normalized_text, offset_map)

Design note on evidence spans (read this before Part 2):
Whitespace collapsing and de-hyphenation both change text LENGTH, so a
character offset found in normalized_text does NOT point at the same
character in raw_text unless you track the mapping. This module builds
that mapping (`offset_map`) during normalization instead of hand-waving
it - `offset_map[i]` gives the raw_text index for normalized_text[i], so
a match's (start_char, end_char) in normalized_text can always be
translated back to the true position in the original document via
`map_span_to_raw()`. Matching itself runs case-insensitively (spaCy's
`attr="LOWER"`, or the fallback matcher's lowercase comparison) rather
than lowercasing the text - so normalized_text keeps original casing,
and mention_text in every output record is exactly as it appeared in
the source, not lowercased.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import docx  # python-docx - DOCX
import pypdf  # already available in this environment - PDF
from bs4 import BeautifulSoup  # HTML stripping (job descriptions ship as HTML)


@dataclass
class ParsedDocument:
    source_type: str          # "resume" | "job" | "course"
    source_id: str
    raw_text: str
    normalized_text: str
    offset_map: list          # offset_map[i] = raw_text index for normalized_text[i]


# ---------------------------------------------------------------------------
# Format-specific text extraction -> plain raw_text
# ---------------------------------------------------------------------------

def extract_pdf_text(path) -> str:
    reader = pypdf.PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_docx_text(path) -> str:
    d = docx.Document(str(path))
    return "\n".join(p.text for p in d.paragraphs)


_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """
    jobDescription cells in the Naukri dataset ship as HTML fragments
    (<p>, <li>, <br>, ...). Strip tags but insert a space where a tag
    was, so "equipment.</li><li>Knowledge" doesn't glue into one word -
    a plain regex-replace-with-nothing would silently merge tokens and
    break phrase matching across what used to be a tag boundary.
    """
    if "<" not in text or ">" not in text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")


# ---------------------------------------------------------------------------
# Normalization WITH offset tracking
# ---------------------------------------------------------------------------

def normalize_with_offsets(raw_text: str):
    """
    - Collapses any run of whitespace (space/tab/CR/LF) to a single space.
    - De-hyphenates a word split across a line break: "soft-\\nware" -> "software"
      (only when preceded by an alnum char and followed, after the break,
      by another alnum char - so a real hyphenated compound like
      "father-in-law" that never crosses a line break is left untouched).
    - Does NOT lowercase - casing is preserved for evidence reporting;
      case-insensitive matching is handled by the matcher, not here.
    Returns (normalized_text, offset_map) where offset_map[i] is the
    raw_text index that normalized_text[i] came from.
    """
    out_chars = []
    offset_map = []
    i, n = 0, len(raw_text)

    while i < n:
        c = raw_text[i]

        if c == "-" and out_chars and out_chars[-1].isalnum():
            j = i + 1
            while j < n and raw_text[j] in " \t":
                j += 1
            if j < n and raw_text[j] == "\n":
                j += 1
                while j < n and raw_text[j] in " \t":
                    j += 1
                if j < n and raw_text[j].isalnum():
                    i = j  # drop the hyphen + line break entirely
                    continue

        if c in " \t\r\n":
            j = i
            while j < n and raw_text[j] in " \t\r\n":
                j += 1
            if out_chars and out_chars[-1] != " ":
                out_chars.append(" ")
                offset_map.append(i)
            i = j
            continue

        out_chars.append(c)
        offset_map.append(i)
        i += 1

    # trim a leading/trailing collapsed space without breaking alignment
    # (out_chars and offset_map are always the same length, so slicing
    # both with the same bounds keeps them in lockstep)
    start, end = 0, len(out_chars)
    if start < end and out_chars[start] == " ":
        start += 1
    if end > start and out_chars[end - 1] == " ":
        end -= 1

    normalized_text = "".join(out_chars[start:end])
    offset_map = offset_map[start:end]
    return normalized_text, offset_map


def map_span_to_raw(offset_map: list, start_char: int, end_char: int):
    """Translate a (start_char, end_char) span in normalized_text back to raw_text."""
    if not offset_map or start_char >= len(offset_map):
        return None, None
    raw_start = offset_map[start_char]
    raw_end = offset_map[min(end_char, len(offset_map)) - 1] + 1
    return raw_start, raw_end


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_document(source_type: str, source_id: str, raw_text: str) -> ParsedDocument:
    raw_text = strip_html(raw_text) if raw_text else ""
    normalized_text, offset_map = normalize_with_offsets(raw_text)
    return ParsedDocument(source_type, source_id, raw_text, normalized_text, offset_map)


def parse_file(source_type: str, source_id: str, path) -> ParsedDocument:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw_text = extract_pdf_text(path)
    elif suffix == ".docx":
        raw_text = extract_docx_text(path)
    else:  # plain text
        raw_text = path.read_text(errors="ignore")
    return parse_document(source_type, source_id, raw_text)
