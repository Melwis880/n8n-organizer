from __future__ import annotations

from .config import ANALYSIS_VERSION, CLIENT_PROBLEM_MAP
from .models import Category, WorkflowMetadata, WorkflowMetrics, WorkflowScore
from .utils import clean_text


def infer_project_purpose(node_types: set[str], primary_category: str) -> str:
    lowered = {t.lower() for t in node_types}

    if "n8n-nodes-base.httprequest" in lowered and "n8n-nodes-base.googlesheets" in lowered:
        return "Automated data flow that pulls data from external sources into a sheet or reporting layer."
    if any("openai" in t for t in lowered):
        return "AI-assisted flow for content generation, summarising, classification or chat."
    if "n8n-nodes-base.webhook" in lowered:
        return "Workflow that receives requests from external systems and runs integration logic."
    if primary_category == Category.DATA_INTEGRATION.value:
        return "Automation for collecting, transforming and reporting data."
    if primary_category == Category.AI_CONTENT.value:
        return "Automation for AI content, chatbots or information processing."
    return "Automation for integration, orchestration and operational process management."


def infer_complexity(metrics: WorkflowMetrics) -> str:
    score = (
        metrics.node_count * 1.0
        + metrics.branch_count * 2.0
        + (3 if metrics.has_error_handling else 0)
        + (4 if metrics.has_subworkflow else 0)
        + metrics.integration_count * 1.5
        + (2 if metrics.has_ai_or_memory else 0)
    )
    if score <= 10:
        return "Low"
    if score <= 24:
        return "Medium"
    return "High"


def infer_freelance_value(primary_category: str) -> str:
    if primary_category == Category.DATA_INTEGRATION.value:
        return "Useful for clients who need automated reporting, lead collection, scraping or data synchronisation."
    if primary_category == Category.AI_CONTENT.value:
        return "Useful for clients who want AI content generation, chatbots, knowledge access or social media automation."
    return "Useful for clients who need webhook integrations, fault tolerance, process orchestration or operational resilience."


def build_metadata(
    source_file: str,
    workflow_name: str,
    raw_hash: str,
    normalized_hash: str,
    metrics: WorkflowMetrics,
    score: WorkflowScore,
    node_types: set[str],
) -> WorkflowMetadata:
    primary = score.primary_category.value
    secondary = score.secondary_category.value if score.secondary_category else None

    return WorkflowMetadata(
        workflow_id=raw_hash,
        source_file=source_file,
        workflow_name=workflow_name,
        primary_category=primary,
        secondary_category=secondary,
        category_confidence=score.confidence,
        project_purpose=infer_project_purpose(node_types, primary),
        architectural_complexity=infer_complexity(metrics),
        freelance_value=infer_freelance_value(primary),
        client_problem_type=list(CLIENT_PROBLEM_MAP.get(primary, [])),
        node_count=metrics.node_count,
        connection_count=metrics.connection_count,
        branching_factor=metrics.branch_count,
        trigger_nodes=[clean_text(t) for t in metrics.trigger_nodes],
        external_services=metrics.external_services,
        key_patterns=score.key_patterns,
        dedup_fingerprint=normalized_hash,
        analysis_version=ANALYSIS_VERSION,
    )
