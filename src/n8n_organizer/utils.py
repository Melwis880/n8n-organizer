from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def sha1_json(data: Any) -> str:
    return sha1_text(json.dumps(data, ensure_ascii=False, sort_keys=True))


def safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def get_word_count(text: str) -> int:
    """
    Approximate word count for Markdown/JSON-like text.
    Works well enough for NotebookLM source-size splitting.
    """
    if not text:
        return 0

    words = re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)
    return len(words)