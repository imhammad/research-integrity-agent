"""
Main extraction pipeline: raw document text in, candidate (claim, citation)
pairs out.

A sentence only becomes an ExtractedClaim if it contains at least one
citation marker -- sentences with no citations are not candidates for
verification and are dropped here.
"""
from typing import List

from .citation_patterns import find_citations_in_sentence
from .sentence_splitter import split_sentences
from .preprocessing import normalize_whitespace
from .models import ExtractedClaim


def extract_claims(text: str) -> List[ExtractedClaim]:
    text = normalize_whitespace(text)
    sentences = split_sentences(text)
    claims: List[ExtractedClaim] = []

    for sent_text, start, end in sentences:
        markers = find_citations_in_sentence(sent_text)
        if markers:
            claims.append(ExtractedClaim(
                sentence_text=sent_text,
                citation_markers=markers,
                doc_start_char=start,
                doc_end_char=end,
            ))

    return claims