from __future__ import annotations

import errno
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from .config import MAX_FILE_BYTES


@dataclass
class LoadResult:
    data: dict[str, Any] | None
    skip_reason: str | None = None


def iter_workflow_files(
    input_dir: Path, on_error: Callable[[Path, OSError], None] | None = None
) -> Iterator[Path]:
    """Yield every *.json path under input_dir in sorted order, without following directory symlinks.

    A folder's files come first, then its subfolders, as os.walk gives them. The walk uses its own
    stack: os.walk before Python 3.12 recurses and stops the run on folders ~1,000 levels deep.
    A folder that cannot be listed goes to on_error; os.walk dropped it without a word.
    """
    stack = [Path(input_dir)]
    while stack:
        folder = stack.pop()
        try:
            with os.scandir(folder) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError as exc:
            if on_error is not None:
                on_error(folder, exc)
            continue
        subfolders = []
        for entry in entries:
            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False
            if is_dir:
                if not entry.is_symlink():
                    subfolders.append(folder / entry.name)
            elif entry.name.lower().endswith(".json"):
                yield folder / entry.name
        stack.extend(reversed(subfolders))


def is_workflow(data: Any) -> bool:
    nodes = data.get("nodes") if isinstance(data, dict) else None
    return isinstance(nodes, list) and all(isinstance(n, dict) for n in nodes)


def load_workflow_json(path: Path, max_bytes: int = MAX_FILE_BYTES) -> LoadResult:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return LoadResult(None, "symlink")
    # Checked before opening as well as after: opening a device can have side effects (a tape rewinds).
    if not stat.S_ISREG(mode):
        return LoadResult(None, "not_regular_file")
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
