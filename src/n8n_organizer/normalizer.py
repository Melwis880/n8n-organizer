from __future__ import annotations

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
    # No deep copy: data is only read. Nodes are rebuilt by _normalize_node; parameters and
    # connections are shared with data and nothing changes them. A deep copy doubled peak memory
    # and failed on deeply nested parameters (RecursionError) that json.loads accepts.
    connections = data.get("connections")
    name = data.get("name")

    normalized_nodes = sorted(
        (_normalize_node(node) for node in data.get("nodes", [])),
        key=lambda x: (str(x.get("type", "")), str(x.get("name", ""))),
    )
    return {
        "name": name.strip() if isinstance(name, str) else "",
        "nodes": normalized_nodes,
        "connections": connections if isinstance(connections, dict) else {},
    }
