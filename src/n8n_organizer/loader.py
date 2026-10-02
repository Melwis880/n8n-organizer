from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .config import MAX_FILE_BYTES


@dataclass
class LoadResult:
    data: dict[str, Any] | None
    skip_reason: str | None = None


def iter_workflow_files(input_dir: Path) -> Iterator[Path]:
    """Yield every *.json path under input_dir in sorted order, without following directory symlinks."""
    for root, dirs, files in os.walk(input_dir, followlinks=False):
        dirs.sort()
        for name in sorted(files):
            if name.lower().endswith(".json"):
                yield Path(root) / name


def is_workflow(data: Any) -> bool:
    nodes = data.get("nodes") if isinstance(data, dict) else None
    return isinstance(nodes, list) and all(isinstance(n, dict) for n in nodes)


def load_workflow_json(path: Path, max_bytes: int = MAX_FILE_BYTES) -> LoadResult:
    if path.is_symlink():
        return LoadResult(None, "symlink")
    size = path.stat().st_size
    if size > max_bytes:
        return LoadResult(None, "too_large")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return LoadResult(None, "not_utf8")
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, RecursionError):
        return LoadResult(None, "invalid_json")
    if not is_workflow(data):
        return LoadResult(None, "not_a_workflow")
    return LoadResult(data)
