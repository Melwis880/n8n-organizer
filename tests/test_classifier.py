import unittest

from n8n_organizer.classifier import classify_workflow, count_connections, extract_metrics, llm_step_type, type_of
from n8n_organizer.enricher import infer_project_purpose
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

    def test_reason_prefers_the_model_node_then_embeddings(self):
        loader = "@n8n/n8n-nodes-langchain.documentDefaultDataLoader"
        embeddings = "@n8n/n8n-nodes-langchain.embeddingsOpenAi"
        model = "@n8n/n8n-nodes-langchain.lmChatAnthropic"
        self.assertEqual(llm_step_type([loader, embeddings, model]), model)
        self.assertEqual(llm_step_type([loader, embeddings]), embeddings)
        self.assertEqual(llm_step_type([loader]), loader)

    def test_without_llm_the_data_workflow_stays_data(self):
        self.assertEqual(classify_workflow(workflow("Plain", self.HEAVY_DATA))[1].primary_category, Category.DATA_INTEGRATION)


class PatternTagTests(unittest.TestCase):
    def patterns(self, *types):
        return classify_workflow(workflow("Tags", [node(f"N{i}", t) for i, t in enumerate(types)]))[1].key_patterns

    def test_embedding_pipeline_is_not_generation_or_agent(self):
        tags = self.patterns(
            "@n8n/n8n-nodes-langchain.embeddingsOpenAi",
            "@n8n/n8n-nodes-langchain.documentDefaultDataLoader",
            "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
        )
        self.assertEqual(tags, ["rag_or_vector_memory"])

    def test_model_without_agent_is_generation_only(self):
        tags = self.patterns("@n8n/n8n-nodes-langchain.chainLlm", "@n8n/n8n-nodes-langchain.lmChatAnthropic")
        self.assertEqual(tags, ["ai_generation"])

    def test_base_openai_node_is_generation(self):
        self.assertEqual(self.patterns("n8n-nodes-base.openAi"), ["ai_generation"])

    def test_agent_node_is_agentic(self):
        self.assertEqual(self.patterns("@n8n/n8n-nodes-langchain.agent"), ["ai_generation", "agentic_ai"])

    def test_tags_do_not_change_scores(self):
        _, score = classify_workflow(workflow("Embed", [node("E", "@n8n/n8n-nodes-langchain.embeddingsOpenAi")]))
        # weight 5 + OpenAI bonus 4 + LangChain bonus 5 + AI signal 2
        self.assertEqual(score.scores[Category.AI_CONTENT], 16)


class ServiceListTests(unittest.TestCase):
    def test_every_service_node_is_listed_once_by_name(self):
        metrics = extract_metrics(workflow("Services", [
            node("Mail", "n8n-nodes-base.gmail"),
            node("Mail in", "n8n-nodes-base.gmailTrigger"),
            node("Drive", "n8n-nodes-base.googleDriveTrigger"),
            node("Drive tool", "n8n-nodes-base.googleDriveTool"),
            node("Video", "n8n-nodes-base.youTube"),
            node("Mail out", "n8n-nodes-base.awsSes"),
            node("Shop", "n8n-nodes-base.wooCommerceTrigger"),
            node("Sheet", "n8n-nodes-base.googleSheets"),
            node("Set", "n8n-nodes-base.set"),
            node("Model", "@n8n/n8n-nodes-langchain.lmChatAnthropic"),
        ]))
        self.assertEqual(metrics.external_services, ["AWS SES", "Gmail", "Google Drive", "Google Sheets", "WooCommerce", "YouTube"])

    def test_scoring_still_counts_only_known_services(self):
        wf = workflow("Three new services", [
            node("Mail", "n8n-nodes-base.gmail"),
            node("Drive", "n8n-nodes-base.googleDrive"),
            node("CRM", "n8n-nodes-base.hubspot"),
        ])
        metrics, score = classify_workflow(wf)
        self.assertEqual(len(metrics.external_services), 3)
        self.assertEqual(metrics.integration_count, 0)
        self.assertEqual(score.scores[Category.ORCHESTRATION], 0)
        self.assertFalse(any(r.startswith("Three or more") for r in score.reasons))

    def test_type_that_is_not_a_type_name_gives_no_service(self):
        metrics = extract_metrics(workflow("Evil", [
            node("A", "n8n-nodes-base.evil\nType\x1b[31m"),
            node("B", "n8n-nodes-base.https://secret.example/api?key=ABC"),
            node("C", "n8n-nodes-base."),
        ]))
        self.assertEqual(metrics.external_services, [])


