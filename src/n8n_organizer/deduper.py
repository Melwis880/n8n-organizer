from __future__ import annotations

from dataclasses import dataclass

from .models import WorkflowRecord


@dataclass
class Duplicate:
    record: WorkflowRecord
    kept: WorkflowRecord
    kind: str  # "exact" (same JSON) or "normalized" (same after ignoring ids, positions, credentials)


def deduplicate_records(records: list[WorkflowRecord]) -> tuple[list[WorkflowRecord], list[Duplicate]]:
    """Keep the first record of each group, in the order given (sorted paths, so the result is stable)."""
    by_raw: dict[str, WorkflowRecord] = {}
    by_normalized: dict[str, WorkflowRecord] = {}
    unique: list[WorkflowRecord] = []
    duplicates: list[Duplicate] = []

    for record in records:
        if record.raw_hash in by_raw:
            duplicates.append(Duplicate(record, by_raw[record.raw_hash], "exact"))
            continue
        if record.normalized_hash in by_normalized:
            duplicates.append(Duplicate(record, by_normalized[record.normalized_hash], "normalized"))
            continue
        by_raw[record.raw_hash] = record
        by_normalized[record.normalized_hash] = record
        unique.append(record)

    return unique, duplicates
