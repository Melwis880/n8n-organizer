from __future__ import annotations

from collections import defaultdict
from typing import Any

from .config import NODE_CATEGORY_WEIGHTS, SERVICE_NODE_HINTS, TRIGGER_NODE_TYPES
from .models import Category, WorkflowMetrics, WorkflowScore


def extract_metrics(data: dict[str, Any]) -> WorkflowMetrics:
    nodes = data.get("nodes", [])
    connections = data.get("connections", {})

    metrics = WorkflowMetrics()
    metrics.node_count = len(nodes)
    metrics.connection_count = sum(len(v.get("main", [])) for v in connections.values() if isinstance(v, dict))

    branch_types = {
        "n8n-nodes-base.if",
        "n8n-nodes-base.switch",
        "n8n-nodes-base.merge",
    }

    service_names = set()

    for node in nodes:
        node_type = node.get("type", "")
        node_name = node.get("name", "")

        if node_type in TRIGGER_NODE_TYPES:
            metrics.trigger_nodes.append(node_name or node_type)

        if node_type in branch_types:
            metrics.branch_count += 1

        if node_type == "n8n-nodes-base.errorTrigger":
            metrics.has_error_handling = True

        if node_type == "n8n-nodes-base.executeWorkflow":
            metrics.has_subworkflow = True

        if "openAi" in node_type or "langchain" in node_type or "vector" in node_type.lower():
            metrics.has_ai_or_memory = True

        for hint, label in SERVICE_NODE_HINTS.items():
            if hint.lower() in node_type.lower():
                service_names.add(label)

    metrics.external_services = sorted(service_names)
    metrics.integration_count = len(metrics.external_services)
    metrics.max_path_length = metrics.node_count  # placeholder, later graph analysis can improve this

    return metrics


def detect_patterns(data: dict[str, Any]) -> tuple[dict[Category, int], list[str], list[str]]:
    nodes = data.get("nodes", [])
    node_types = {n.get("type", "") for n in nodes}

    bonus = defaultdict(int)
    patterns: list[str] = []
    reasons: list[str] = []

    def has(*types: str) -> bool:
        return all(t in node_types for t in types)

    if has("n8n-nodes-base.httpRequest", "n8n-nodes-base.googleSheets"):
        bonus[Category.SEO_DATA] += 6
        patterns.append("reporting_pipeline")
        reasons.append("HTTP Request + Google Sheets tespit edildi")

    if "n8n-nodes-base.httpRequest" in node_types:
        bonus[Category.SEO_DATA] += 2
        patterns.append("api_ingestion")

    if has("n8n-nodes-base.webhook", "n8n-nodes-base.respondToWebhook"):
        bonus[Category.ARCH_SECURITY] += 6
        patterns.append("webhook_request_lifecycle")
        reasons.append("Webhook request lifecycle pattern tespit edildi")

    if "n8n-nodes-base.errorTrigger" in node_types:
        bonus[Category.ARCH_SECURITY] += 5
        patterns.append("error_handling")
        reasons.append("Error handling node tespit edildi")

    if any("openai" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 4
        patterns.append("ai_generation")
        reasons.append("OpenAI tabanlı node bulundu")

    if any("langchain" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 5
        patterns.append("agentic_ai")
        reasons.append("LangChain tabanlı node bulundu")

    if any("vector" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 4
        patterns.append("rag_or_vector_memory")
        reasons.append("Vector store / memory pattern bulundu")

    return dict(bonus), patterns, reasons


def classify_workflow(data: dict[str, Any]) -> tuple[WorkflowMetrics, WorkflowScore]:
    metrics = extract_metrics(data)

    scores = defaultdict(int)
    reasons: list[str] = []

    for node in data.get("nodes", []):
        node_type = node.get("type", "")
        weight_map = NODE_CATEGORY_WEIGHTS.get(node_type, {})
        for category, value in weight_map.items():
            scores[category] += value
            reasons.append(f"{node_type} -> {category.value} +{value}")

    pattern_bonus, patterns, pattern_reasons = detect_patterns(data)
    for category, bonus in pattern_bonus.items():
        scores[category] += bonus

    reasons.extend(pattern_reasons)

    if metrics.branch_count >= 2:
        scores[Category.ARCH_SECURITY] += 2
        reasons.append("Yoğun branching tespit edildi -> Architecture_Security_N8N +2")

    if metrics.has_ai_or_memory:
        scores[Category.AI_CONTENT] += 2
        reasons.append("AI/memory sinyali bulundu -> AI_Content_N8N +2")

    if metrics.integration_count >= 3:
        scores[Category.SEO_DATA] += 1
        scores[Category.ARCH_SECURITY] += 1
        reasons.append("Çoklu entegrasyon yüzeyi tespit edildi")

    for category in Category:
        scores[category] += 0

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else None

    top_score = ranked[0][1]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    delta_ratio = (top_score - second_score) / max(top_score, 1)

    if delta_ratio > 0.40:
        confidence = "high"
    elif delta_ratio > 0.20:
        confidence = "medium"
    else:
        confidence = "low"

    score = WorkflowScore(
        scores=dict(scores),
        primary_category=primary,
        secondary_category=secondary,
        confidence=confidence,
        reasons=reasons,
        key_patterns=patterns,
    )

    return metrics, score