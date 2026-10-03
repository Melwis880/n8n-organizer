from __future__ import annotations

import errno
import json
import os
import stat
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


def _open_log(path: Path) -> TextIO:
    """Open the trace file for appending. A symlink planted at the predictable dated name is not
    followed (it would append to any file the user can write) and nothing but a regular file is
    used (O_NONBLOCK: a FIFO there fails at once instead of waiting for a reader). A new file is
    readable by its owner only: it holds workflow and file names."""
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError(errno.EINVAL, "trace path is not a regular file")
    return os.fdopen(fd, "a", encoding="utf-8", buffering=1)


class Tracer:
    """Append one JSON line per event, linked by run_id and seq. Never receives workflow content."""

    def __init__(self, log_dir: Path | None, debug: bool = False, stream: TextIO | None = None) -> None:
        self.run_id = uuid.uuid4().hex[:12]
        self.seq = 0
        self.debug = debug
        self.stream = stream if stream is not None else sys.stderr
        self.path: Path | None = None
        self._file: TextIO | None = None
        self._warned = False
        if log_dir is not None:
            now = datetime.now(timezone.utc)
            self.path = log_dir / f"{now:%Y-%m-%d}.jsonl"

    def event(self, event_name: str, /, **fields: Any) -> None:
        self.seq += 1
        record = {
            "run_id": self.run_id,
            "seq": self.seq,
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "event": event_name,
            **fields,
        }
        # ensure_ascii keeps control and bidi characters from file names escaped in the log and the terminal.
        line = json.dumps(record, ensure_ascii=True, sort_keys=False)
        if self.path is not None:
            try:
                if self._file is None:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    # Opened once per run, line buffered: every event is on disk as soon as it is written.
                    self._file = _open_log(self.path)
                self._file.write(line + "\n")
            except OSError as exc:
                if not self._warned:
                    print(f"n8n-organizer: warning: cannot write trace ({exc.strerror}); continuing", file=self.stream)
                    self._warned = True
        if self.debug:
            print(line, file=self.stream)

    def close(self) -> None:
        """Close the trace file; a later event opens it again."""
        if self._file is not None:
            self._file.close()
            self._file = None
