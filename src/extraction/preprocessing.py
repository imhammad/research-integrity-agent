"""
Text normalization applied before sentence segmentation.

PDF-extracted academic text almost always contains hard line-wraps (a single
newline where a line of the PDF ended, with no semantic meaning) mixed with
genuine paragraph breaks (a blank line between paragraphs). If left as-is,
a hard line-wrap landing right before a citation marker can fool the
sentence segmenter into treating the citation as its own "sentence",
severing it from the claim it belongs to.

This function collapses hard line-wraps into spaces while preserving real
paragraph breaks, so downstream sentence segmentation sees clean, correctly
joined sentences regardless of how the source PDF happened to wrap its lines.
"""
import re

_PARA_BREAK_PLACEHOLDER = "\x00PARA_BREAK\x00"

# Diaeresis, acute, grave, circumflex, tilde, cedilla: PDF text extraction
# sometimes emits these as free-floating characters (surrounded by
# whitespace) instead of correctly combining them into the letter they
# belong to (e.g. "Muller" + stray "¨" instead of "Müller"). Found via
# testing against a real paper where this silently broke citation-marker
# regex matching by inserting an unexpected character where none was
# expected. These characters never appear as meaningful standalone content
# in English academic prose, so removing an isolated, whitespace-surrounded
# instance is safe.
_STRAY_DIACRITIC_RE = re.compile(r"\s+[\u00A8\u00B4\u0060\u005E\u007E\u00B8]\s+")


def normalize_whitespace(text: str) -> str:
    # Step 1: protect genuine paragraph breaks (a blank line, i.e. 2+ newlines)
    text = re.sub(r"\n\s*\n+", _PARA_BREAK_PLACEHOLDER, text)

    # Step 2: any remaining single newlines are hard line-wraps -- collapse to a space
    text = text.replace("\n", " ")

    # Step 3: restore paragraph breaks as a clean double-newline
    text = text.replace(_PARA_BREAK_PLACEHOLDER, "\n\n")

    # Step 4: strip stray floating diacritic artifacts from PDF extraction
    text = _STRAY_DIACRITIC_RE.sub("", text)

    # Step 5: collapse repeated spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()