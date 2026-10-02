import unittest

from n8n_organizer.classifier import classify_workflow, count_connections, extract_metrics, llm_step_type
from n8n_organizer.models import Category

from helpers import AI_WF, DATA_WF, ORCH_WF, node, workflow


class CategoryTests(unittest.TestCase):
    def test_each_fixture_gets_its_category(self):
        self.assertEqual(classify_workflow(AI_WF)[1].primary_category, Category.AI_CONTENT)
        self.assertEqual(classify_workflow(DATA_WF)[1].primary_category, Category.DATA_INTEGRATION)
        self.assertEqual(classify_workflow(ORCH_WF)[1].primary_category, Category.ORCHESTRATION)

    def test_no_signal_falls_back_to_first_category_with_confidence_none(self):
        _, score = classify_workflow(workflow("Empty", [node("Set", "n8n-nodes-base.set")]))
        self.assertEqual(score.primary_category, Category.DATA_INTEGRATION)
        self.assertIsNone(score.secondary_category)
        self.assertEqual(score.confidence, "none")
        self.assertTrue(score.reasons[0].startswith("No scoring signal"))


class LlmRuleTests(unittest.TestCase):
    HEAVY_DATA = [node(f"Fetch {i}", "n8n-nodes-base.httpRequest") for i in range(6)] + [
        node(f"Sheet {i}", "n8n-nodes-base.googleSheets") for i in range(4)
    ]

    def test_llm_step_wins_over_many_data_nodes(self):
        wf = workflow("Enrich leads", self.HEAVY_DATA + [node("Model", "@n8n/n8n-nodes-langchain.lmChatOpenAi")])
        _, score = classify_workflow(wf)
        self.assertEqual(score.primary_category, Category.AI_CONTENT)
        self.assertEqual(score.secondary_category, Category.DATA_INTEGRATION)
        self.assertEqual(score.confidence, "high")
        self.assertIn("LLM step found (@n8n/n8n-nodes-langchain.lmChatOpenAi)", score.reasons[0])

    def test_any_langchain_node_counts(self):
        wf = workflow("Gemini bot", self.HEAVY_DATA + [node("Gemini", "@n8n/n8n-nodes-langchain.lmChatGoogleGemini")])
        self.assertEqual(classify_workflow(wf)[1].primary_category, Category.AI_CONTENT)

    def test_base_openai_node_counts(self):
        wf = workflow("Summarise", self.HEAVY_DATA + [node("OpenAI", "n8n-nodes-base.openAi")])
        self.assertEqual(classify_workflow(wf)[1].primary_category, Category.AI_CONTENT)

    def test_sticky_note_mentioning_ai_does_not_count(self):
        wf = workflow("No AI", self.HEAVY_DATA + [node("Sticky Note", "n8n-nodes-base.stickyNote", parameters={"content": "OpenAI"})])
        self.assertEqual(classify_workflow(wf)[1].primary_category, Category.DATA_INTEGRATION)

    def test_reason_names_the_first_llm_type_in_sorted_order(self):
        # Set order changes between Python runs; the reason line must not.
        given = ["n8n-nodes-base.openAi", "@n8n/n8n-nodes-langchain.lmChatOpenAi", "@n8n/n8n-nodes-langchain.agent"]
        self.assertEqual(llm_step_type(given), "@n8n/n8n-nodes-langchain.agent")
        self.assertIsNone(llm_step_type(["n8n-nodes-base.set", "n8n-nodes-base.httpRequest"]))

    def test_without_llm_the_data_workflow_stays_data(self):
        self.assertEqual(classify_workflow(workflow("Plain", self.HEAVY_DATA))[1].primary_category, Category.DATA_INTEGRATION)


class TieTests(unittest.TestCase):
    def test_tie_goes_to_the_earlier_category(self):
        # telegram gives AI_Content +2, wait gives Orchestration_Reliability +2.
        _, score = classify_workflow(
            workflow("Tie", [node("Wait", "n8n-nodes-base.wait"), node("Telegram", "n8n-nodes-base.telegram")])
        )
        self.assertEqual(score.primary_category, Category.AI_CONTENT)
        self.assertEqual(score.secondary_category, Category.ORCHESTRATION)
        self.assertEqual(score.confidence, "low")


class TriggerTests(unittest.TestCase):
    def test_types_ending_in_trigger_are_triggers(self):
        metrics = extract_metrics(AI_WF)
        self.assertEqual(metrics.trigger_nodes, ["Telegram Trigger"])

    def test_known_trigger_list_still_counts(self):
        self.assertEqual(extract_metrics(ORCH_WF).trigger_nodes, ["On error", "Webhook"])


class StickyNoteTests(unittest.TestCase):
    def test_sticky_notes_do_not_count(self):
        with_notes = workflow(
            DATA_WF["name"],
            DATA_WF["nodes"]
            + [node(f"Sticky Note{i}", "n8n-nodes-base.stickyNote", parameters={"content": "note"}) for i in range(5)],
        )
        plain_metrics, plain_score = classify_workflow(DATA_WF)
        metrics, score = classify_workflow(with_notes)
        self.assertEqual(metrics.node_count, plain_metrics.node_count)
        self.assertEqual(score.scores, plain_score.scores)


class ConnectionTests(unittest.TestCase):
    def test_edges_counted_across_output_types(self):
        self.assertEqual(count_connections(AI_WF["connections"]), 3)

    def test_fan_out_counts_every_target(self):
        connections = {"A": {"main": [[{"node": "B"}, {"node": "C"}], [{"node": "D"}]]}}
        self.assertEqual(count_connections(connections), 3)

    def test_malformed_connections_count_zero(self):
        for bad in (None, [], {"A": "x"}, {"A": {"main": "x"}}, {"A": {"main": ["x"]}}):
            self.assertEqual(count_connections(bad), 0)


if __name__ == "__main__":
    unittest.main()
