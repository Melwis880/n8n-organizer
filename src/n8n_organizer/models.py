from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Category(str, Enum):
    SEO_DATA = "SEO_Data_N8N"
    AI_CONTENT = "AI_Content_N8N"
    ARCH_SECURITY = "Architecture_Security_N8N"


@dataclass
class WorkflowMetrics:
    node_count: int = 0
    connection_count: int = 0
    branch_count: int = 0
    trigger_nodes: list[str] = field(default_factory=list)
    external_services: list[str] = field(default_factory=list)
    integration_count: int = 0
    max_path_length: int = 0
    has_error_handling: bool = False
    has_subworkflow: bool = False
    has_ai_or_memory: bool = False


@dataclass
class WorkflowScore:
    scores: dict[Category, int]
    primary_category: Category
    secondary_category: Category | None
    confidence: str
    reasons: list[str] = field(default_factory=list)
    key_patterns: list[str] = field(default_factory=list)


@dataclass
class WorkflowMetadata:
    workflow_id: str
    source_file: str
    workflow_name: str
    primary_category: str
    secondary_category: str | None
    category_confidence: str
    project_purpose: str
    architectural_complexity: str
    freelance_value: str
    client_problem_type: list[str]
    node_count: int
    connection_count: int
    branching_factor: int
    trigger_nodes: list[str]
    external_services: list[str]
    key_patterns: list[str]
    dedup_fingerprint: str
    analysis_version: str = "1.0.0"


@dataclass
class WorkflowRecord:
    source_file: str
    raw_data: dict[str, Any]
    normalized_data: dict[str, Any]
    raw_hash: str
    normalized_hash: str
    metrics: WorkflowMetrics
    score: WorkflowScore
    metadata: WorkflowMetadata