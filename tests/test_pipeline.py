import json
import os
import unittest

import yaml

from n8n_organizer.main import run
from n8n_organizer.trace import Tracer

from helpers import AI_WF, DATA_WF, ORCH_WF, TempDirTest, node, workflow, write_json


def front_matters(text):
    """Yield every YAML block that opens a workflow section."""
    parts = text.split("\n---\n")
    for i, part in enumerate(parts):
        if part.startswith("workflow_id:"):
            yield yaml.safe_load(part)


class NormalRunTests(TempDirTest):
    def setUp(self):
        super().setUp()
        write_json(self.input / "Telegram" / "ai.json", AI_WF)
        write_json(self.input / "Sheets" / "data.json", DATA_WF)
        write_json(self.input / "Webhook" / "orch.json", ORCH_WF)

    def test_workflows_land_in_their_category_files(self):
        result = run(self.input, self.output)
        self.assertEqual((result.files_found, result.analysed, result.unique), (3, 3, 3))
        self.assertEqual(
            result.output_files, ["1-AI_Content.md", "1-Data_Integration.md", "1-Orchestration_Reliability.md"]
        )
        self.assertIn("# Workflow: AI support bot", (self.output / "1-AI_Content.md").read_text())
        self.assertIn("# Workflow: Daily report", (self.output / "1-Data_Integration.md").read_text())
        self.assertIn("# Workflow: Webhook router", (self.output / "1-Orchestration_Reliability.md").read_text())
        summary = (self.output / "summary.txt").read_text()
        self.assertIn("Workflows analysed: 3", summary)
        self.assertIn("Errors: 0", summary)

    def test_source_file_relative(self):
        run(self.input, self.output)
        sources = sorted(fm["source_file"] for fm in front_matters(self.output_text()))
        self.assertEqual(sources, ["Sheets/data.json", "Telegram/ai.json", "Webhook/orch.json"])
        self.assertNotIn(str(self.tmp), self.output_text())

    def test_code_fences_are_closed(self):
        run(self.input, self.output)
        for path in self.output.glob("*.md"):
            fences = [line for line in path.read_text().splitlines() if line.startswith("```")]
            self.assertEqual(len(fences) % 2, 0, path.name)


class EmptyInputTests(TempDirTest):
    def test_empty_folder(self):
        result = run(self.input, self.output)
        self.assertEqual((result.files_found, result.analysed, result.output_files), (0, 0, []))
        self.assertIn("Files found: 0", (self.output / "summary.txt").read_text())
        self.assertEqual(sorted(p.name for p in self.output.iterdir()), ["summary.txt"])


class SkipTests(TempDirTest):
    def test_invalid_json(self):
        (self.input / "broken.json").write_text('{"name": "x", "nodes": [', encoding="utf-8")
        (self.input / "deep.json").write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
        write_json(self.input / "ok.json", DATA_WF)
        result = run(self.input, self.output)
        self.assertEqual(result.skipped, {"invalid_json": 2})
        self.assertEqual(result.analysed, 1)

    def test_not_a_workflow(self):
        write_json(self.input / "list.json", [{"name": "a"}])
        write_json(self.input / "package.json", {"name": "pkg", "version": "1.0.0"})
        write_json(self.input / "bad_nodes.json", {"name": "x", "nodes": ["a", "b"]})
        write_json(self.input / "nodes_dict.json", {"name": "x", "nodes": {"a": 1}})
        result = run(self.input, self.output)
        self.assertEqual(result.skipped, {"not_a_workflow": 4})
        self.assertEqual(result.errors, [])

    def test_too_large(self):
        write_json(self.input / "big.json", workflow("Big", [node("Set", "n8n-nodes-base.set", notes="x" * 5000)]))
        write_json(self.input / "small.json", DATA_WF)
        result = run(self.input, self.output, max_file_bytes=2000)
        self.assertEqual(result.skipped, {"too_large": 1})
        self.assertEqual(result.analysed, 1)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks not supported")
    def test_symlinks(self):
        outside = self.tmp / "outside"
        write_json(outside / "secret.json", DATA_WF)
        os.symlink(outside / "secret.json", self.input / "link.json")
        os.symlink(outside, self.input / "linked_dir")
        result = run(self.input, self.output)
        self.assertEqual(result.skipped, {"symlink": 1})
        self.assertEqual(result.analysed, 0)

    def test_encoding(self):
        (self.input / "latin1.json").write_bytes('{"name": "Caf\xe9", "nodes": []}'.encode("latin-1"))
        (self.input / "bom.json").write_bytes(b"\xef\xbb\xbf" + json.dumps(DATA_WF).encode("utf-8"))
        result = run(self.input, self.output)
        self.assertEqual(result.skipped, {"not_utf8": 1})
        self.assertEqual(result.analysed, 1)


