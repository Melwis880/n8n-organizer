from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def sha1_json(data: Any) -> str:
    return sha1_text(json.dumps(data, ensure_ascii=False, sort_keys=True))


def get_word_count(text: str) -> int:
    """Approximate word count, good enough for NotebookLM source-size splitting."""
    if not text:
        return 0
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def clean_text(value: Any, max_len: int = 200) -> str:
    """Make untrusted text safe for one Markdown line: no control, format or bidi characters, no newlines."""
    text = value if isinstance(value, str) else ("" if value is None else str(value))
    text = "".join(" " if unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") else ch for ch in text)
    text = " ".join(text.split())
    if len(text) > max_len:
        text = text[: max_len - 3].rstrip() + "..."
    return text
