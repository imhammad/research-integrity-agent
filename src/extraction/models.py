"""
Data models shared across the extraction pipeline.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class CitationMarker:
    """A single citation marker found within a sentence."""
    raw_text: str        # e.g. "Jemal et al. (2024)" or "[12]"
    style: str            # "numbered" | "parenthetical" | "narrative"
    start_char: int       # offset within the sentence (not the full document)
    end_char: int

    def __repr__(self) -> str:
        return f"CitationMarker({self.raw_text!r}, style={self.style!r})"


@dataclass
class ExtractedClaim:
    """A sentence that contains at least one citation marker, i.e. a
    candidate (claim, citation) pair to be verified downstream."""
    sentence_text: str
    citation_markers: List[CitationMarker] = field(default_factory=list)
    doc_start_char: int = 0   # offset within the full source document
    doc_end_char: int = 0

    def __repr__(self) -> str:
        markers = [m.raw_text for m in self.citation_markers]
        return f"ExtractedClaim(sentence={self.sentence_text[:50]!r}..., markers={markers})"