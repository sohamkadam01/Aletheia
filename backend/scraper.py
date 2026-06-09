"""scraper.py
Utility functions for cleaning raw HTML content extracted from a webpage.
"""

import re
import unicodedata
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Unicode / encoding cleanup
# ---------------------------------------------------------------------------

# Characters that are pure encoding noise and should be deleted outright
_NOISE_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f"
    r"\ufeff\ufffd\u00ad"
    r"\u200b-\u200f\u202a-\u202e\u2060-\u206f]"
)

# Windows-1252 characters mis-decoded as Latin-1 / ISO-8859-1
# Maps the raw byte value (0x80-0x9f) to its correct Unicode code-point.
_WIN1252 = {
    0x80: "\u20ac",  # €
    0x82: "\u201a",  # ‚
    0x83: "\u0192",  # ƒ
    0x84: "\u201e",  # „
    0x85: "\u2026",  # …
    0x86: "\u2020",  # †
    0x87: "\u2021",  # ‡
    0x88: "\u02c6",  # ˆ
    0x89: "\u2030",  # ‰
    0x8a: "\u0160",  # Š
    0x8b: "\u2039",  # ‹
    0x8c: "\u0152",  # Œ
    0x8e: "\u017d",  # Ž
    0x91: "\u2018",  # '
    0x92: "\u2019",  # '
    0x93: "\u201c",  # "
    0x94: "\u201d",  # "
    0x95: "\u2022",  # •
    0x96: "\u2013",  # –
    0x97: "\u2014",  # —
    0x98: "\u02dc",  # ˜
    0x99: "\u2122",  # ™
    0x9a: "\u0161",  # š
    0x9b: "\u203a",  # ›
    0x9c: "\u0153",  # œ
    0x9e: "\u017e",  # ž
    0x9f: "\u0178",  # Ÿ
}

# Â followed by a Windows-1252 character – the classic double-encode pattern
# e.g. b"\xc2\x80\x99" → "'", b"\xc2\x80\x93" → "–"
_DOUBLE_ENCODED = re.compile(rb"\xc2([\x80-\x9f])")

# Common smart-quote / typographic replacements to plain ASCII
_UNICODE_TO_ASCII = str.maketrans({
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote / apostrophe
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u2015": "-",   # horizontal bar
    "\u2026": "...", # ellipsis
    "\u00a0": " ",   # non-breaking space
    "\u00ad": "",    # soft hyphen
    "\u202f": " ",   # narrow no-break space
    "\u2212": "-",   # minus sign
    "\u00b7": ".",   # middle dot
    "\u2022": "-",   # bullet → dash
    "\u2023": "-",   # triangular bullet
    "\u25cf": "-",   # black circle
    "\u25e6": "-",   # white bullet
})


def _fix_bytes(raw: bytes) -> bytes:
    """Fix Â+byte double-encoding in raw bytes before decoding."""
    def _replace(m: re.Match) -> bytes:
        byte_val = m.group(1)[0]
        fixed = _WIN1252.get(byte_val)
        if fixed:
            return fixed.encode("utf-8")
        return m.group(0)
    return _DOUBLE_ENCODED.sub(_replace, raw)


def clean_text(text: str) -> str:
    """
    Normalise a plain-text string extracted from HTML, PDF, or DOCX:
    1. NFC-normalise all Unicode
    2. Replace typographic punctuation with ASCII equivalents
    3. Remove zero-width / control characters
    4. Collapse runs of whitespace to a single space
    Returns a clean UTF-8 string safe for embedding and LLM prompts.
    """
    if not text:
        return ""

    # 1. Attempt to fix Mojibake: bytes decoded as Windows-1252 or Latin-1 when they were UTF-8
    try:
        # CP1252 is the most common Windows encoding and maps 0x80-0x9F to curly quotes, Euro, etc.
        fixed = text.encode("cp1252").decode("utf-8")
        text = fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            # Fallback to Latin-1 for characters that CP1252 doesn't define (e.g. U+0081)
            fixed = text.encode("latin-1").decode("utf-8")
            text = fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass  # Text was already correct Unicode

    # 2. NFC normalise
    text = unicodedata.normalize("NFC", text)

    # 3. Replace typographic characters with ASCII equivalents
    text = text.translate(_UNICODE_TO_ASCII)

    # 4. Remove noise characters
    text = _NOISE_CHARS.sub("", text)

    # 5. Collapse whitespace (preserve newlines for structure)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def decode_bytes(raw: bytes, charset: str = "utf-8") -> str:
    """
    Decode raw bytes to str, fixing double-encoded UTF-8 sequences first.
    Falls back through common encodings before giving up.
    """
    # Fix Â+byte patterns in the raw bytes
    raw = _fix_bytes(raw)

    # Try the declared charset first
    for enc in (charset, "utf-8", "windows-1252", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# HTML cleaning
# ---------------------------------------------------------------------------

def clean_html_content(html: str) -> str:
    """Remove scripts, styles, and unnecessary whitespace from raw HTML.

    Args:
        html: Raw HTML string extracted from the page.
    Returns:
        Cleaned, encoding-fixed plain text.
    """
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "iframe"]):
        element.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return clean_text(text)
