from __future__ import annotations

from collections import Counter
from typing import Any

from .classifier import iter_edges, typed_nodes
from .utils import clean_name, sha256_json, text_field

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


def structure_fingerprint(data: dict[str, Any]) -> str:
    """dedup_fingerprint in the output: a hash of what a profile shows (workflow name, node types,
    node names as cleaned for the output, which node feeds which), never of parameter values.
    The normalized hash covers parameters: anyone who knew the template could confirm guesses of
    a value filled into it, such as a 9-digit chat ID in about a second. Duplicates are still
    found with the full hashes, which never leave the run."""
    nodes = typed_nodes(data)
    # Names are cleaned once per node (at most MAX_NODES); an edge to or from a name that is no
    # node is left out, so 10 MB of made-up edges costs a dictionary lookup each.
    shown = {raw: clean_name(raw).lower() for raw in (text_field(n.get("name")) for n, _ in nodes)}
    edges = Counter(
        (shown[source], shown[target])
        for source, target in (
            (source, target.get("node")) for source, target in iter_edges(data.get("connections"))
        )
        if source in shown and isinstance(target, str) and target in shown
    )
    return sha256_json({
        "name": clean_name(data.get("name")).lower(),
        "nodes": sorted((node_type, shown[text_field(n.get("name"))]) for n, node_type in nodes),
        "edges": sorted(edges.items()),
    })
