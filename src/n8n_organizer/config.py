from __future__ import annotations

from .models import Category

ANALYSIS_VERSION = "2.0.0"

MAX_WORDS_PER_FILE = 450_000

MAX_FILE_BYTES = 10 * 1024 * 1024

STICKY_NOTE_TYPE = "n8n-nodes-base.stickyNote"

NODE_CATEGORY_WEIGHTS: dict[str, dict[Category, int]] = {
    "n8n-nodes-base.googleSheets": {
        Category.DATA_INTEGRATION: 4,
    },
    "n8n-nodes-base.httpRequest": {
        Category.DATA_INTEGRATION: 3,
        Category.ORCHESTRATION: 1,
    },
    "n8n-nodes-base.postgres": {
        Category.DATA_INTEGRATION: 4,
    },
    "n8n-nodes-base.mySql": {
        Category.DATA_INTEGRATION: 4,
    },
    "n8n-nodes-base.mongoDb": {
        Category.DATA_INTEGRATION: 4,
    },
    "n8n-nodes-base.airtable": {
        Category.DATA_INTEGRATION: 3,
    },
    "n8n-nodes-base.webhook": {
        Category.ORCHESTRATION: 4,
    },
    "n8n-nodes-base.respondToWebhook": {
        Category.ORCHESTRATION: 3,
    },
    "n8n-nodes-base.errorTrigger": {
        Category.ORCHESTRATION: 6,
    },
    "n8n-nodes-base.executeWorkflow": {
        Category.ORCHESTRATION: 4,
    },
    "n8n-nodes-base.executeWorkflowTrigger": {
        Category.ORCHESTRATION: 4,
    },
    "n8n-nodes-base.stopAndError": {
        Category.ORCHESTRATION: 3,
    },
    "@n8n/n8n-nodes-langchain.openAi": {
        Category.AI_CONTENT: 5,
    },
    "@n8n/n8n-nodes-langchain.agent": {
        Category.AI_CONTENT: 6,
        Category.ORCHESTRATION: 1,
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
}

# Built-in n8n nodes that move or reshape data inside the workflow. Any other
# n8n-nodes-base type without a weight above is an external service.
SERVICE_NODE_WEIGHT = 2

CORE_NODE_TYPES = {
    f"n8n-nodes-base.{name}"
    for name in (
        "aggregate", "code", "compareDatasets", "compression", "convertToFile", "cron", "crypto",
        "dateTime", "debugHelper", "editImage", "executeCommand", "executionData", "extractFromFile",
        "filter", "form", "formTrigger", "function", "functionItem", "html", "if", "interval",
        "itemLists", "limit", "localFileTrigger", "manualTrigger", "markdown", "merge",
        "moveBinaryData", "n8n", "noOp", "readBinaryFile", "readBinaryFiles", "readWriteFile",
        "removeDuplicates", "renameKeys", "scheduleTrigger", "set", "sort", "splitInBatches",
        "splitOut", "spreadsheetFile", "start", "stickyNote", "summarize", "switch", "wait",
        "workflowTrigger", "writeBinaryFile", "xml",
    )
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
    "Data_Integration": [
        "Automated reporting",
        "Lead collection",
        "Data synchronisation",
    ],
    "AI_Content": [
        "Content generation automation",
        "AI chatbot / support assistant",
        "RAG / company knowledge access",
    ],
    "Orchestration_Reliability": [
        "CRM / API integration",
        "Error handling and operational resilience",
        "Approval flows / business process automation",
    ],
}
