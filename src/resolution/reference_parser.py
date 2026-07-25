"""
Parses a paper's reference list (bibliography) into structured entries.

This exists because numbered in-text citations like "[12]" are meaningless
on their own -- they only resolve to something once we know what reference
#12 actually is in that specific paper's bibliography. This module turns the
raw References section text into a {number: raw_reference_string} mapping
that the resolver (Phase 2, next step) can search against CrossRef /
Semantic Scholar to find the real paper.
"""
import re
from typing import Dict, Optional

# Matches a "References" section heading, optionally preceded by a roman
# numeral section number (e.g. "VII. REFERENCES"), on its own line.
_REFERENCES_HEADING_RE = re.compile(
    r"^\s*(?:[IVXLCM]+\.?\s*)?REFERENCES\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# Matches a numbered reference-list entry marker, e.g. "[12]"
_ENTRY_MARKER_RE = re.compile(r"\[(\d+)\]")


def extract_references_section(full_text: str) -> str:
    """Return the text of the document starting after the "References"
    heading. Returns an empty string if no such heading is found.
    """
    match = _REFERENCES_HEADING_RE.search(full_text)
    if not match:
        return ""
    return full_text[match.end():]


def parse_numbered_reference_list(references_text: str) -> Dict[int, str]:
    """Parse a numbered reference list into {number: raw_reference_string}.

    Only a bracketed number that continues a strictly increasing sequence
    starting at 1 is treated as an entry boundary. This deliberately
    excludes any other bracketed number that might appear inside an entry's
    own text (e.g. "[Online]" doesn't match since it has no digits, but a
    stray "[2020]"-shaped false positive would also be rejected here since
    it wouldn't continue the expected sequence).
    """
    matches = list(_ENTRY_MARKER_RE.finditer(references_text))

    boundaries = []  # (number, position right after the closing bracket)
    expected = 1
    for m in matches:
        num = int(m.group(1))
        if num == expected:
            boundaries.append((num, m.end()))
            expected += 1

    entries: Dict[int, str] = {}
    for i, (num, content_start) in enumerate(boundaries):
        content_end = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(references_text)
        # content_end currently points right after the NEXT entry's bracket;
        # trim back to right before that next entry's own "[" marker instead.
        if i + 1 < len(boundaries):
            next_marker_start = matches[
                next(j for j, m in enumerate(matches) if m.end() == boundaries[i + 1][1])
            ].start()
            content_end = next_marker_start
        entry_text = references_text[content_start:content_end].strip()
        entry_text = re.sub(r"\s+", " ", entry_text)  # collapse hard-wraps within the entry
        entries[num] = entry_text

    return entries


def get_reference(references: Dict[int, str], number: int) -> Optional[str]:
    """Convenience lookup, returns None if the number isn't present
    (e.g. the references section failed to parse, or the paper doesn't
    have that many references -- both real, meaningful "not found" cases)."""
    return references.get(number)