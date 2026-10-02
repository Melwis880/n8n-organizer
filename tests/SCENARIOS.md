# Test scenarios

Every scenario has an automated test (`python -m unittest discover -s tests`). No network; all
input is synthetic and built in temporary folders by `tests/helpers.py`.

| # | Scenario | Expected | Test |
|---|---|---|---|
| 1 | Normal folder with workflows of each category | Each workflow lands in its category file; summary counts match | `test_pipeline.NormalRunTests` |
| 2 | Empty input folder | No crash; summary shows zeros; no category files | `test_pipeline.EmptyInputTests` |
| 3 | Malformed JSON | Skipped as `invalid_json`, reason in trace; run continues | `test_pipeline.SkipTests.test_invalid_json` |
| 4 | JSON that is not a workflow (list, dict without `nodes`, non-dict nodes) | Skipped as `not_a_workflow`, not an error | `test_pipeline.SkipTests.test_not_a_workflow` |
| 5 | File over the size limit | Skipped as `too_large` | `test_pipeline.SkipTests.test_too_large` |
| 6 | Symlinked file and symlinked folder | Neither is followed | `test_pipeline.SkipTests.test_symlinks` |
| 7 | Non-UTF-8 file; UTF-8 file with BOM | First skipped as `not_utf8`; second is read | `test_pipeline.SkipTests.test_encoding` |
| 8 | Two byte-for-byte identical workflows | One kept, duplicate kind `exact`, kept = first by path | `test_pipeline.DuplicateTests.test_exact` |
| 9 | Two workflows that differ only in ids, positions, credentials, webhookId | One kept, duplicate kind `normalized` | `test_pipeline.DuplicateTests.test_normalized` |
| 10 | Workflow and node names with `:`, newline, quotes, backticks, control and bidi characters | YAML parses back; heading is one line; code fences stay balanced | `test_pipeline.UntrustedTextTests` |
| 11 | Node type ending in `Trigger` (e.g. `telegramTrigger`) | Counted as a trigger | `test_classifier.TriggerTests` |
| 12 | Sticky notes | Not counted in node count, inventory or scoring | `test_classifier.StickyNoteTests` |
| 13 | Parameters with API keys, credentials, URLs, sticky-note text | None of it appears in any output file | `test_pipeline.LeakTests` |
| 14 | Same input, two runs | Byte-identical output files | `test_pipeline.DeterminismTests` |
| 15 | Output folder equal to input, inside input, or not empty; missing input | Refused with a clear message, exit code 2, nothing written | `test_cli.LocationTests` |
| 16 | Word limit passed | A second numbered file is opened; no workflow is lost | `test_pipeline.ChunkTests` |
| 17 | `source_file` in output | Relative to the input root, no local absolute path | `test_pipeline.NormalRunTests.test_source_file_relative` |
| 18 | Trace | Each file has the expected event chain; no workflow content in the trace; `--debug` mirrors to stderr; unwritable log folder warns once and the run continues; each event is on disk as soon as it is written; the file is opened once per run and closed at its end | `test_trace` |
| 19 | `search` command | Clear "not built yet" error, exit code 2 | `test_cli.CliTests.test_search_is_a_clear_stub` |
| 20 | Connections | Edges are counted across all output types (`main`, `ai_*`) | `test_classifier.ConnectionTests` |
| 21 | File system lists folders and files in a non-sorted order | Files are still processed in sorted path order | `test_loader.OrderTests` |
| 22 | Two categories tie | The earlier category in the fixed order wins, confidence `low` | `test_classifier.TieTests` |
| 23 | Untrusted text helper | Control, bidi, zero-width, line/paragraph separator and lone surrogate characters become spaces (ASCII-only text too); printable text is kept; whitespace collapses; long text is cut with `...` | `test_utils.CleanTextTests` |
| 24 | Workflow with an LLM step (any LangChain node or OpenAI node) among many data nodes | Primary is AI_Content by rule, confidence `high`, reason names the node type; secondary comes from scores | `test_classifier.LlmRuleTests` |
| 25 | Workflow with no scoring signal | Data_Integration by default, confidence `none`, reason says so | `test_classifier.CategoryTests.test_no_signal_falls_back_to_first_category_with_confidence_none` |
| 26 | Messaging channel nodes (Slack, Telegram, Twitter, LinkedIn) | No AI_Content score; they count as services | `test_classifier.ScoringRuleTests.test_messaging_channels_give_no_ai_score` |
| 27 | Only generic flow nodes (IF, Merge, Switch, Wait) besides services | No Orchestration_Reliability score | `test_classifier.ScoringRuleTests.test_generic_flow_nodes_alone_do_not_make_orchestration` |
| 28 | Sub-workflow trigger and Stop and Error | Orchestration_Reliability signals | `test_classifier.ScoringRuleTests.test_sub_workflows_and_error_stops_are_orchestration` |
| 29 | Service nodes without their own weight (Drive, Todoist...) | Data_Integration +2 once per type, with a reason line; core nodes (including utility nodes such as HTML Extract, Read PDF, TOTP and n8n's own demo and event nodes) and non-base types give nothing | `test_classifier.ScoringRuleTests` |
| 30 | Service nodes outside the known-service list (Gmail, Drive trigger, Drive tool, AWS SES, WooCommerce) | Listed once each in `external_services` with a readable name; a type that does not look like an n8n type name gives no service; the "three or more services" score and complexity still count only known services | `test_classifier.ServiceListTests` |
| 31 | LLM step rule with several AI node types | Reason names a model, chain or agent node first, then an embeddings node, then any other LangChain node | `test_classifier.LlmRuleTests.test_reason_prefers_the_model_node_then_embeddings` |
| 32 | Pattern tags | `ai_generation` only with a node that calls a model; `agentic_ai` only with an agent node; scores do not change | `test_classifier.PatternTagTests` |
| 33 | Workflow JSON without a name | The normalized excerpt shows the same name as the heading (the file name) | `test_pipeline.UnnamedWorkflowTests` |
| 34 | Vector store nodes (`vectorStoreQdrant`, `vectorStorePinecone`, ...) | Each node gets the vector-store weight (AI_Content +5) through a prefix match; unrelated LangChain types do not | `test_classifier.PrefixWeightTests` |
| 35 | File or folder name with bytes that are not UTF-8, a line break, NEL or a control character | Skipped as `unsafe_file_name`; the run completes and `summary.txt` gets no forged line | `test_pipeline.SkipTests.test_unsafe_file_and_folder_names_are_skipped_and_the_run_completes` |
| 36 | FIFO (or other non-regular file) named `*.json` | Skipped as `not_regular_file` without waiting | `test_pipeline.SkipTests.test_fifo_is_skipped_without_waiting` |
| 37 | File swapped for a symlink after the symlink check | Still not followed (`O_NOFOLLOW`), skipped as `symlink` | `test_pipeline.SkipTests.test_symlink_swapped_in_after_the_check_is_not_followed` |
| 38 | File that cannot be read | Counted as an error with its relative path and the reason only; no absolute path in `summary.txt` or the trace (`run_start` holds folder names) | `test_pipeline.ErrorTests.test_unreadable_file_error_has_no_absolute_path` |
| 39 | A file or symlink appears at an output file name during the run | Not followed, not overwritten; the run stops with a clear message | `test_pipeline.ErrorTests.test_output_file_that_appears_during_the_run_is_not_overwritten`, `test_utils.WriteNewFileTests` |
| 40 | Names with Markdown or HTML (`<!--`, images, links, tags, backticks); very long names | Escaped in headings and lists; the metadata yaml code block keeps them exactly and no name can close it | `test_pipeline.MarkdownInjectionTests`, `test_pipeline.LongNameTests`, `test_utils.MdTextTests` |
| 41 | Workflow or node name that is not a string; node type with spaces, a URL or a header | None of it reaches the output or the trace; such a type counts as no type | `test_pipeline.LeakTests.test_non_string_names_and_odd_types_never_reach_output`, `test_classifier.ServiceListTests.test_type_that_is_not_a_type_name_gives_no_service` |
| 42 | Every category file | Opens with a note that names are untrusted data, not instructions; `workflow_id` and `dedup_fingerprint` are SHA-256 | `test_pipeline.NormalRunTests.test_files_start_with_the_untrusted_note_and_hashes_are_sha256` |
| 43 | Records kept in memory during a run | Only node names and types, never parameters or credentials | `test_pipeline.LeakTests.test_records_keep_only_node_names_and_types` |
| 44 | Valid workflow with parameters nested 600 levels deep | Analysed, not an error; normalizing never changes the workflow it reads | `test_pipeline.DeepNestingTests` |
| 45 | Metadata block, built key by key from a cache | Byte-identical to one `yaml.safe_dump` of the whole metadata, for hard names (newlines, fences, HTML, emoji, YAML-like words, empty) and on cache hits | `test_pipeline.YamlBlockTests` |
