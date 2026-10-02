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
| 18 | Trace | Each file has the expected event chain; no workflow content in the trace; `--debug` mirrors to stderr; unwritable log folder warns once and the run continues | `test_trace` |
| 19 | `search` command | Clear "not built yet" error, exit code 2 | `test_cli.CliTests.test_search_is_a_clear_stub` |
| 20 | Connections | Edges are counted across all output types (`main`, `ai_*`) | `test_classifier.ConnectionTests` |
| 21 | File system lists folders and files in a non-sorted order | Files are still processed in sorted path order | `test_loader.OrderTests` |
| 22 | Two categories tie | The earlier category in the fixed order wins, confidence `low` | `test_classifier.TieTests` |
| 23 | Untrusted text helper | Control, bidi and zero-width characters become spaces; whitespace collapses; long text is cut with `...` | `test_utils.CleanTextTests` |
