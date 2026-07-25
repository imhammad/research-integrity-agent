"""
Decides whether a candidate search result (from CrossRef / Semantic Scholar)
actually matches a citation, and how confidently.

This is the part of the resolver that determines whether a citation
resolves, is uncertain, or fails to resolve -- getting the thresholds and
comparison logic right here matters more than the API plumbing, since a
mismatch here would either wrongly clear a bad citation or wrongly flag a
real one. Every scoring rule is independently unit-testable without a
network call.
"""
import re
import difflib
from typing import List, Optional, Tuple

from .models import SearchResult, MatchScore

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_QUOTED_TITLE_RE = re.compile(r'["\u201c]([^"\u201d]{10,300})["\u201d]')


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalized_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def extract_year_from_reference(text: str) -> Optional[int]:
    """The publication year in an IEEE-style reference is almost always the
    last 4-digit year-shaped number in the entry (volume/page/issue numbers
    don't look like years). Takes the last match found."""
    years = [int(m.group(0)) for m in _YEAR_RE.finditer(text)]
    return years[-1] if years else None


def extract_quoted_title(reference_text: str) -> Optional[str]:
    """IEEE-style references almost always quote the paper title. Falls
    back to None if no quoted text is found (e.g. a book reference with no
    quoted title, which is a real, valid case -- not every reference has one).

    Trailing punctuation is stripped from the result: American-style
    citation punctuation places the comma *inside* the closing quote mark
    (e.g. "...Riemannian geometry,"), so the raw regex match would otherwise
    include a trailing comma that isn't semantically part of the title.
    """
    match = _QUOTED_TITLE_RE.search(reference_text)
    if not match:
        return None
    return match.group(1).strip().rstrip(",.;").strip()


def _extract_last_name(name_chunk: str) -> Optional[str]:
    """Extract the surname from a single author name chunk like "A. Barachant"
    or "and C. Jutten". Requires 2+ letters so bare initials ("A.") are
    correctly excluded."""
    name_chunk = re.sub(r"^\s*and\s+", "", name_chunk.strip(), flags=re.IGNORECASE)
    words = re.findall(r"[A-Z][a-zA-Z\-']+", name_chunk)
    return words[-1] if words else None


def extract_authors_from_reference(reference_text: str, title: Optional[str]) -> List[str]:
    """Author list in an IEEE-style reference is everything before the
    quoted title. Splits on commas (the "and" before the final author is
    stripped by _extract_last_name)."""
    if title:
        idx = reference_text.find(title)
        author_section = reference_text[:idx] if idx > 0 else reference_text
    else:
        author_section = reference_text
    author_section = author_section.strip().rstrip(',').rstrip('"').rstrip('\u201c')

    chunks = [c for c in author_section.split(",") if c.strip()]
    names = [_extract_last_name(c) for c in chunks]
    return [n for n in names if n]


def parse_reference_for_query(reference_text: str) -> Tuple[List[str], Optional[str], Optional[int]]:
    """Parse a raw reference-list entry into (author_lastnames, title, year)
    for use as a search query and as the basis for match scoring."""
    title = extract_quoted_title(reference_text)
    authors = extract_authors_from_reference(reference_text, title)
    year = extract_year_from_reference(reference_text)
    return authors, title, year


def score_match(
    query_authors: List[str],
    query_title: Optional[str],
    query_year: Optional[int],
    candidate: SearchResult,
) -> MatchScore:
    """Score how well a candidate SearchResult matches a query citation.

    Weighting rationale: title is the strongest signal (0.6) since it's the
    most specific identifier; author overlap is secondary (0.3) since author
    lists can be truncated ("et al.") or reordered; year is a weak tiebreaker
    (0.1) since preprint vs. published year commonly differ by one.

    A MATCH verdict additionally requires title_similarity >= 0.6 on its
    own, not just a high combined score -- this prevents a citation with
    the right authors and year but a completely different (or fabricated)
    title from being wrongly accepted.
    """
    title_sim = _normalized_ratio(query_title, candidate.title) if (query_title and candidate.title) else 0.0

    author_overlap = 0.0
    if query_authors:
        candidate_lastnames = {
            _normalize(name.strip().split()[-1]) for name in candidate.authors if name.strip()
        }
        query_lastnames_norm = {_normalize(a) for a in query_authors}
        matched = query_lastnames_norm & candidate_lastnames
        author_overlap = len(matched) / len(query_lastnames_norm) if query_lastnames_norm else 0.0

    year_match = (
        query_year is not None and candidate.year is not None
        and abs(query_year - candidate.year) <= 1
    )

    confidence = 0.6 * title_sim + 0.3 * author_overlap + 0.1 * (1.0 if year_match else 0.0)

    if confidence >= 0.75 and title_sim >= 0.6:
        verdict = "MATCH"
    elif confidence >= 0.45:
        verdict = "POSSIBLE_MATCH"
    else:
        verdict = "NO_MATCH"

    return MatchScore(
        title_similarity=title_sim,
        author_overlap=author_overlap,
        year_match=year_match,
        confidence=confidence,
        verdict=verdict,
        candidate=candidate,
    )


def find_best_match(reference_text: str, candidates: List[SearchResult]) -> Optional[MatchScore]:
    """Parse a raw reference entry and score it against every candidate
    search result, returning the highest-confidence match (or None if
    candidates is empty -- a real "nothing came back from the API" case)."""
    if not candidates:
        return None
    authors, title, year = parse_reference_for_query(reference_text)
    scores = [score_match(authors, title, year, c) for c in candidates]
    return max(scores, key=lambda s: s.confidence)