class TypePatternTests(unittest.TestCase):
    def test_n8n_type_names_are_types(self):
        for type_ in (
            "n8n-nodes-base.googleSheets",
            "@n8n/n8n-nodes-langchain.agent",
            "@horka/n8n-nodes-storage-kv.keyValueStorage",
            "n8n-nodes-community_x.node_1",
        ):
            self.assertEqual(type_of({"type": type_}), type_)

    def test_links_addresses_and_odd_shapes_are_no_type(self):
        for type_ in (
            "www.evil.example",
            "WWW.evil",
            "www.evil.example/phish",
            "n8n-nodes-base.mail@evil.example",
            "evil@x.example",
            "n8n-nodes-base.a.b",
            "n8n-nodes-base",
            "n8n-nodes-base.",
            "@scope/.x",
            # A package must be named n8n-nodes-*, and a scope has no dot: a host name with a
            # path would reach the output (n8n loads community nodes only from such packages).
            "@horka.tv/n8n-nodes-storage-kv.keyValueStorage",
            "@evil.example/n8n-nodes-login.x",
            "bit.ly",
            "evil.example",
            "CUSTOM.klicktipp",
            "n8n-nodes-base." + "x" * 106,
        ):
            self.assertEqual(type_of({"type": type_}), "", type_)
        self.assertEqual(type_of({"type": "n8n-nodes-base." + "x" * 105}), "n8n-nodes-base." + "x" * 105)


class TieTests(unittest.TestCase):
    def test_tie_goes_to_the_earlier_category(self):
        # googleSheets gives Data_Integration +4, webhook gives Orchestration_Reliability +4.
        _, score = classify_workflow(
            workflow("Tie", [node("Hook", "n8n-nodes-base.webhook"), node("Sheet", "n8n-nodes-base.googleSheets")])
        )
        self.assertEqual(score.scores[Category.DATA_INTEGRATION], score.scores[Category.ORCHESTRATION])
        self.assertEqual(score.primary_category, Category.DATA_INTEGRATION)
        self.assertEqual(score.secondary_category, Category.ORCHESTRATION)
        self.assertEqual(score.confidence, "low")


class ScoringRuleTests(unittest.TestCase):
    def test_messaging_channels_give_no_ai_score(self):
        wf = workflow("Zendesk to Slack", [
            node("Cron", "n8n-nodes-base.cron"),
            node("Zendesk", "n8n-nodes-base.zendesk"),
            node("Slack", "n8n-nodes-base.slack"),
            node("Telegram", "n8n-nodes-base.telegram"),
            node("Tweet", "n8n-nodes-base.twitter"),
            node("Post", "n8n-nodes-base.linkedIn"),
        ])
        _, score = classify_workflow(wf)
        self.assertEqual(score.scores[Category.AI_CONTENT], 0)
        self.assertEqual(score.primary_category, Category.DATA_INTEGRATION)

    def test_generic_flow_nodes_alone_do_not_make_orchestration(self):
        wf = workflow("Telegram files to Drive", [
            node("Trigger", "n8n-nodes-base.telegramTrigger"),
            node("If", "n8n-nodes-base.if"),
            node("Merge", "n8n-nodes-base.merge"),
            node("Switch", "n8n-nodes-base.switch"),
            node("Wait", "n8n-nodes-base.wait"),
            node("Drive", "n8n-nodes-base.googleDrive"),
        ])
        _, score = classify_workflow(wf)
        self.assertEqual(score.scores[Category.ORCHESTRATION], 0)
        self.assertEqual(score.primary_category, Category.DATA_INTEGRATION)

    def test_sub_workflows_and_error_stops_are_orchestration(self):
        wf = workflow("Router", [
            node("Called", "n8n-nodes-base.executeWorkflowTrigger"),
            node("Fail", "n8n-nodes-base.stopAndError"),
            node("Drive", "n8n-nodes-base.googleDrive"),
        ])
        _, score = classify_workflow(wf)
        self.assertEqual(score.scores[Category.ORCHESTRATION], 7)
        self.assertEqual(score.primary_category, Category.ORCHESTRATION)

    def test_service_nodes_count_once_per_type(self):
        wf = workflow("Two drives", [node("A", "n8n-nodes-base.googleDrive"), node("B", "n8n-nodes-base.googleDrive"), node("T", "n8n-nodes-base.todoist")])
        _, score = classify_workflow(wf)
        self.assertEqual(score.scores[Category.DATA_INTEGRATION], 4)
        self.assertIn("n8n-nodes-base.googleDrive (service) -> Data_Integration +2", score.reasons)

    def test_core_nodes_and_non_base_types_are_not_services(self):
        wf = workflow("Core only", [
            node("Set", "n8n-nodes-base.set"),
            node("Code", "n8n-nodes-base.code"),
            node("Manual", "n8n-nodes-base.manualTrigger"),
            node("Schedule", "n8n-nodes-base.scheduleTrigger"),
            node("Custom", "n8n-nodes-community.something"),
        ])
        _, score = classify_workflow(wf)
        self.assertEqual(max(score.scores.values()), 0)
        self.assertEqual(score.confidence, "none")

    def test_utility_and_n8n_demo_nodes_are_not_services(self):
        utility = ["htmlExtract", "readPDF", "totp", "iCal", "aiTransform", "executeCommandTool",
                   "n8nTrainingCustomerDatastore", "n8nTrainingCustomerMessenger", "n8nTrigger"]
        wf = workflow("Utility only", [node(t, f"n8n-nodes-base.{t}") for t in utility])
        metrics, score = classify_workflow(wf)
        self.assertEqual(max(score.scores.values()), 0)
        self.assertEqual(score.confidence, "none")
        self.assertEqual(metrics.external_services, [])


