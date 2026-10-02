from __future__ import annotations

from collections import defaultdict
from typing import Any

from .config import NODE_CATEGORY_WEIGHTS, SERVICE_NODE_HINTS, STICKY_NOTE_TYPE, TRIGGER_NODE_TYPES
from .models import Category, WorkflowMetrics, WorkflowScore

BRANCH_TYPES = {
    "n8n-nodes-base.if",
    "n8n-nodes-base.switch",
    "n8n-nodes-base.merge",
}

CATEGORY_ORDER = list(Category)


def working_nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Nodes that do work. Sticky notes are comments on the canvas, not steps."""
    return [n for n in data.get("nodes", []) if str(n.get("type", "")) != STICKY_NOTE_TYPE]


def is_trigger(node_type: str) -> bool:
    return node_type in TRIGGER_NODE_TYPES or node_type.endswith("Trigger")


def count_connections(connections: Any) -> int:
    """Count edges: source node -> output type (main, ai_tool, ...) -> output slot -> target list."""
    if not isinstance(connections, dict):
        return 0
    total = 0
    for outputs in connections.values():
        if not isinstance(outputs, dict):
            continue
        for slots in outputs.values():
            if not isinstance(slots, list):
                continue
            for targets in slots:
                if isinstance(targets, list):
                    total += sum(1 for t in targets if isinstance(t, dict))
    return total


def extract_metrics(data: dict[str, Any]) -> WorkflowMetrics:
    nodes = working_nodes(data)
    metrics = WorkflowMetrics()
    metrics.node_count = len(nodes)
    metrics.connection_count = count_connections(data.get("connections"))

    service_names = set()
    for node in nodes:
        node_type = str(node.get("type", ""))
        node_name = node.get("name")

        if is_trigger(node_type):
            metrics.trigger_nodes.append(node_name if isinstance(node_name, str) and node_name else node_type)
        if node_type in BRANCH_TYPES:
            metrics.branch_count += 1
        if node_type == "n8n-nodes-base.errorTrigger":
            metrics.has_error_handling = True
        if node_type == "n8n-nodes-base.executeWorkflow":
            metrics.has_subworkflow = True
        if "openai" in node_type.lower() or "langchain" in node_type.lower() or "vector" in node_type.lower():
            metrics.has_ai_or_memory = True
        for hint, label in SERVICE_NODE_HINTS.items():
            if hint.lower() in node_type.lower():
                service_names.add(label)

    metrics.trigger_nodes.sort()
    metrics.external_services = sorted(service_names)
    metrics.integration_count = len(metrics.external_services)
    return metrics


def detect_patterns(node_types: set[str]) -> tuple[dict[Category, int], list[str], list[str]]:
    bonus: dict[Category, int] = defaultdict(int)
    patterns: list[str] = []
    reasons: list[str] = []

    def has(*types: str) -> bool:
        return all(t in node_types for t in types)

    if has("n8n-nodes-base.httpRequest", "n8n-nodes-base.googleSheets"):
        bonus[Category.DATA_INTEGRATION] += 6
        patterns.append("reporting_pipeline")
        reasons.append("HTTP Request + Google Sheets found -> Data_Integration +6")

    if "n8n-nodes-base.httpRequest" in node_types:
        bonus[Category.DATA_INTEGRATION] += 2
        patterns.append("api_ingestion")
        reasons.append("HTTP Request found -> Data_Integration +2")

    if has("n8n-nodes-base.webhook", "n8n-nodes-base.respondToWebhook"):
        bonus[Category.ORCHESTRATION] += 6
        patterns.append("webhook_request_lifecycle")
        reasons.append("Webhook request/response lifecycle found -> Orchestration_Reliability +6")

    if "n8n-nodes-base.errorTrigger" in node_types:
        bonus[Category.ORCHESTRATION] += 5
        patterns.append("error_handling")
        reasons.append("Error Trigger found -> Orchestration_Reliability +5")

    if any("openai" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 4
        patterns.append("ai_generation")
        reasons.append("OpenAI node found -> AI_Content +4")

    if any("langchain" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 5
        patterns.append("agentic_ai")
        reasons.append("LangChain node found -> AI_Content +5")

    if any("vector" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 4
        patterns.append("rag_or_vector_memory")
        reasons.append("Vector store / memory node found -> AI_Content +4")

    return dict(bonus), patterns, reasons


def classify_workflow(data: dict[str, Any]) -> tuple[WorkflowMetrics, WorkflowScore]:
    metrics = extract_metrics(data)
    nodes = working_nodes(data)

    scores: dict[Category, int] = {category: 0 for category in Category}
    reasons: list[str] = []

    for node in nodes:
        node_type = str(node.get("type", ""))
        for category, value in NODE_CATEGORY_WEIGHTS.get(node_type, {}).items():
            scores[category] += value
            reasons.append(f"{node_type} -> {category.value} +{value}")

    pattern_bonus, patterns, pattern_reasons = detect_patterns({str(n.get("type", "")) for n in nodes})
    for category, value in pattern_bonus.items():
        scores[category] += value
    reasons.extend(pattern_reasons)

    if metrics.branch_count >= 2:
        scores[Category.ORCHESTRATION] += 2
        reasons.append("Two or more branch nodes -> Orchestration_Reliability +2")

    if metrics.has_ai_or_memory:
        scores[Category.AI_CONTENT] += 2
        reasons.append("AI or memory signal -> AI_Content +2")

    if metrics.integration_count >= 3:
        scores[Category.DATA_INTEGRATION] += 1
        scores[Category.ORCHESTRATION] += 1
        reasons.append("Three or more external services -> Data_Integration +1, Orchestration_Reliability +1")

    # Ties break by the fixed category order, so the same input always gives the same result.
    ranked = sorted(scores.items(), key=lambda x: (-x[1], CATEGORY_ORDER.index(x[0])))
    primary, top_score = ranked[0]
    second, second_score = ranked[1]
    secondary = second if second_score > 0 else None

    delta_ratio = (top_score - second_score) / max(top_score, 1)
    if delta_ratio > 0.40:
        confidence = "high"
    elif delta_ratio > 0.20:
        confidence = "medium"
    else:
        confidence = "low"

    return metrics, WorkflowScore(
        scores=scores,
        primary_category=primary,
        secondary_category=secondary,
        confidence=confidence,
        reasons=reasons,
        key_patterns=patterns,
    )
