from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path, PurePosixPath

import yaml

from .classifier import working_nodes
from .config import MAX_WORDS_PER_FILE
from .models import Category, WorkflowRecord
from .utils import clean_text, get_word_count


def _yaml_block(metadata: dict) -> str:
    return yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()


def _format_node_inventory(record: WorkflowRecord) -> str:
    nodes = working_nodes(record.raw_data)
    if not nodes:
        return "- No nodes found"
    return "\n".join(
        f"- {clean_text(node.get('name')) or 'Unnamed'} ({clean_text(node.get('type')) or 'Unknown'})"
        for node in nodes
    )


def _bullets(items: list[str], empty: str) -> str:
    return "\n".join(f"- {clean_text(item, 300)}" for item in items) if items else f"- {empty}"


def _normalized_excerpt(record: WorkflowRecord, max_nodes: int = 15) -> str:
    nodes = [n for n in record.normalized_data.get("nodes", []) if str(n.get("type", "")) != "n8n-nodes-base.stickyNote"]
    excerpt = {
        "name": clean_text(record.normalized_data.get("name", "")),
        "nodes": [{"name": clean_text(n.get("name")), "type": clean_text(n.get("type"))} for n in nodes[:max_nodes]],
    }
    # indent=2 starts every line with a space or a brace, so no line can close the code fence.
    return json.dumps(excerpt, ensure_ascii=False, indent=2)


def folder_name(record: WorkflowRecord) -> str:
    parent = PurePosixPath(record.source_file).parent.name
    return parent or "(root)"


def workflow_to_markdown(record: WorkflowRecord) -> str:
    m = record.metadata
    services = ", ".join(m.external_services) if m.external_services else "None detected"
    problems = ", ".join(m.client_problem_type) if m.client_problem_type else "None"

    return f"""---
{_yaml_block(asdict(m))}
---

# Workflow: {m.workflow_name}

## 1. Executive Summary
{m.project_purpose}

## 2. Why This Matters
{m.freelance_value}

## 3. Node Inventory
{_format_node_inventory(record)}

## 4. Integration Surface
{services}

## 5. Detected Patterns
{_bullets(m.key_patterns, "none")}

## 6. Architecture Notes
Primary category: **{m.primary_category}**  
Secondary category: **{m.secondary_category or "None"}**  
Complexity: **{m.architectural_complexity}**

## 7. Reusable Insight
Client problems this pattern can answer: {problems}

## 8. Workflow Metrics
- Node count: {m.node_count}
- Connection count: {m.connection_count}
- Branching factor: {m.branching_factor}
- Confidence: {m.category_confidence}

## 9. Classification Reasons
{_bullets(record.score.reasons[:20], "No classification reasons recorded")}

## 10. Normalized JSON Excerpt
```json
{_normalized_excerpt(record)}
```
"""


def _folder_section(name: str, records: list[WorkflowRecord]) -> str:
    records = sorted(records, key=lambda r: (r.metadata.workflow_name.lower(), r.source_file))
    parts = ["---", "", f"# Folder: {clean_text(name)}", "", f"Workflows analysed in this folder: {len(records)}", ""]
    parts.extend(workflow_to_markdown(r) for r in records)
    return "\n".join(parts)


def _file_header(category: str, max_words: int) -> str:
    return f"# {category}\n\nCombined NotebookLM source file.\nWord limit per file: {max_words}\n"


def write_category_markdowns(
    records: list[WorkflowRecord],
    output_dir: Path,
    max_words: int = MAX_WORDS_PER_FILE,
) -> dict[str, list[WorkflowRecord]]:
    """Write one large file per category, starting a new numbered file when the word limit would be passed.

    Returns {output file name: records written to it}.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, list[WorkflowRecord]] = {}

    for category in Category:
        category_records = [r for r in records if r.metadata.primary_category == category.value]
        if not category_records:
            continue

        by_folder: dict[str, list[WorkflowRecord]] = {}
        for record in category_records:
            by_folder.setdefault(folder_name(record), []).append(record)

        header = _file_header(category.value, max_words)
        index = 1
        parts: list[str] = [header]
        words = get_word_count(header)
        in_file: list[WorkflowRecord] = []

        def flush() -> None:
            name = f"{index}-{category.value}.md"
            (output_dir / name).write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
            written[name] = list(in_file)

        for folder in sorted(by_folder):
            section = _folder_section(folder, by_folder[folder])
            section_words = get_word_count(section)
            if in_file and words + section_words > max_words:
                flush()
                index += 1
                parts = [header]
                words = get_word_count(header)
                in_file = []
            parts.append(section)
            words += section_words
            in_file.extend(by_folder[folder])

        flush()

    return written
