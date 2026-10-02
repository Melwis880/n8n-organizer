from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def iter_workflow_files(input_dir: Path) -> Iterator[Path]:
    for path in input_dir.rglob("*.json"):
        if path.is_file():
            yield path


def load_workflow_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return json.load(f)