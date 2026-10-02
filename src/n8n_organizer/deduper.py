from __future__ import annotations

from .models import WorkflowRecord


def deduplicate_records(records: list[WorkflowRecord]) -> tuple[list[WorkflowRecord], list[WorkflowRecord]]:
    seen_normalized: dict[str, WorkflowRecord] = {}
    duplicates: list[WorkflowRecord] = []

    for record in records:
        if record.normalized_hash in seen_normalized:
            duplicates.append(record)
            continue
        seen_normalized[record.normalized_hash] = record

    unique_records = list(seen_normalized.values())
    return unique_records, duplicates