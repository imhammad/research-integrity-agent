"""
Tests for src/resolution/reference_parser.py.
Run with: pytest tests/test_reference_parser.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.resolution.reference_parser import (
    extract_references_section,
    parse_numbered_reference_list,
    get_reference,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_extract_references_section_finds_heading():
    text = "Some body text here.\n\nREFERENCES\n[1] First reference.\n[2] Second reference."
    section = extract_references_section(text)
    assert section.strip().startswith("[1] First reference.")


def test_extract_references_section_handles_roman_numeral_prefix():
    text = "Body text.\n\nVII. REFERENCES\n[1] First reference."
    section = extract_references_section(text)
    assert section.strip().startswith("[1] First reference.")


def test_extract_references_section_returns_empty_if_no_heading():
    text = "Just some body text with no references heading at all."
    assert extract_references_section(text) == ""


def test_parse_simple_three_entry_list():
    text = (
        '[1] A. Author, "First paper title," Journal A, 2020.\n'
        '[2] B. Author, "Second paper title," Journal B, 2021.\n'
        '[3] C. Author, "Third paper title," Journal C, 2022.'
    )
    entries = parse_numbered_reference_list(text)
    assert len(entries) == 3
    assert "First paper title" in entries[1]
    assert "Second paper title" in entries[2]
    assert "Third paper title" in entries[3]


def test_parse_rejects_out_of_sequence_bracket_as_boundary():
    # A bracketed number that does NOT continue the expected sequence
    # (here "[99]" appears where "[2]" was expected) must not be treated
    # as a new entry boundary -- it should remain part of entry [1]'s text.
    text = (
        '[1] A. Author, "Title mentions result [99] somewhere," Journal, 2020.\n'
        '[2] B. Author, "Second paper," Journal B, 2021.'
    )
    entries = parse_numbered_reference_list(text)
    assert len(entries) == 2
    assert "[99]" in entries[1]  # stayed inside entry 1's own text
    assert "Second paper" in entries[2]


def test_get_reference_returns_none_for_missing_number():
    entries = {1: "Some reference"}
    assert get_reference(entries, 5) is None
    assert get_reference(entries, 1) == "Some reference"


# ---------- Integration tests against real papers ----------

def test_parse_full_he_wu_2019_reference_list():
    full_text = (FIXTURES_DIR / "he_wu_2019_references.txt").read_text(encoding="utf-8")
    section = extract_references_section(full_text)
    entries = parse_numbered_reference_list(section)

    assert len(entries) == 42
    assert all(n in entries for n in range(1, 43))
    assert "Siena scalp eeg database" in entries[6]
    assert "[Online]" in entries[6]
    assert "A new generation of braincomputer interface" in entries[7]
    assert "Zanini" in entries[42]


def test_parse_full_hosen_2026_reference_list():
    full_text = (FIXTURES_DIR / "hosen_2026_references.txt").read_text(encoding="utf-8")
    section = extract_references_section(full_text)
    entries = parse_numbered_reference_list(section)

    assert len(entries) == 11
    assert all(n in entries for n in range(1, 12))
    assert "Aboalsamh et al." in entries[2]
    assert "Eegnet" in entries[5] or "EEGNet" in entries[5]