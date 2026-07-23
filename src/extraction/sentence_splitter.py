"""
Sentence segmentation using spaCy.

Deliberately not LLM-based: sentence boundary detection in academic text
(handling "et al.", "Fig.", decimal numbers, abbreviations) is a solved,
deterministic problem. spaCy's statistical sentencizer handles this
reliably and reproducibly, with no API cost and no non-determinism.
"""
from typing import List, Tuple
import spacy

from .citation_patterns import NUMBERED_CITATION_RE

_nlp = None  # lazy-loaded singleton so the model loads once per process


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _is_citation_only_fragment(sentence_text: str) -> bool:
    """True if, after removing numbered citation markers, no letters remain.

    Known limitation of spaCy's statistical (dependency-parse-based)
    sentencizer: a numbered citation like "[3, 4]." at the end of a longer
    sentence is sometimes misjudged as the start of a new sentence, producing
    a standalone fragment such as "[3, 4]." with no actual sentence content.
    This check identifies that failure mode so it can be corrected below.
    """
    remainder = NUMBERED_CITATION_RE.sub("", sentence_text)
    return not any(ch.isalpha() for ch in remainder)


def split_sentences(text: str) -> List[Tuple[str, int, int]]:
    """Split text into sentences.

    Returns a list of (sentence_text, start_char, end_char) tuples, where
    start_char/end_char are offsets into the original input text -- needed
    so extracted claims can be traced back to their location in the source
    document later in the pipeline.

    Post-processing merges any sentence fragment that consists only of a
    numbered citation marker (see _is_citation_only_fragment) back into the
    preceding sentence, correcting a known spaCy sentence-boundary error.
    """
    nlp = get_nlp()
    doc = nlp(text)
    raw_sents = [(sent.text, sent.start_char, sent.end_char) for sent in doc.sents]

    merged: List[Tuple[str, int, int]] = []
    for sent_text, start, end in raw_sents:
        if merged and _is_citation_only_fragment(sent_text):
            prev_text, prev_start, prev_end = merged[-1]
            # Reconstruct from the original text to preserve exact spacing
            joined_text = text[prev_start:end]
            merged[-1] = (joined_text, prev_start, end)
        else:
            merged.append((sent_text, start, end))

    return merged