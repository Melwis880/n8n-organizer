from __future__ import annotations

from copy import deepcopy
from typing import Any


VOLATILE_NODE_FIELDS = {
    "id",
    "position",
    "credentials",
    "webhookId",
}


def _normalize_node(node: dict[str, Any]) -> dict[str, Any]:
    clean = {}
    for key, value in node.items():
        if key in VOLATILE_NODE_FIELDS:
            continue

        if key == "name" and isinstance(value, str):
            clean[key] = value.strip().lower()
        else:
            clean[key] = value

    return clean


def normalize_workflow(data: dict[str, Any]) -> dict[str, Any]:
    cloned = deepcopy(data)

    nodes = cloned.get("nodes", [])
    connections = cloned.get("connections", {})

    normalized_nodes = [_normalize_node(node) for node in nodes]
    normalized_nodes = sorted(
        normalized_nodes,
        key=lambda x: (str(x.get("type", "")), str(x.get("name", "")))
    )

    normalized = {
        "name": cloned.get("name", "").strip(),
        "nodes": normalized_nodes,
        "connections": connections,
    }
    return normalized