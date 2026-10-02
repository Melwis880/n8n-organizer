from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from .config import (
    CORE_NODE_TYPES,
    NODE_CATEGORY_WEIGHTS,
    NODE_PREFIX_WEIGHTS,
    LABEL_ACRONYMS,
    SERVICE_LABELS,
    SERVICE_NODE_HINTS,
    SERVICE_NODE_WEIGHT,
    STICKY_NOTE_TYPE,
    TRIGGER_NODE_TYPES,
)
from .models import Category, WorkflowMetrics, WorkflowScore
from .utils import clean_text

BRANCH_TYPES = {
    "n8n-nodes-base.if",
    "n8n-nodes-base.switch",
    "n8n-nodes-base.merge",
}

CATEGORY_ORDER = list(Category)

LANGCHAIN_PREFIX = "@n8n/n8n-nodes-langchain."

# LangChain nodes that call a model themselves (besides lm*, chain* and agent* nodes).
LANGCHAIN_MODEL_NODES = {"openAi", "openAiAssistant", "informationExtractor", "textClassifier", "sentimentAnalysis"}


def working_nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Nodes that do work. Sticky notes are comments on the canvas, not steps."""
    return [n for n in data.get("nodes", []) if str(n.get("type", "")) != STICKY_NOTE_TYPE]


def is_trigger(node_type: str) -> bool:
    return node_type in TRIGGER_NODE_TYPES or node_type.endswith("Trigger")


def is_unweighted_service(node_type: str) -> bool:
    """A built-in n8n node for an outside service (Drive, Stripe, Todoist...) that has no weight of its own."""
    return (
        node_type.startswith("n8n-nodes-base.")
        and node_type not in CORE_NODE_TYPES
        and node_type not in NODE_CATEGORY_WEIGHTS
    )


def node_weights(node_type: str) -> dict[Category, int]:
    """Weights for one node: an exact key first, then the first matching prefix key (sorted)."""
    if node_type in NODE_CATEGORY_WEIGHTS:
        return NODE_CATEGORY_WEIGHTS[node_type]
    for prefix in sorted(NODE_PREFIX_WEIGHTS):
        if node_type.startswith(prefix):
            return NODE_PREFIX_WEIGHTS[prefix]
    return {}


def service_label(node_type: str) -> str:
    """Readable service name from a service node type: n8n-nodes-base.googleDriveTrigger -> Google Drive."""
    name = node_type.split(".", 1)[1]
    for suffix in ("Trigger", "Tool"):
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
    if name in SERVICE_LABELS:
        return SERVICE_LABELS[name]
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name).split()
    words = [w[0].upper() + w[1:] for w in words]
    return clean_text(" ".join(LABEL_ACRONYMS.get(w, w) for w in words), 60)


def is_llm_step(node_type: str) -> bool:
    return node_type.startswith(LANGCHAIN_PREFIX) or "openai" in node_type.lower()


def generates_text(node_type: str) -> bool:
    """A node that calls a language model itself: a model, chain or agent node, or an OpenAI node."""
    if not node_type.startswith(LANGCHAIN_PREFIX):
        return "openai" in node_type.lower()
    name = node_type[len(LANGCHAIN_PREFIX):]
    return name.startswith(("lm", "chain", "agent")) or name in LANGCHAIN_MODEL_NODES


def is_agent(node_type: str) -> bool:
    return node_type.startswith(LANGCHAIN_PREFIX + "agent")


def _llm_rank(node_type: str) -> int:
    if generates_text(node_type):
        return 0
    if node_type.startswith(LANGCHAIN_PREFIX + "embeddings"):
        return 1
    return 2


def llm_step_type(node_types: Iterable[str]) -> str | None:
    """The node type named in the LLM step rule's reason: a model, chain or agent node first, then
    embeddings, then any other LangChain node; sorted by name within each group."""
    steps = [t for t in node_types if is_llm_step(t)]
    return min(steps, key=lambda t: (_llm_rank(t), t)) if steps else None


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

    known_services = set()
    other_services = set()
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
        hints = [label for hint, label in SERVICE_NODE_HINTS.items() if hint.lower() in node_type.lower()]
        known_services.update(hints)
        if not hints and is_unweighted_service(node_type):
            other_services.add(service_label(node_type))

    metrics.trigger_nodes.sort()
    metrics.external_services = sorted((known_services | other_services) - {""})
    # Scoring and complexity count only the known services, so the measured accuracy still holds.
    metrics.integration_count = len(known_services)
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
        reasons.append("OpenAI node found -> AI_Content +4")

    if any(generates_text(t) for t in node_types):
        patterns.append("ai_generation")

    if any("langchain" in t.lower() for t in node_types):
        bonus[Category.AI_CONTENT] += 5
        reasons.append("LangChain node found -> AI_Content +5")

    if any(is_agent(t) for t in node_types):
        patterns.append("agentic_ai")

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
        for category, value in node_weights(node_type).items():
            scores[category] += value
            reasons.append(f"{node_type} -> {category.value} +{value}")

    node_types = {str(n.get("type", "")) for n in nodes}
    for node_type in sorted(node_types):
        if is_unweighted_service(node_type):
            scores[Category.DATA_INTEGRATION] += SERVICE_NODE_WEIGHT
            reasons.append(f"{node_type} (service) -> {Category.DATA_INTEGRATION.value} +{SERVICE_NODE_WEIGHT}")

    pattern_bonus, patterns, pattern_reasons = detect_patterns(node_types)
    for category, value in pattern_bonus.items():
        scores[category] += value
    reasons.extend(pattern_reasons)

    if metrics.has_ai_or_memory:
        scores[Category.AI_CONTENT] += 2
        reasons.append("AI or memory signal -> AI_Content +2")

    if metrics.integration_count >= 3:
        scores[Category.DATA_INTEGRATION] += 1
        scores[Category.ORCHESTRATION] += 1
        reasons.append("Three or more external services -> Data_Integration +1, Orchestration_Reliability +1")

    # Ties break by the fixed category order, so the same input always gives the same result.
    ranked = sorted(scores.items(), key=lambda x: (-x[1], CATEGORY_ORDER.index(x[0])))
    llm_type = llm_step_type(node_types)

    if llm_type:
        # Any LLM step makes it an AI workflow; repeated HTTP/Sheets/IF nodes must not outvote it.
        primary = Category.AI_CONTENT
        others = [(c, s) for c, s in ranked if c != primary]
        secondary = others[0][0] if others[0][1] > 0 else None
        confidence = "high"
        reasons.insert(0, f"LLM step found ({llm_type}) -> AI_Content by rule")
    elif ranked[0][1] == 0:
        primary, secondary, confidence = ranked[0][0], None, "none"
        reasons.insert(0, f"No scoring signal; placed in {primary.value} by default")
    else:
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
