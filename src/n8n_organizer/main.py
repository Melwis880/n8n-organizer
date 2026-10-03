from __future__ import annotations

from pathlib import Path

from .classifier import classify_workflow, typed_nodes
from .config import EXCERPT_MAX_NODES, MAX_FILE_BYTES, MAX_WORDS_PER_FILE, REASONS_SHOWN
from .deduper import deduplicate_records
from .enricher import build_metadata
from .loader import iter_workflow_files, load_workflow_json
from .markdown_writer import write_category_markdowns
from .models import RunResult, WorkflowRecord
from .normalizer import normalize_workflow
from .trace import Tracer
from .utils import clean_name, clean_text, has_unsafe_chars, sha256_json, text_field, write_new_file


class UsageError(Exception):
    """Bad input or output location; reported to the user without a traceback."""


def check_locations(input_dir: Path, output_dir: Path) -> None:
    if not input_dir.is_dir():
        raise UsageError(f"input folder not found: {input_dir}")
    src = input_dir.resolve()
    dst = output_dir.resolve()
    if dst == src or src in dst.parents:
        raise UsageError("output folder must not be the input folder or inside it")
    if dst.exists() and (not dst.is_dir() or any(dst.iterdir())):
        raise UsageError(f"output folder must be empty or not exist yet: {output_dir}")


def build_record(path: Path, rel: str, data: dict) -> WorkflowRecord:
    name = clean_name(text_field(data.get("name"))) or clean_name(path.stem)
    normalized = normalize_workflow(data)
    raw_hash = sha256_json(data)
    normalized_hash = sha256_json(normalized)
    metrics, score = classify_workflow(data)
    working = typed_nodes(data)
    node_types = {t for _, t in working}
    metadata = build_metadata(rel, name, raw_hash, normalized_hash, metrics, score, node_types)
    nodes = [(clean_name(text_field(n.get("name"))), t) for n, t in working]
    # Keep only what a profile shows, so a record stays small however large the workflow is.
    excerpt = typed_nodes(normalized)[:EXCERPT_MAX_NODES]
    excerpt_nodes = [(clean_name(text_field(n.get("name"))), t) for n, t in excerpt]
    score.reasons = score.reasons[:REASONS_SHOWN]
    return WorkflowRecord(rel, nodes, excerpt_nodes, raw_hash, normalized_hash, metrics, score, metadata)


def write_summary(output_dir: Path, result: RunResult) -> None:
    lines = [
        f"Files found: {result.files_found}",
        f"Workflows analysed: {result.analysed}",
        f"Unique workflows: {result.unique}",
        f"Duplicates removed: {result.duplicates_exact + result.duplicates_normalized}"
        f" (exact: {result.duplicates_exact}, normalized: {result.duplicates_normalized})",
        f"Skipped: {sum(result.skipped.values())}",
        *[f"  {reason}: {count}" for reason, count in sorted(result.skipped.items())],
        f"Errors: {len(result.errors)}",
        *[f"  {e}" for e in result.errors],
        "",
        "Output files:",
        *[f"  {name}" for name in result.output_files],
    ]
    write_new_file(output_dir / "summary.txt", "\n".join(lines) + "\n")


def run(
    input_dir: Path,
    output_dir: Path,
    tracer: Tracer | None = None,
    max_words: int = MAX_WORDS_PER_FILE,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> RunResult:
    tracer = tracer or Tracer(None)
    try:
        return _run(input_dir, output_dir, tracer, max_words, max_file_bytes)
    finally:
        tracer.close()


def _run(input_dir: Path, output_dir: Path, tracer: Tracer, max_words: int, max_file_bytes: int) -> RunResult:
    check_locations(input_dir, output_dir)
    # Folder names only: the trace never holds a local absolute path.
    tracer.event("run_start", input=input_dir.resolve().name, output=output_dir.resolve().name)

    result = RunResult()
    records: list[WorkflowRecord] = []

    def unreadable_folder(folder: Path, exc: OSError) -> None:
        # Counted and traced: files in a folder that cannot be listed were never seen.
        result.skipped["unreadable_dir"] = result.skipped.get("unreadable_dir", 0) + 1
        rel = folder.relative_to(input_dir).as_posix()
        tracer.event("skipped", path=rel, reason="unreadable_dir", detail=clean_text(exc.strerror))

    for path in iter_workflow_files(input_dir, on_error=unreadable_folder):
        rel = path.relative_to(input_dir).as_posix()
        result.files_found += 1
        tracer.event("found", path=rel)
        if has_unsafe_chars(rel):
            # Bytes that are not UTF-8, line breaks or control characters in a file or folder name
            # would break summary.txt and the Markdown, or stop the run when it is written.
            result.skipped["unsafe_file_name"] = result.skipped.get("unsafe_file_name", 0) + 1
            tracer.event("skipped", path=rel, reason="unsafe_file_name")
            continue
        try:
            loaded = load_workflow_json(path, max_bytes=max_file_bytes)
            if loaded.skip_reason:
                result.skipped[loaded.skip_reason] = result.skipped.get(loaded.skip_reason, 0) + 1
                tracer.event("skipped", path=rel, reason=loaded.skip_reason)
                continue
            tracer.event("loaded", path=rel)
            record = build_record(path, rel, loaded.data)
        except Exception as exc:  # one bad file must not stop the run
            # An OSError message carries the full path as given to --input; strerror does not. Other
            # messages are left out: one built from a workflow value could carry its content.
            detail = clean_text(exc.strerror) if isinstance(exc, OSError) and exc.strerror else ""
            result.errors.append(f"{rel}: {type(exc).__name__}" + (f": {detail}" if detail else ""))
            tracer.event("error", path=rel, error=type(exc).__name__, detail=detail)
            continue
        records.append(record)
        tracer.event(
            "classified",
            path=rel,
            name=record.metadata.workflow_name,
            primary=record.metadata.primary_category,
            secondary=record.metadata.secondary_category,
            confidence=record.score.confidence,
            scores={c.value: s for c, s in record.score.scores.items()},
            raw_hash=record.raw_hash,
            normalized_hash=record.normalized_hash,
        )

    result.analysed = len(records)
    unique, duplicates = deduplicate_records(records)
    result.unique = len(unique)
    for dup in duplicates:
        if dup.kind == "exact":
            result.duplicates_exact += 1
        else:
            result.duplicates_normalized += 1
        tracer.event("duplicate", path=dup.record.source_file, kept=dup.kept.source_file, kind=dup.kind)

    try:
        written = write_category_markdowns(unique, output_dir, max_words=max_words)
        for name, in_file in written.items():
            for record in in_file:
                tracer.event("placed", path=record.source_file, file=name)
            tracer.event("written", file=name, workflows=len(in_file))
        result.output_files = sorted(written)
        write_summary(output_dir, result)
    except FileExistsError as exc:
        name = Path(exc.filename).name
        raise UsageError(f"output file appeared during the run and was not overwritten: {name}") from None
    tracer.event(
        "run_end",
        files_found=result.files_found,
        analysed=result.analysed,
        unique=result.unique,
        duplicates_exact=result.duplicates_exact,
        duplicates_normalized=result.duplicates_normalized,
        skipped=result.skipped,
        errors=len(result.errors),
    )
    return result
