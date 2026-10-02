import json
import shutil
import tempfile
import unittest
from pathlib import Path


def node(name, type_, **extra):
    data = {"id": f"id-{name}", "name": name, "type": type_, "position": [0, 0], "parameters": {}}
    data.update(extra)
    return data


def workflow(name, nodes, connections=None):
    return {"name": name, "nodes": nodes, "connections": connections or {}}


AI_WF = workflow(
    "AI support bot",
    [
        node("Telegram Trigger", "n8n-nodes-base.telegramTrigger"),
        node("Agent", "@n8n/n8n-nodes-langchain.agent"),
        node("OpenAI", "@n8n/n8n-nodes-langchain.openAi"),
        node("Reply", "n8n-nodes-base.telegram"),
    ],
    {
        "Telegram Trigger": {"main": [[{"node": "Agent", "type": "main", "index": 0}]]},
        "OpenAI": {"ai_languageModel": [[{"node": "Agent", "type": "ai_languageModel", "index": 0}]]},
        "Agent": {"main": [[{"node": "Reply", "type": "main", "index": 0}]]},
    },
)

DATA_WF = workflow(
    "Daily report",
    [
        node("Schedule", "n8n-nodes-base.scheduleTrigger"),
        node("Fetch", "n8n-nodes-base.httpRequest"),
        node("Sheet", "n8n-nodes-base.googleSheets"),
    ],
)

ORCH_WF = workflow(
    "Webhook router",
    [
        node("Webhook", "n8n-nodes-base.webhook"),
        node("Switch", "n8n-nodes-base.switch"),
        node("If", "n8n-nodes-base.if"),
        node("Respond", "n8n-nodes-base.respondToWebhook"),
        node("On error", "n8n-nodes-base.errorTrigger"),
    ],
)


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="n8n-organizer-test-"))
        self.input = self.tmp / "input"
        self.input.mkdir()
        self.output = self.tmp / "output"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def output_text(self, output=None) -> str:
        out = output or self.output
        return "\n".join(p.read_text(encoding="utf-8") for p in sorted(out.glob("*.md")))
