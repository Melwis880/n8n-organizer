from __future__ import annotations

import sys
from pathlib import Path
import traceback

from .classifier import classify_workflow
from .deduper import deduplicate_records
from .enricher import build_metadata
from .loader import iter_workflow_files, load_workflow_json
from .markdown_writer import write_category_markdowns
from .models import WorkflowRecord
from .normalizer import normalize_workflow
from .utils import sha1_json


def run(input_dir: Path, output_dir: Path) -> None:
    records: list[WorkflowRecord] = []
    errors: list[str] = []

    for file_path in iter_workflow_files(input_dir):
        try:
            raw_data = load_workflow_json(file_path)

            workflow_name = raw_data.get("name", file_path.stem)
            normalized_data = normalize_workflow(raw_data)

            raw_hash = sha1_json(raw_data)
            normalized_hash = sha1_json(normalized_data)

            metrics, score = classify_workflow(raw_data)

            metadata = build_metadata(
                source_file=file_path,
                workflow_name=workflow_name,
                workflow_id=raw_hash,
                normalized_hash=normalized_hash,
                metrics=metrics,
                score=score,
                data=raw_data,
            )

            records.append(
                WorkflowRecord(
                    source_file=str(file_path),
                    raw_data=raw_data,
                    normalized_data=normalized_data,
                    raw_hash=raw_hash,
                    normalized_hash=normalized_hash,
                    metrics=metrics,
                    score=score,
                    metadata=metadata,
                )
            )

        except Exception as exc:
            errors.append(f"{file_path}: {exc}")
            traceback.print_exc()

    unique_records, duplicate_records = deduplicate_records(records)

    write_category_markdowns(
        records=unique_records,
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "summary.txt"
    summary_path.write_text(
        "\n".join(
            [
                f"Total files processed: {len(records)}",
                f"Unique workflows: {len(unique_records)}",
                f"Duplicate workflows: {len(duplicate_records)}",
                f"Errors: {len(errors)}",
                "",
                "Error details:",
                *errors,
            ]
        ),
        encoding="utf-8",
    )
