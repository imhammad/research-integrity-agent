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


def normalize_whitespace(text: str) -> str:
    # Step 1: protect genuine paragraph breaks (a blank line, i.e. 2+ newlines)
    text = re.sub(r"\n\s*\n+", _PARA_BREAK_PLACEHOLDER, text)

    # Step 2: any remaining single newlines are hard line-wraps -- collapse to a space
    text = text.replace("\n", " ")

    # Step 3: restore paragraph breaks as a clean double-newline
    text = text.replace(_PARA_BREAK_PLACEHOLDER, "\n\n")

    # Step 4: collapse repeated spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()