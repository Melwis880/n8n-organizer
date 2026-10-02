from __future__ import annotations

from .models import Category

ANALYSIS_VERSION = "1.0.0"

MAX_WORDS_PER_FILE = 450_000

NODE_CATEGORY_WEIGHTS: dict[str, dict[Category, int]] = {
    "n8n-nodes-base.googleSheets": {
        Category.SEO_DATA: 4,
    },
    "n8n-nodes-base.httpRequest": {
        Category.SEO_DATA: 3,
        Category.ARCH_SECURITY: 1,
    },
    "n8n-nodes-base.postgres": {
        Category.SEO_DATA: 4,
    },
    "n8n-nodes-base.mySql": {
        Category.SEO_DATA: 4,
    },
    "n8n-nodes-base.mongoDb": {
        Category.SEO_DATA: 4,
    },
    "n8n-nodes-base.airtable": {
        Category.SEO_DATA: 3,
    },
    "n8n-nodes-base.webhook": {
        Category.ARCH_SECURITY: 4,
    },
    "n8n-nodes-base.respondToWebhook": {
        Category.ARCH_SECURITY: 3,
    },
    "n8n-nodes-base.errorTrigger": {
        Category.ARCH_SECURITY: 6,
    },
    "n8n-nodes-base.if": {
        Category.ARCH_SECURITY: 2,
    },
    "n8n-nodes-base.switch": {
        Category.ARCH_SECURITY: 3,
    },
    "n8n-nodes-base.merge": {
        Category.ARCH_SECURITY: 2,
    },
    "n8n-nodes-base.wait": {
        Category.ARCH_SECURITY: 2,
    },
    "n8n-nodes-base.executeWorkflow": {
        Category.ARCH_SECURITY: 4,
    },
    "@n8n/n8n-nodes-langchain.openAi": {
        Category.AI_CONTENT: 5,
    },
    "@n8n/n8n-nodes-langchain.agent": {
        Category.AI_CONTENT: 6,
        Category.ARCH_SECURITY: 1,
    },
    "@n8n/n8n-nodes-langchain.vectorStore": {
        Category.AI_CONTENT: 5,
    },
    "@n8n/n8n-nodes-langchain.embeddingsOpenAi": {
        Category.AI_CONTENT: 5,
    },
    "n8n-nodes-base.openAi": {
        Category.AI_CONTENT: 5,
    },
    "n8n-nodes-base.telegram": {
        Category.AI_CONTENT: 2,
    },
    "n8n-nodes-base.slack": {
        Category.AI_CONTENT: 2,
        Category.ARCH_SECURITY: 1,
    },
    "n8n-nodes-base.twitter": {
        Category.AI_CONTENT: 3,
    },
    "n8n-nodes-base.linkedin": {
        Category.AI_CONTENT: 3,
    },
}

TRIGGER_NODE_TYPES = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.errorTrigger",
    "n8n-nodes-base.formTrigger",
}

SERVICE_NODE_HINTS = {
    "googleSheets": "Google Sheets",
    "postgres": "PostgreSQL",
    "mySql": "MySQL",
    "mongoDb": "MongoDB",
    "airtable": "Airtable",
    "openAi": "OpenAI",
    "telegram": "Telegram",
    "slack": "Slack",
    "discord": "Discord",
    "notion": "Notion",
    "github": "GitHub",
    "httpRequest": "HTTP API",
    "webhook": "Webhook",
}

CLIENT_PROBLEM_MAP = {
    "SEO_Data_N8N": [
        "Otomatik Raporlama İhtiyacı",
        "Lead Toplama",
        "Veri Senkronizasyonu",
    ],
    "AI_Content_N8N": [
        "İçerik Üretim Otomasyonu",
        "AI Chatbot / Destek Asistanı",
        "RAG / Kurumsal Bilgi Erişimi",
    ],
    "Architecture_Security_N8N": [
        "CRM / API Entegrasyonu",
        "Hata Yönetimi ve Operasyonel Dayanıklılık",
        "Onay Akışı / İş Süreci Otomasyonu",
    ],
}