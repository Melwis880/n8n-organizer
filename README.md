# n8n-organizer

Turn a folder of n8n workflow JSON exports into three Markdown knowledge files, one per
architecture category, ready to load into NotebookLM or any other reader.

Every workflow is classified by fixed, explainable rules: each file says which node gave which
points. No LLM, no network, no API key. The same input always gives byte-identical output.

```
input/                                output/
  Slack/0123_....json                   1-Data_Integration.md
  Webhook/0456_....json      ──────►    1-AI_Content.md
  ...  (2,057 files)                    1-Orchestration_Reliability.md
                                        summary.txt
```

## Why

A large n8n library is useful when you scope client work ("has anyone built a webhook-to-CRM
flow with error handling?"), but 2,000 raw JSON files are hard to search and too many to load
into a notebook tool one by one. This tool groups them, removes duplicates, and writes a short,
uniform profile of each workflow: its nodes, services, metrics and the reasons for its category.

On the [Zie619/n8n-workflows](https://github.com/Zie619/n8n-workflows) collection it reads
2,057 files and writes 1,973 unique workflow profiles in about 10 seconds. See
[CASE_STUDY.md](CASE_STUDY.md).

## Install

Needs Python 3.10 or newer. The only dependency is PyYAML.

```bash
# from a checkout of this repository
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
n8n-organizer --help
```

## Usage

```bash
n8n-organizer build --input path/to/workflows --output path/to/new-folder
```

| Option | Meaning |
|---|---|
| `--input DIR` | Folder with n8n workflow JSON files. Read recursively. |
| `--output DIR` | Folder for the Markdown files. Must be empty or not exist yet. |
| `--log-dir DIR` | Folder for the JSONL trace (default `./logs`). |
| `--debug` | Also print every trace line to stderr. |

Exit code is `0` on success and `2` on a usage problem (missing input, output folder not empty
or inside the input folder). A file that cannot be read never stops the run; it is counted and
listed in `summary.txt`.

`n8n-organizer search` is reserved for a planned search index and is not built yet. It exits
with a clear "not built yet" message.

### Try it on a real collection

```bash
git clone https://github.com/Zie619/n8n-workflows
mkdir -p input/zie619-ae8cf6dc
git -C n8n-workflows archive ae8cf6dc5b873cbb4f74587aa9180ed3a9f70682 workflows \
  | tar -x -C input/zie619-ae8cf6dc
n8n-organizer build --input input/zie619-ae8cf6dc/workflows --output output/zie619
cat output/zie619/summary.txt
```

This commit is pinned on purpose: later commits in that collection replaced the LangChain nodes
with `noOp` and broke connections (details in [CASE_STUDY.md](CASE_STUDY.md)).

## Output

[`examples/`](examples/) holds the real output for four workflows from that collection.

- **`<n>-<Category>.md`**: one file per category, grouped by source folder, then sorted by
  workflow name. When a file would pass 450,000 words (the NotebookLM source limit), the next
  folder goes into `2-<Category>.md`, and so on.
- **`summary.txt`**: files found, workflows analysed, unique, duplicates (exact / normalized),
  skipped files by reason, errors, output files.

Each workflow profile starts with YAML front matter:

| Field | Content |
|---|---|
| `workflow_id`, `dedup_fingerprint` | SHA-1 of the workflow JSON and of its normalized form |
| `source_file` | Path relative to `--input`; never an absolute local path |
| `workflow_name` | From the JSON, or the file name if it has none |
| `primary_category`, `secondary_category` | See [Classification](#classification) |
| `category_confidence` | `high`, `medium`, `low` or `none` |
| `node_count`, `connection_count`, `branching_factor` | Sticky notes excluded; connections are real edges of every type (`main`, `ai_*`) |
| `trigger_nodes` | Names of trigger nodes (any type ending in `Trigger`, plus Webhook) |
| `external_services` | Every service the workflow talks to, by name (Gmail, Google Drive, HubSpot...) |
| `key_patterns` | `ai_generation` (a node calls a model), `agentic_ai` (an agent node), `rag_or_vector_memory`, `api_ingestion`, `reporting_pipeline`, `webhook_request_lifecycle`, `error_handling` |
| `project_purpose`, `freelance_value`, `client_problem_type` | Short category-level text for scoping work |
| `architectural_complexity` | `Low`, `Medium` or `High`, from nodes, branches, services, sub-workflows, error handling, AI |

After the front matter come ten sections: summary, value, node inventory (name and type),
services, patterns, architecture notes, reusable insight, metrics, classification reasons and a
short normalized node list.

**What never reaches the output:** node parameters, credentials, URLs and sticky-note text.
Workflows often carry API keys in parameters, so only names, types, counts and hashes are
written.

### Trace

Every run appends one JSON line per event to `<log-dir>/YYYY-MM-DD.jsonl`, linked by `run_id`
and `seq`. Each file produces `found`, then `skipped` (with a reason) or `loaded` →
`classified` (scores, hashes) → `duplicate` (with the kept file) or `placed` (output file). The
run starts with `run_start` and ends with `written` per file and `run_end` with the totals. The
trace holds paths, names, hashes and numbers, never workflow content.

## Classification

Three categories, chosen for what a client asks for, not for node families:

| Category | Covers |
|---|---|
| `Data_Integration` | Moving data between services: APIs, sheets, databases, CRMs, sync and reporting |
| `AI_Content` | Any workflow with an LLM step: generation, chat, agents, RAG, embeddings |
| `Orchestration_Reliability` | Webhook request/response, sub-workflows, error handling |

### Rules, in order

1. **Node weights.** Each node adds its weight (counted per node):

   | Node type | Points |
   |---|---|
   | Google Sheets, Postgres, MySQL, MongoDB | Data +4 |
   | Airtable | Data +3 |
   | HTTP Request | Data +3, Orchestration +1 |
   | Error Trigger | Orchestration +6 |
   | Webhook, Execute Workflow, Execute Workflow Trigger | Orchestration +4 |
   | Respond to Webhook, Stop and Error | Orchestration +3 |
   | LangChain Agent | AI +6, Orchestration +1 |
   | OpenAI (base and LangChain), any LangChain vector store (`vectorStore*`), OpenAI Embeddings | AI +5 |

2. **Other services.** Every other built-in service node (Gmail, Drive, Slack, Todoist,
   QuickBooks...) adds Data +2, once per node type. Built-in core nodes (Set, Code, IF, Merge,
   Switch, Wait, Split, Schedule...) add nothing: they appear in almost every workflow and say
   nothing about its purpose. The same goes for utility nodes that work inside n8n (HTML
   Extract, Read PDF, TOTP, iCal) and n8n's own demo and event nodes. Messaging channels (Slack, Telegram, Twitter, LinkedIn) are
   services, not AI.
3. **Patterns.** HTTP Request + Google Sheets: Data +6. HTTP Request: Data +2. Webhook +
   Respond to Webhook: Orchestration +6. Error Trigger: Orchestration +5. Any OpenAI node: AI +4.
   Any LangChain node: AI +5. Any vector node: AI +4. Any of those three: AI +2 more. Three or
   more known services (Google Sheets, Postgres, MySQL, MongoDB, Airtable, OpenAI, Telegram,
   Slack, Discord, Notion, GitHub, HTTP, Webhook): Data +1 and Orchestration +1.
4. **LLM step rule.** If the workflow has any LangChain node or any node with `openai` in its
   type, the primary category is `AI_Content` with `high` confidence, whatever the scores say.
   Without this rule, five HTTP and Sheets nodes around one LLM call outvoted it. The secondary
   category still comes from the scores. The reason line names a model, chain or agent node if
   there is one, then an embeddings node, then any other LangChain node.
5. **Otherwise** the highest score wins and the runner-up (if above zero) is secondary.
   Confidence comes from the gap between them, `(top - second) / top`: above 0.40 is `high`,
   above 0.20 `medium`, otherwise `low`. Ties go to the first category in the order Data,
   AI, Orchestration.
6. **No signal.** A workflow with zero points (only core nodes, for example a Set + XML flow)
   goes to `Data_Integration` with confidence `none`, and its reason line says so. Filter these
   out if you only want real matches.

All weights live in [`src/n8n_organizer/config.py`](src/n8n_organizer/config.py).

### Input handling and duplicates

- Files are processed in sorted path order, so runs are reproducible.
- Skipped, with the reason in the trace and `summary.txt`: symlinks (never followed),
  files over 10 MB, files that are not valid UTF-8 (a BOM is fine), invalid JSON, and JSON that
  is not a workflow (no top-level object with a `nodes` list, such as `package.json`).
- Duplicates are found in two steps: same JSON content (key order and whitespace ignored), then
  same name, nodes and connections after ignoring node ids, positions, credentials, webhook ids,
  node order and node-name case. Workflow-level fields such as `id`, `tags` and `settings` are
  ignored in this step. The first file by path is kept; the trace records which file each
  duplicate matched.
- The output folder must not be the input folder or inside it, so a later run never reads its
  own output. The tool never deletes or overwrites a file.

## Limits

- **It only sees node types.** A workflow that calls an AI service through a plain HTTP Request
  (Midjourney, a self-hosted model) lands in `Data_Integration`. The tool never reads
  parameters, by design.
- **Accuracy was checked by hand on small samples, not a benchmark.** On an independent sample
  of 24 workflows with a scoring signal (8 per category), all 24 primary categories were correct.
  The sample checked before the last scoring round gave 14 of 20. 59 of 1,973 workflows (3.0%)
  had no signal at all.
- **Service names come from node types.** `googleDriveTrigger` becomes "Google Drive"; a short
  table fixes brand spellings (HubSpot, WooCommerce). Providers behind LangChain nodes
  (Anthropic, Supabase vector store) are not listed, except OpenAI.
- **Prose fields are per category, not per workflow.** Summary, value and client problems are
  fixed texts for the category.
- Word counts for splitting are approximate.

## Development

```bash
pip install -e .
python -m unittest discover -s tests
```

Every behaviour above has a scenario in [`tests/SCENARIOS.md`](tests/SCENARIOS.md) and a test
on synthetic fixtures. Tests use no network and no real workflows. CI runs them on Python 3.10
to 3.13.

## License

MIT, see [LICENSE](LICENSE). The files in [`examples/`](examples/) are derived from
Zie619/n8n-workflows (MIT); attribution in [`examples/NOTICE`](examples/NOTICE).
