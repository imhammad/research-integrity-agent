"""
Regex-based citation marker detection.

Deliberately not LLM-based: citation marker shapes (numbered, author-year
parenthetical, author-year narrative) are a fixed, well-defined set of
patterns. Regex is deterministic, fast, free, and fully testable -- an LLM
would add non-determinism and cost with no accuracy benefit here.

Three citation styles are handled:
  - numbered / IEEE style:      [12]   [3, 4]   [3-5]
  - author-year parenthetical:  (Jemal et al., 2024)   (Smith, 2023; Jones et al., 2024)
  - author-year narrative:      Jemal et al. (2024)   Smith and Jones (2023)
"""
import re
from typing import List

from .models import CitationMarker

# --- Numbered / IEEE style: [12], [3, 4], [3-5], [3, 5-7] ---
NUMBERED_CITATION_RE = re.compile(
    r"\[\s*\d+(?:\s*[-\u2013\u2014]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-\u2013\u2014]\s*\d+)?)*\s*\]"
)

# Building block: a single author unit, e.g. "Jemal et al.", "Smith and Jones", "Smith"
_AUTHOR_PART = r"[A-Z][A-Za-z'\-]+(?:\s+et al\.|\s+(?:and|&)\s+[A-Z][A-Za-z'\-]+)?"

# Building block: one "Author, YYYY" unit used inside parenthetical citations
_AUTHOR_YEAR_UNIT = _AUTHOR_PART + r",?\s+\d{4}[a-z]?"

# --- Author-year parenthetical: (Jemal et al., 2024)  (Smith, 2023; Jones et al., 2024) ---
PARENTHETICAL_CITATION_RE = re.compile(
    r"\(\s*(" + _AUTHOR_YEAR_UNIT + r"(?:\s*;\s*" + _AUTHOR_YEAR_UNIT + r")*)\s*\)"
)

# --- Author-year narrative: Jemal et al. (2024)   Smith and Jones (2023) ---
NARRATIVE_CITATION_RE = re.compile(
    r"\b(" + _AUTHOR_PART + r")\s*\((\d{4}[a-z]?)\)"
)


def find_citations_in_sentence(sentence: str) -> List[CitationMarker]:
    """Find all citation markers in a single sentence, deduplicated by
    character span and sorted by position of appearance."""
    matches = []

    for m in NUMBERED_CITATION_RE.finditer(sentence):
        matches.append(CitationMarker(
            raw_text=m.group(0), style="numbered",
            start_char=m.start(), end_char=m.end()
        ))

    for m in NARRATIVE_CITATION_RE.finditer(sentence):
        matches.append(CitationMarker(
            raw_text=m.group(0), style="narrative",
            start_char=m.start(), end_char=m.end()
        ))

    # Narrative citations look like "Jemal et al. (2024)" -- the parenthetical
    # regex would also match the "(2024)" part in isolation as a false
    # positive, so parenthetical matches are only kept if they are not
    # already contained within a narrative match found above.
    narrative_spans = [(m.start_char, m.end_char) for m in matches if m.style == "narrative"]

    def _inside_narrative(start, end):
        return any(ns <= start and end <= ne for ns, ne in narrative_spans)

    for m in PARENTHETICAL_CITATION_RE.finditer(sentence):
        if _inside_narrative(m.start(), m.end()):
            continue
        matches.append(CitationMarker(
            raw_text=m.group(0), style="parenthetical",
            start_char=m.start(), end_char=m.end()
        ))

    # Deduplicate identical spans, then sort by position of appearance
    seen = set()
    deduped = []
    for marker in sorted(matches, key=lambda m: m.start_char):
        span = (marker.start_char, marker.end_char)
        if span in seen:
            continue
        seen.add(span)
        deduped.append(marker)

    return deduped