from __future__ import annotations

from .models import Category

ANALYSIS_VERSION = "2.2.0"

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
    "@n8n/n8n-nodes-langchain.embeddingsOpenAi": {
        Category.AI_CONTENT: 5,
    },
    "n8n-nodes-base.openAi": {
        Category.AI_CONTENT: 5,
    },
}

# Weights for node families whose real types share a prefix (vectorStoreQdrant, vectorStorePinecone...).
# There is no node type named exactly "vectorStore", so an exact key never matched.
NODE_PREFIX_WEIGHTS: dict[str, dict[Category, int]] = {
    "@n8n/n8n-nodes-langchain.vectorStore": {
        Category.AI_CONTENT: 5,
    },
}

# Built-in n8n nodes that work inside n8n (move or reshape data, n8n's own events, demo data).
# Any other n8n-nodes-base type without a weight above is an external service.
SERVICE_NODE_WEIGHT = 2

CORE_NODE_TYPES = {
    f"n8n-nodes-base.{name}"
    for name in (
        "aggregate", "aiTransform", "code", "compareDatasets", "compression", "convertToFile", "cron",
        "crypto", "dateTime", "debugHelper", "editImage", "executeCommand", "executeCommandTool",
        "executionData", "extractFromFile", "filter", "form", "formTrigger", "function", "functionItem",
        "html", "htmlExtract", "iCal", "if", "interval", "itemLists", "limit", "localFileTrigger",
        "manualTrigger", "markdown", "merge", "moveBinaryData", "n8n", "n8nTrainingCustomerDatastore",
        "n8nTrainingCustomerMessenger", "n8nTrigger", "noOp", "readBinaryFile", "readBinaryFiles",
        "readPDF", "readWriteFile", "removeDuplicates", "renameKeys", "scheduleTrigger", "set", "sort",
        "splitInBatches", "splitOut", "spreadsheetFile", "start", "stickyNote", "summarize", "switch",
        "totp", "wait", "workflowTrigger", "writeBinaryFile", "xml",
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

# Display names for service node types whose camelCase split reads badly. Display only: the
# scoring rules count services from SERVICE_NODE_HINTS above.
SERVICE_LABELS = {
    "activeCampaign": "ActiveCampaign",
    "bambooHr": "BambooHR",
    "circleCi": "CircleCI",
    "clickUp": "ClickUp",
    "coinGecko": "CoinGecko",
    "convertKit": "ConvertKit",
    "crateDb": "CrateDB",
    "customerIo": "Customer.io",
    "deepL": "DeepL",
    "emailReadImap": "Email (IMAP)",
    "emailSend": "Email (SMTP)",
    "erpNext": "ERPNext",
    "getResponse": "GetResponse",
    "goToWebinar": "GoToWebinar",
    "graphql": "GraphQL",
    "highLevel": "HighLevel",
    "hubspot": "HubSpot",
    "jotForm": "JotForm",
    "linkedIn": "LinkedIn",
    "mailerLite": "MailerLite",
    "messageBird": "MessageBird",
    "microsoftOneDrive": "Microsoft OneDrive",
    "mondayCom": "monday.com",
    "nextCloud": "Nextcloud",
    "nocoDb": "NocoDB",
    "openWeatherMap": "OpenWeatherMap",
    "pagerDuty": "PagerDuty",
    "payPal": "PayPal",
    "postHog": "PostHog",
    "questDb": "QuestDB",
    "rssFeedRead": "RSS",
    "sendGrid": "SendGrid",
    "serviceNow": "ServiceNow",
    "surveyMonkey": "SurveyMonkey",
    "timescaleDb": "TimescaleDB",
    "uptimeRobot": "UptimeRobot",
    "whatsApp": "WhatsApp",
    "wooCommerce": "WooCommerce",
    "wordpress": "WordPress",
    "youTube": "YouTube",
}

# Words written in capitals when a label is built from a camelCase type name (awsSes -> AWS SES).
LABEL_ACRONYMS = {
    word.capitalize(): word
    for word in (
        "AI", "API", "AWS", "CI", "CRM", "DB", "DHL", "FTP", "HR", "HTML", "IO", "MQTT", "AMQP",
        "NASA", "PDF", "S3", "SES", "SNS", "SQL", "SQS", "SSE", "SSH", "TLS", "TOTP",
    )
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
