from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Category(str, Enum):
    DATA_INTEGRATION = "Data_Integration"
    AI_CONTENT = "AI_Content"
    ORCHESTRATION = "Orchestration_Reliability"


@dataclass
class WorkflowMetrics:
    node_count: int = 0
    connection_count: int = 0
    branch_count: int = 0
    trigger_nodes: list[str] = field(default_factory=list)
    external_services: list[str] = field(default_factory=list)
    integration_count: int = 0
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
    analysis_version: str


@dataclass
class WorkflowRecord:
    source_file: str
    # Only node names and types are kept, never the workflow JSON: nothing else can reach the
    # output, and memory stays small however many workflows a run reads.
    nodes: list[tuple[str, str]]  # working nodes (name, type) in workflow order
    excerpt_nodes: list[tuple[str, str]]  # the same nodes in normalized order and naming
    raw_hash: str
    normalized_hash: str
    metrics: WorkflowMetrics
    score: WorkflowScore
    metadata: WorkflowMetadata


@dataclass
class RunResult:
    files_found: int = 0
    analysed: int = 0
    unique: int = 0
    duplicates_exact: int = 0
    duplicates_normalized: int = 0
    skipped: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
