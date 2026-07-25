"""
Tests for src/resolution/matching.py.
Run with: pytest tests/test_matching.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.resolution.models import SearchResult
from src.resolution.matching import (
    extract_quoted_title,
    extract_year_from_reference,
    extract_authors_from_reference,
    parse_reference_for_query,
    score_match,
    find_best_match,
)

# Real reference-list entry [1] from He & Wu (2019)'s bibliography
BARACHANT_2012_REF = (
    'A. Barachant, S. Bonnet, M. Congedo, and C. Jutten, "Multiclass '
    'braincomputer interface classification by Riemannian geometry," IEEE Trans. '
    'on Biomedical Engineering, vol. 59, no. 4, pp. 920\u2013928, 2012.'
)

# The real, correct paper this reference points to (hyphen restored, as a
# CrossRef/Semantic Scholar result would report it)
BARACHANT_2012_CORRECT = SearchResult(
    title="Multiclass Brain-Computer Interface Classification by Riemannian Geometry",
    authors=["Alexandre Barachant", "Stephane Bonnet", "Marco Congedo", "Christian Jutten"],
    year=2012,
    doi="10.1109/TBME.2011.2172210",
    source_api="crossref",
)

# A real but unrelated paper (should NOT match)
UNRELATED_PAPER = SearchResult(
    title="Attention Is All You Need",
    authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
    year=2017,
    doi="10.48550/arXiv.1706.03762",
    source_api="semantic_scholar",
)


# ---------- Extraction helpers ----------

def test_extract_quoted_title():
    title = extract_quoted_title(BARACHANT_2012_REF)
    assert title == "Multiclass braincomputer interface classification by Riemannian geometry"


def test_extract_quoted_title_none_when_no_quotes():
    # Book reference with no quoted title -- a real, valid case
    text = "C. M. Bishop, Pattern Recognition and Machine Learning. NY: Springer-Verlag, 2006."
    assert extract_quoted_title(text) is None


def test_extract_year_ignores_volume_and_page_numbers():
    year = extract_year_from_reference(BARACHANT_2012_REF)
    assert year == 2012  # not 59, 4, 920, or 928


def test_extract_authors_from_reference():
    title = extract_quoted_title(BARACHANT_2012_REF)
    authors = extract_authors_from_reference(BARACHANT_2012_REF, title)
    assert authors == ["Barachant", "Bonnet", "Congedo", "Jutten"]


def test_parse_reference_for_query_combines_all_three():
    authors, title, year = parse_reference_for_query(BARACHANT_2012_REF)
    assert authors == ["Barachant", "Bonnet", "Congedo", "Jutten"]
    assert title == "Multiclass braincomputer interface classification by Riemannian geometry"
    assert year == 2012


def test_extract_authors_does_not_crash_on_unquoted_book_reference():
    # Known limitation: book references without a quoted title don't cleanly
    # separate authors from the rest of the citation. Must not crash, and
    # the true first author's surname should still be found.
    text = "C. M. Bishop, Pattern Recognition and Machine Learning. NY: Springer-Verlag, 2006."
    authors = extract_authors_from_reference(text, None)
    assert "Bishop" in authors


# ---------- Scoring ----------

def test_score_match_correct_candidate_is_high_confidence():
    authors, title, year = parse_reference_for_query(BARACHANT_2012_REF)
    result = score_match(authors, title, year, BARACHANT_2012_CORRECT)
    assert result.verdict == "MATCH"
    assert result.title_similarity > 0.9  # only differs by a hyphen and casing
    assert result.author_overlap == 1.0
    assert result.year_match is True


def test_score_match_unrelated_candidate_is_no_match():
    authors, title, year = parse_reference_for_query(BARACHANT_2012_REF)
    result = score_match(authors, title, year, UNRELATED_PAPER)
    assert result.verdict == "NO_MATCH"
    assert result.title_similarity < 0.3
    assert result.author_overlap == 0.0


def test_score_match_right_authors_wrong_title_does_not_reach_match():
    # A candidate with the SAME authors and year but a fabricated/wrong
    # title must not be accepted as a MATCH -- title similarity gates it
    # even if the combined confidence alone might look high.
    wrong_title_same_authors = SearchResult(
        title="A Completely Different Paper About Something Else Entirely",
        authors=["Alexandre Barachant", "Stephane Bonnet", "Marco Congedo", "Christian Jutten"],
        year=2012,
        source_api="crossref",
    )
    authors, title, year = parse_reference_for_query(BARACHANT_2012_REF)
    result = score_match(authors, title, year, wrong_title_same_authors)
    assert result.verdict != "MATCH"


def test_score_match_fabricated_citation_against_real_candidates():
    # Ties back to the Phase 0 benchmark: eeg_008.json is a citation
    # constructed to not exist. Scored against real, unrelated candidates,
    # it must never resolve to a false MATCH.
    fabricated_ref = (
        "Okafor & Lindqvist, \"Federated meta-learning framework for "
        "cross-corpus seizure onset detection,\" 2023."
    )
    authors, title, year = parse_reference_for_query(fabricated_ref)
    result_a = score_match(authors, title, year, BARACHANT_2012_CORRECT)
    result_b = score_match(authors, title, year, UNRELATED_PAPER)
    assert result_a.verdict == "NO_MATCH"
    assert result_b.verdict == "NO_MATCH"


# ---------- End-to-end find_best_match ----------

def test_find_best_match_picks_correct_candidate_among_multiple():
    candidates = [UNRELATED_PAPER, BARACHANT_2012_CORRECT]
    best = find_best_match(BARACHANT_2012_REF, candidates)
    assert best is not None
    assert best.candidate is BARACHANT_2012_CORRECT
    assert best.verdict == "MATCH"


def test_find_best_match_returns_none_for_empty_candidate_list():
    assert find_best_match(BARACHANT_2012_REF, []) is None