class PrefixWeightTests(unittest.TestCase):
    def test_every_vector_store_type_gets_the_vector_store_weight(self):
        for store in ("vectorStoreQdrant", "vectorStorePinecone", "vectorStoreInMemory"):
            node_type = f"@n8n/n8n-nodes-langchain.{store}"
            _, score = classify_workflow(workflow("RAG", [node("Store", node_type)]))
            self.assertIn(f"{node_type} -> AI_Content +5", score.reasons)

    def test_vector_store_weight_counts_per_node(self):
        nodes = [node(f"Store {i}", "@n8n/n8n-nodes-langchain.vectorStoreQdrant") for i in range(2)]
        _, one = classify_workflow(workflow("One", nodes[:1]))
        _, two = classify_workflow(workflow("Two", nodes))
        self.assertEqual(two.scores[Category.AI_CONTENT] - one.scores[Category.AI_CONTENT], 5)

    def test_prefix_does_not_reach_unrelated_types(self):
        _, score = classify_workflow(workflow("Loader", [node("Loader", "@n8n/n8n-nodes-langchain.documentDefaultDataLoader")]))
        self.assertFalse(any("documentDefaultDataLoader ->" in r for r in score.reasons))


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


class AiSignalTests(unittest.TestCase):
    def test_ai_or_memory_signal_from_each_word_in_any_case(self):
        for node_type in ("n8n-nodes-base.openAi", "@n8n/n8n-nodes-langchain.toolCalculator", "n8n-nodes-community.VectorDb"):
            metrics, score = classify_workflow(workflow("AI", [node("N", node_type)]))
            self.assertTrue(metrics.has_ai_or_memory, node_type)
            self.assertIn("AI or memory signal -> AI_Content +2", score.reasons, node_type)
        metrics, score = classify_workflow(workflow("Plain", [node("N", "n8n-nodes-base.slack")]))
        self.assertFalse(metrics.has_ai_or_memory)
        self.assertNotIn("AI or memory signal -> AI_Content +2", score.reasons)

    def test_purpose_text_follows_node_types_in_any_case(self):
        def purpose(*types):
            return infer_project_purpose(set(types), Category.ORCHESTRATION.value)
        self.assertTrue(purpose("n8n-nodes-base.httpRequest", "n8n-nodes-base.googleSheets").startswith("Automated data flow"))
        self.assertTrue(purpose("@n8n/n8n-nodes-langchain.lmChatOpenAi").startswith("AI-assisted flow"))
        self.assertTrue(purpose("n8n-nodes-base.webhook").startswith("Workflow that receives requests"))
        self.assertTrue(purpose("n8n-nodes-base.slack").startswith("Automation for integration, orchestration"))


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
