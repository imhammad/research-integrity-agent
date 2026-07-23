"""
Tests for src/extraction. Run with: pytest tests/test_extraction.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.extraction.citation_patterns import find_citations_in_sentence
from src.extraction.extractor import extract_claims
from src.extraction.sentence_splitter import split_sentences


# ---------- Numbered / IEEE style ----------

def test_single_numbered_citation():
    markers = find_citations_in_sentence("This was shown previously [12].")
    assert len(markers) == 1
    assert markers[0].style == "numbered"
    assert markers[0].raw_text == "[12]"


def test_multiple_numbered_in_one_marker():
    markers = find_citations_in_sentence("Several works agree [3, 4].")
    assert len(markers) == 1
    assert markers[0].raw_text == "[3, 4]"


def test_numbered_range():
    markers = find_citations_in_sentence("This is well established [3-5].")
    assert len(markers) == 1
    assert markers[0].raw_text == "[3-5]"


def test_two_separate_numbered_markers():
    markers = find_citations_in_sentence("Model X [3] outperforms baselines [4].")
    assert len(markers) == 2
    assert [m.raw_text for m in markers] == ["[3]", "[4]"]


# ---------- Author-year parenthetical style ----------

def test_single_parenthetical_citation():
    markers = find_citations_in_sentence("Accuracy improved substantially (Jemal et al., 2024).")
    assert len(markers) == 1
    assert markers[0].style == "parenthetical"
    assert markers[0].raw_text == "(Jemal et al., 2024)"


def test_multiple_citations_in_one_parenthetical():
    markers = find_citations_in_sentence(
        "This has been reported consistently (Smith, 2023; Jones et al., 2024)."
    )
    assert len(markers) == 1
    assert markers[0].style == "parenthetical"
    assert "Smith, 2023" in markers[0].raw_text
    assert "Jones et al., 2024" in markers[0].raw_text


def test_two_authors_with_ampersand():
    markers = find_citations_in_sentence("This was first proposed (Smith & Jones, 2023).")
    assert len(markers) == 1
    assert markers[0].style == "parenthetical"


# ---------- Author-year narrative style ----------

def test_narrative_citation_et_al():
    markers = find_citations_in_sentence("Jemal et al. (2024) reported a 10.30% improvement.")
    assert len(markers) == 1
    assert markers[0].style == "narrative"
    assert markers[0].raw_text == "Jemal et al. (2024)"


def test_narrative_citation_two_authors():
    markers = find_citations_in_sentence("Smith and Jones (2023) proposed a new baseline.")
    assert len(markers) == 1
    assert markers[0].style == "narrative"
    assert markers[0].raw_text == "Smith and Jones (2023)"


def test_narrative_not_double_counted_as_parenthetical():
    # "(2024)" alone should not ALSO be picked up as a separate parenthetical match
    markers = find_citations_in_sentence("Jemal et al. (2024) reported strong results.")
    assert len(markers) == 1


# ---------- No citation present ----------

def test_sentence_with_no_citation():
    markers = find_citations_in_sentence("This sentence makes a claim with no source at all.")
    assert len(markers) == 0


# ---------- Full pipeline: extractor ----------

def test_extractor_drops_sentences_without_citations():
    text = (
        "Seizure detection is an important clinical problem. "
        "Jemal et al. (2024) improved cross-subject accuracy by 10.30% on CHB-MIT. "
        "This motivates further study of domain adaptation."
    )
    claims = extract_claims(text)
    assert len(claims) == 1
    assert "Jemal et al." in claims[0].sentence_text
    assert claims[0].citation_markers[0].raw_text == "Jemal et al. (2024)"


def test_extractor_handles_et_al_period_without_splitting_sentence():
    # Regression test: spaCy must not treat "et al." as an end-of-sentence period
    text = "Jemal et al. (2024) reported a 10.3% improvement. CG-MambaNet outperformed prior work."
    claims = extract_claims(text)
    assert len(claims) == 1
    assert claims[0].sentence_text.strip() == (
        "Jemal et al. (2024) reported a 10.3% improvement."
    )


def test_extractor_multiple_claims_multiple_styles():
    text = (
        "Several methods have been proposed [3, 4]. "
        "Chen et al. (2026) achieved a higher AUC than prior work. "
        "No citation appears in this sentence at all. "
        "This finding has been replicated (Smith, 2023; Jones et al., 2024)."
    )
    claims = extract_claims(text)
    assert len(claims) == 3
    styles_found = {claims[0].citation_markers[0].style,
                     claims[1].citation_markers[0].style,
                     claims[2].citation_markers[0].style}
    assert styles_found == {"numbered", "narrative", "parenthetical"}


def test_sentence_splitter_does_not_isolate_numbered_citation():
    # Regression test: found via manual stress-testing. spaCy's statistical
    # sentencizer sometimes misjudges a numbered citation like "[3, 4]." at
    # the end of a longer sentence as the start of a new sentence, even with
    # no newline involved at all. split_sentences() must correct this so a
    # citation marker never appears as its own standalone "sentence".
    text = (
        "Several domain adaptation techniques have been proposed to address "
        "this [3, 4]. This remains an open problem."
    )
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert sentences[0][0] == (
        "Several domain adaptation techniques have been proposed to address this [3, 4]."
    )
    assert sentences[1][0] == "This remains an open problem."


def test_extractor_handles_hard_line_wrap_before_citation():
    # Regression test: PDF-extracted text often has a hard line-wrap (single
    # newline with no semantic meaning) right before a citation marker. This
    # must NOT cause the citation to be split into its own "sentence" away
    # from the claim it belongs to.
    text = (
        "Several domain adaptation techniques have been proposed to address this\n"
        "[3, 4]. This remains an open problem."
    )
    claims = extract_claims(text)
    assert len(claims) == 1
    assert claims[0].sentence_text.strip() == (
        "Several domain adaptation techniques have been proposed to address this [3, 4]."
    )
    assert claims[0].citation_markers[0].raw_text == "[3, 4]"


def test_extractor_preserves_paragraph_breaks_as_non_merging():
    # Two paragraphs separated by a blank line should NOT be joined into one
    # run-on sentence -- only single hard-wrap newlines get collapsed.
    text = (
        "This is the end of paragraph one with a citation (Smith, 2023).\n\n"
        "This is the start of paragraph two, unrelated and uncited."
    )
    claims = extract_claims(text)
    assert len(claims) == 1
    assert "paragraph two" not in claims[0].sentence_text


def test_extractor_preserves_document_char_offsets():
    text = "Intro sentence with no citation. Jemal et al. (2024) found strong results."
    claims = extract_claims(text)
    assert len(claims) == 1
    start, end = claims[0].doc_start_char, claims[0].doc_end_char
    assert text[start:end].strip() == claims[0].sentence_text.strip()