class DuplicateTests(TempDirTest):
    def test_exact(self):
        write_json(self.input / "a" / "one.json", DATA_WF)
        write_json(self.input / "b" / "two.json", DATA_WF)
        tracer = Tracer(self.tmp / "logs")
        result = run(self.input, self.output, tracer=tracer)
        self.assertEqual((result.unique, result.duplicates_exact, result.duplicates_normalized), (1, 1, 0))
        events = [json.loads(l) for l in tracer.path.read_text().splitlines()]
        dup = [e for e in events if e["event"] == "duplicate"][0]
        self.assertEqual((dup["path"], dup["kept"], dup["kind"]), ("b/two.json", "a/one.json", "exact"))

    def test_normalized(self):
        copy = json.loads(json.dumps(DATA_WF))
        for i, n in enumerate(copy["nodes"]):
            n["id"] = f"other-{i}"
            n["position"] = [100 * i, 50]
            n["credentials"] = {"googleApi": {"id": "9", "name": "Prod"}}
            n["webhookId"] = "abc"
        write_json(self.input / "one.json", DATA_WF)
        write_json(self.input / "two.json", copy)
        result = run(self.input, self.output)
        self.assertEqual((result.unique, result.duplicates_exact, result.duplicates_normalized), (1, 0, 1))

    def test_different_parameters_are_not_duplicates(self):
        other = json.loads(json.dumps(DATA_WF))
        other["nodes"][1]["parameters"] = {"url": "https://example.com/other"}
        write_json(self.input / "one.json", DATA_WF)
        write_json(self.input / "two.json", other)
        self.assertEqual(run(self.input, self.output).unique, 2)


class UntrustedTextTests(TempDirTest):
    NASTY = 'Evil: name\nwith "quotes" `ticks` ```fence``` \x1b[31m‮RTL​ # --- end'

    def test_names_cannot_break_yaml_or_markdown(self):
        wf = workflow(self.NASTY, [node(self.NASTY, "n8n-nodes-base.telegramTrigger"), node("Agent", "@n8n/n8n-nodes-langchain.agent")])
        write_json(self.input / "evil.json", wf)
        run(self.input, self.output)
        text = self.output_text()
        meta = list(front_matters(text))[0]
        self.assertNotIn("\n", meta["workflow_name"])
        self.assertNotIn("\x1b", text)
        self.assertNotIn("‮", text)
        self.assertNotIn("​", text)
        heading = [line for line in text.splitlines() if line.startswith("# Workflow:")]
        self.assertEqual(len(heading), 1)
        self.assertIn("Evil: name with", heading[0])
        fences = [line for line in text.splitlines() if line.startswith("```")]
        self.assertEqual(len(fences), 2)


class LeakTests(TempDirTest):
    def test_parameters_credentials_urls_and_notes_never_reach_output(self):
        wf = workflow(
            "Leaky",
            [
                node(
                    "Fetch",
                    "n8n-nodes-base.httpRequest",
                    parameters={
                        "url": "https://internal.example.com/api?token=SECRET_QUERY",
                        "headerParameters": {"parameters": [{"name": "Authorization", "value": "Bearer SECRET_HEADER"}]},
                    },
                    credentials={"httpHeaderAuth": {"id": "1", "name": "SECRET_CRED_NAME"}},
                ),
                node("Sticky Note", "n8n-nodes-base.stickyNote", parameters={"content": "SECRET_NOTE password=hunter2"}),
                node("Sheet", "n8n-nodes-base.googleSheets", parameters={"apiKey": "sk-SECRET_KEY"}),
            ],
        )
        write_json(self.input / "leaky.json", wf)
        tracer = Tracer(self.tmp / "logs")
        run(self.input, self.output, tracer=tracer)
        everything = self.output_text() + (self.output / "summary.txt").read_text() + tracer.path.read_text()
        self.assertNotIn("n8n-nodes-base.stickyNote", self.output_text())
        for secret in ("SECRET_QUERY", "SECRET_HEADER", "SECRET_CRED_NAME", "SECRET_NOTE", "hunter2", "sk-SECRET_KEY", "internal.example.com"):
            self.assertNotIn(secret, everything)


class DeterminismTests(TempDirTest):
    def test_two_runs_give_identical_files(self):
        for i, wf in enumerate([AI_WF, DATA_WF, ORCH_WF, DATA_WF]):
            write_json(self.input / f"f{i % 2}" / f"wf{i}.json", wf)
        second = self.tmp / "output2"
        run(self.input, self.output)
        run(self.input, second)
        first_files = sorted(p.name for p in self.output.iterdir())
        self.assertEqual(first_files, sorted(p.name for p in second.iterdir()))
        for name in first_files:
            self.assertEqual((self.output / name).read_bytes(), (second / name).read_bytes(), name)


class ChunkTests(TempDirTest):
    def test_word_limit_opens_a_second_file_without_losing_workflows(self):
        for i in range(4):
            write_json(self.input / f"folder{i}" / "wf.json", workflow(f"Report {i}", DATA_WF["nodes"] + [node(f"Extra {i}", "n8n-nodes-base.set")]))
        result = run(self.input, self.output, max_words=600)
        self.assertEqual(result.output_files[:2], ["1-Data_Integration.md", "2-Data_Integration.md"])
        names = [fm["workflow_name"] for fm in front_matters(self.output_text())]
        self.assertEqual(sorted(names), [f"Report {i}" for i in range(4)])


if __name__ == "__main__":
    unittest.main()
