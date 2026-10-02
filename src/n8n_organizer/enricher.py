from __future__ import annotations

from pathlib import Path

from .config import ANALYSIS_VERSION, CLIENT_PROBLEM_MAP
from .models import WorkflowMetadata, WorkflowMetrics, WorkflowScore


def infer_project_purpose(data: dict, primary_category: str) -> str:
    node_types = {n.get("type", "").lower() for n in data.get("nodes", [])}

    if "n8n-nodes-base.httpsrequest".lower() in node_types and "n8n-nodes-base.googlesheets".lower() in node_types:
        return "Harici kaynaklardan veri çekip tabloya veya raporlama katmanına aktaran otomatik veri akışı."

    if any("openai" in t for t in node_types):
        return "AI destekli içerik üretimi, özetleme, sınıflandırma veya sohbet otomasyonu sağlayan akış."

    if "n8n-nodes-base.webhook".lower() in node_types:
        return "Harici sistemlerden gelen istekleri işleyip entegrasyon mantığı yürüten workflow."

    if primary_category == "SEO_Data_N8N":
        return "Veri toplama, veri dönüştürme ve raporlama amaçlı otomasyon akışı."

    if primary_category == "AI_Content_N8N":
        return "AI tabanlı içerik, chatbot veya bilgi işleme amaçlı otomasyon akışı."

    return "Entegrasyon, orkestrasyon ve operasyonel süreç yönetimi amaçlı otomasyon akışı."


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
        return "Düşük"
    if score <= 24:
        return "Orta"
    return "Yüksek"


def infer_freelance_value(primary_category: str) -> str:
    if primary_category == "SEO_Data_N8N":
        return "Otomatik raporlama, lead toplama, scraping ve veri senkronizasyonu ihtiyacı olan müşteriler için değerlidir."
    if primary_category == "AI_Content_N8N":
        return "AI içerik üretimi, chatbot, bilgi erişimi ve sosyal medya otomasyonu isteyen müşteriler için değerlidir."
    return "Webhook entegrasyonu, hata toleransı, süreç orkestrasyonu ve operasyonel dayanıklılık isteyen müşteriler için değerlidir."


def build_metadata(
    source_file: Path,
    workflow_name: str,
    workflow_id: str,
    normalized_hash: str,
    metrics: WorkflowMetrics,
    score: WorkflowScore,
    data: dict,
) -> WorkflowMetadata:
    primary = score.primary_category.value
    secondary = score.secondary_category.value if score.secondary_category else None

    return WorkflowMetadata(
        workflow_id=workflow_id,
        source_file=str(source_file),
        workflow_name=workflow_name or source_file.stem,
        primary_category=primary,
        secondary_category=secondary,
        category_confidence=score.confidence,
        project_purpose=infer_project_purpose(data, primary),
        architectural_complexity=infer_complexity(metrics),
        freelance_value=infer_freelance_value(primary),
        client_problem_type=CLIENT_PROBLEM_MAP.get(primary, []),
        node_count=metrics.node_count,
        connection_count=metrics.connection_count,
        branching_factor=metrics.branch_count,
        trigger_nodes=metrics.trigger_nodes,
        external_services=metrics.external_services,
        key_patterns=score.key_patterns,
        dedup_fingerprint=normalized_hash,
        analysis_version=ANALYSIS_VERSION,
    )