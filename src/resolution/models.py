"""
Data models for the citation resolution pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SearchResult:
    """A single candidate paper returned by CrossRef or Semantic Scholar."""
    title: str
    authors: List[str] = field(default_factory=list)  # full names, e.g. "Imene Jemal"
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    source_api: str = ""  # "crossref" | "semantic_scholar"
    raw: Dict[str, Any] = field(default_factory=dict)  # original API response, for debugging

    def __repr__(self) -> str:
        return f"SearchResult({self.title[:60]!r}, year={self.year}, source={self.source_api!r})"


@dataclass
class MatchScore:
    """Result of comparing a citation (reference text or author/year) against
    one candidate SearchResult."""
    title_similarity: float   # 0.0-1.0
    author_overlap: float     # 0.0-1.0, fraction of query author last names found in candidate
    year_match: bool
    confidence: float         # combined 0.0-1.0 score
    verdict: str              # "MATCH" | "POSSIBLE_MATCH" | "NO_MATCH"
    candidate: SearchResult

    def __repr__(self) -> str:
        return (f"MatchScore(verdict={self.verdict!r}, confidence={self.confidence:.2f}, "
                f"candidate={self.candidate.title[:50]!r})")