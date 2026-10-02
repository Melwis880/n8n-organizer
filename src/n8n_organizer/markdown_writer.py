from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
import yaml

from .config import MAX_WORDS_PER_FILE
from .models import Category, WorkflowRecord
from .utils import get_word_count


def _yaml_block(metadata: dict) -> str:
    return yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()


def _format_node_inventory(record: WorkflowRecord) -> str:
    nodes = record.raw_data.get("nodes", [])
    if not nodes:
        return "- No nodes found"

    return "\n".join(
        f"- {node.get('name', 'Unnamed')} ({node.get('type', 'Unknown')})"
        for node in nodes
    )


def _format_patterns(record: WorkflowRecord) -> str:
    if not getattr(record.score, "key_patterns", None):
        return "- none"

    return "\n".join(f"- {pattern}" for pattern in record.score.key_patterns)


def _format_reasons(record: WorkflowRecord, limit: int = 20) -> str:
    reasons = getattr(record.score, "reasons", [])[:limit]
    if not reasons:
        return "- No classification reasons recorded"

    return "\n".join(f"- {reason}" for reason in reasons)


def _build_normalized_excerpt(record: WorkflowRecord, max_nodes: int = 15) -> dict:
    return {
        "name": record.normalized_data.get("name", ""),
        "nodes": [
            {
                "name": node.get("name"),
                "type": node.get("type"),
            }
            for node in record.normalized_data.get("nodes", [])[:max_nodes]
        ],
    }


def _get_repo_name(record: WorkflowRecord) -> str:
    source_path = Path(record.source_file)

    parts = source_path.parts
    if len(parts) >= 2:
        return parts[-2]

    return source_path.stem


def _workflow_to_markdown(record: WorkflowRecord) -> str:
    metadata_yaml = _yaml_block(asdict(record.metadata))
    node_inventory = _format_node_inventory(record)
    pattern_lines = _format_patterns(record)
    reasons_lines = _format_reasons(record)
    normalized_excerpt = _build_normalized_excerpt(record)

    integration_surface = (
        ", ".join(record.metadata.external_services)
        if record.metadata.external_services
        else "Bilinmiyor"
    )

    client_problem_types = (
        ", ".join(record.metadata.client_problem_type)
        if record.metadata.client_problem_type
        else "Bilinmiyor"
    )

    normalized_json = json.dumps(
        normalized_excerpt,
        ensure_ascii=False,
        indent=2,
    )

    return f"""---
{metadata_yaml}
---

# Workflow: {record.metadata.workflow_name}

## 1. Executive Summary
{record.metadata.project_purpose}

## 2. Why This Matters
{record.metadata.freelance_value}

## 3. Node Inventory
{node_inventory}

## 4. Integration Surface
{integration_surface}

## 5. Detected Patterns
{pattern_lines}

## 6. Architecture Notes
Ana kategori: **{record.metadata.primary_category}**  
İkincil kategori: **{record.metadata.secondary_category or "Yok"}**  
Karmaşıklık: **{record.metadata.architectural_complexity}**

## 7. Reusable Freelancer Insight
Bu akış özellikle şu müşteri problemlerine örnek olabilir: {client_problem_types}

## 8. Raw Workflow Summary
- Node count: {record.metadata.node_count}
- Connection count: {record.metadata.connection_count}
- Branching factor: {record.metadata.branching_factor}
- Confidence: {record.metadata.category_confidence}

## 9. Classification Reasons
{reasons_lines}

## 10. Normalized JSON Excerpt
```json
{normalized_json}

"""

def _repo_section_to_markdown(repo_name: str, records: list[WorkflowRecord]) -> str:
    records = sorted(
    records,
    key=lambda record: (record.metadata.workflow_name or "").lower(),
)
    parts: list[str] = [
    "",
    "---",
    "",
    f"# REPO: {repo_name}",
    "",
    f"Bu repo içindeki analiz edilen workflow sayısı: {len(records)}",
    "",
    "---",
    "",
]

    for record in records:
        parts.append(_workflow_to_markdown(record))
    

    return "\n".join(parts)


def _write_chunk_file(
output_dir: Path,
category_name: str,
chunk_index: int,
content_parts: list[str],
) -> None:
    output_path = output_dir / f"{chunk_index}-{category_name}.md"
    output_path.write_text(
    "\n".join(content_parts).strip() + "\n",
    encoding="utf-8",   
    )

def write_category_markdowns(records: list[WorkflowRecord], output_dir: Path) -> None:
    """
    Write large category-level Markdown files.

    Instead of writing one Markdown file per repo, this function groups analyses
    by category and keeps appending repo sections until MAX_WORDS_PER_FILE is reached.
    Then it creates chunked files like:

    1-AI_Content_N8N.md
    2-AI_Content_N8N.md
    1-SEO_Data_N8N.md
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    grouped_by_category: dict[str, list[WorkflowRecord]] = {
        Category.SEO_DATA.value: [],
        Category.AI_CONTENT.value: [],
        Category.ARCH_SECURITY.value: [],
    }

    # HATA BURADAYDI: 'reload' yerine 'records' yapıldı ve girintiler düzeltildi.
    for record in records:
        category = record.metadata.primary_category

        if category not in grouped_by_category:
            grouped_by_category[category] = []

        grouped_by_category[category].append(record)

    for category_name, category_records in grouped_by_category.items():
        if not category_records:
            continue

        grouped_by_repo: dict[str, list[WorkflowRecord]] = {}

        for record in category_records:
            repo_name = _get_repo_name(record)

            if repo_name not in grouped_by_repo:
                grouped_by_repo[repo_name] = []

            grouped_by_repo[repo_name].append(record)

        chunk_index = 1
        current_word_count = 0

        current_parts: list[str] = [
            f"# {category_name}",
            "",
            f"NotebookLM birleşik kaynak dosyası.",
            f"Kelime sınırı: {MAX_WORDS_PER_FILE}",
            "",
            "---",
            "",
        ]

        current_word_count = get_word_count("\n".join(current_parts))

        for repo_name in sorted(grouped_by_repo.keys()):
            repo_section = _repo_section_to_markdown(
                repo_name=repo_name,
                records=grouped_by_repo[repo_name],
            )

            repo_word_count = get_word_count(repo_section)

            if (
                current_word_count + repo_word_count > MAX_WORDS_PER_FILE
                and len(current_parts) > 6
            ):
                _write_chunk_file(
                    output_dir=output_dir,
                    category_name=category_name,
                    chunk_index=chunk_index,
                    content_parts=current_parts,
                )

                chunk_index += 1

                current_parts = [
                    f"# {category_name}",
                    "",
                    f"NotebookLM birleşik kaynak dosyası.",
                    f"Kelime sınırı: {MAX_WORDS_PER_FILE}",
                    "",
                    "---",
                    "",
                ]

                current_word_count = get_word_count("\n".join(current_parts))

            current_parts.append(repo_section)
            current_word_count += repo_word_count

        if len(current_parts) > 6:
            _write_chunk_file(
                output_dir=output_dir,
                category_name=category_name,
                chunk_index=chunk_index,
                content_parts=current_parts,
            )