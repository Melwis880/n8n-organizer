from __future__ import annotations

from copy import deepcopy
from typing import Any

# Fields that change between exports of the same workflow; ignored when looking for duplicates.
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
    connections = cloned.get("connections")
    name = cloned.get("name")

    normalized_nodes = sorted(
        (_normalize_node(node) for node in cloned.get("nodes", [])),
        key=lambda x: (str(x.get("type", "")), str(x.get("name", ""))),
    )
    return {
        "name": name.strip() if isinstance(name, str) else "",
        "nodes": normalized_nodes,
        "connections": connections if isinstance(connections, dict) else {},
    }
