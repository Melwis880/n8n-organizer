from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


# Control, format, line/paragraph separator and lone surrogate characters (the last come from
# file names that are not valid UTF-8 and cannot be written to a UTF-8 file).
UNSAFE_CATEGORIES = ("Cc", "Cf", "Zl", "Zp", "Cs")

# Characters that can start a link, image, HTML tag, comment or code span in Markdown.
_MD_SPECIAL = re.compile(r"([\\`<\[\]])")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(data: Any) -> str:
    return sha256_text(json.dumps(data, ensure_ascii=False, sort_keys=True))


def get_word_count(text: str) -> int:
    """Approximate word count, good enough for NotebookLM source-size splitting."""
    if not text:
        return 0
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def clean_text(value: Any, max_len: int = 200) -> str:
    """Make untrusted text safe for one Markdown line: no control, format or bidi characters, no newlines."""
    text = value if isinstance(value, str) else ("" if value is None else str(value))
    text = "".join(" " if unicodedata.category(ch) in UNSAFE_CATEGORIES else ch for ch in text)
    text = " ".join(text.split())
    if len(text) > max_len:
        text = text[: max_len - 3].rstrip() + "..."
    return text


def has_unsafe_chars(text: str) -> bool:
    return any(unicodedata.category(ch) in UNSAFE_CATEGORIES for ch in text)


def text_field(value: Any) -> str:
    """A name field from workflow JSON: strings only, so an object or list never reaches the output."""
    return value if isinstance(value, str) else ""


def md_text(value: Any, max_len: int = 200) -> str:
    """clean_text, then escape what could turn untrusted text into a link, image, HTML or code span."""
    return _MD_SPECIAL.sub(r"\\\1", clean_text(value, max_len))


def write_new_file(path: Path, text: str) -> None:
    """Create path and write text. Fails if anything is already there, a symlink included, so the
    tool never follows a link or overwrites a file, even one that appeared during the run."""
    with path.open("x", encoding="utf-8") as f:
        f.write(text)
