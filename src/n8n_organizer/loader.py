from __future__ import annotations

import errno
import json
import os
import stat
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
    # O_NOFOLLOW: a file swapped for a symlink after the check above is still not followed.
    # O_NONBLOCK: opening a FIFO does not wait for a writer.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            return LoadResult(None, "symlink")
        raise
    with os.fdopen(fd, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode):
            return LoadResult(None, "not_regular_file")
        if info.st_size > max_bytes:
            return LoadResult(None, "too_large")
        # Read one byte past the limit, so a file that grew after fstat is caught too.
        raw = f.read(max_bytes + 1)
    if len(raw) > max_bytes:
        return LoadResult(None, "too_large")
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
