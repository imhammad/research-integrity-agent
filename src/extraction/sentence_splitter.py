"""
Sentence segmentation using spaCy.

Deliberately not LLM-based: sentence boundary detection in academic text
(handling "et al.", "Fig.", decimal numbers, abbreviations) is a solved,
deterministic problem. spaCy's statistical sentencizer handles this
reliably and reproducibly, with no API cost and no non-determinism.
"""
import re
from typing import List, Tuple
import spacy

from .citation_patterns import NUMBERED_CITATION_RE

_nlp = None  # lazy-loaded singleton so the model loads once per process

_ET_AL_RE = re.compile(r"\bet al\.")


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _mask_numbered_citations(text: str) -> str:
    """Replace each numbered citation marker (e.g. "[6]", "[3, 4]") with a
    same-length run of a neutral character before sentence segmentation.

    Root-cause fix for a real, confirmed failure mode: spaCy's statistical
    sentencizer sometimes misjudges a bracketed numbered citation as a
    sentence boundary -- either isolating it as its own fragment, or (worse)
    splitting mid-sentence directly before it with no punctuation cue at all,
    silently severing the claim text from its citation. Numbered citations
    carry no information the sentencizer needs, so masking them removes the
    ambiguity at its source rather than patching each observed symptom.

    Because the replacement is exactly the same length as the original
    match, character offsets are preserved 1:1, so sentence boundaries found
    on the masked text can be used directly to slice the original text.
    """
    return NUMBERED_CITATION_RE.sub(lambda m: "C" * len(m.group(0)), text)


def _mask_et_al(text: str) -> str:
    """Replace "et al." with a same-length placeholder that has no period.

    Root-cause fix for a second, distinct real failure mode found via
    testing against a real paper: "et al." is a classic hard case for
    statistical sentence segmenters, since it ends in a period that can
    legitimately end a sentence in other contexts. spaCy sometimes misjudges
    "Author et al. [42] proposed..." as ending right after "et al.",
    especially when what follows the citation doesn't look like a typical
    continuation. Since "et al." is never actually a sentence boundary in
    citation contexts, masking its period removes the ambiguity outright.
    """
    return _ET_AL_RE.sub(lambda m: "X" * len(m.group(0)), text)


def split_sentences(text: str) -> List[Tuple[str, int, int]]:
    """Split text into sentences.

    Returns a list of (sentence_text, start_char, end_char) tuples, where
    start_char/end_char are offsets into the original input text -- needed
    so extracted claims can be traced back to their location in the source
    document later in the pipeline. sentence_text is always sliced from the
    original (unmasked) text, so citation markers and "et al." appear intact.
    """
    nlp = get_nlp()
    masked = _mask_et_al(_mask_numbered_citations(text))
    doc = nlp(masked)

    return [
        (text[sent.start_char:sent.end_char], sent.start_char, sent.end_char)
        for sent in doc.sents
    ]