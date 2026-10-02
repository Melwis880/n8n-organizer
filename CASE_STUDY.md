# Case study: a 2,000-workflow n8n library as a knowledge base

All numbers below were measured on the
[Zie619/n8n-workflows](https://github.com/Zie619/n8n-workflows) collection at commit
`ae8cf6dc` (2025-09-29), on a laptop (Intel i7-1255U).

## The problem

When scoping an automation project, the useful question is "what has already been built for
this?" A public library of n8n workflows answers it, but only if you can search it. The
Zie619 collection has 2,057 JSON files in 187 folders. Raw n8n JSON is long, full of node
parameters and canvas positions, and some files are copies of others. Loading it as-is into a
notebook tool like NotebookLM means hundreds of sources and a lot of noise.

The goal: a small number of large, clean Markdown sources, each workflow described the same
way, with a category you can trust and see the reason for.

## How it works

1. **Scan** the input folder in sorted path order. Skip symlinks, files over 10 MB, non-UTF-8
   files, invalid JSON and JSON that is not a workflow, and record why.
2. **Measure** each workflow: working nodes (sticky notes excluded), real connection edges,
   triggers, branches, services.
3. **Score** it against three categories (`Data_Integration`, `AI_Content`,
   `Orchestration_Reliability`) with fixed node weights and patterns. Any LLM step makes it
   `AI_Content`. Every point is written out as a reason line.
4. **Remove duplicates** in two steps: same JSON content, then same content after ignoring ids,
   positions, credentials and node order.
5. **Write** one Markdown file per category, plus `summary.txt` and a JSONL trace of every
   decision.

No LLM, no network, one dependency (PyYAML). Node parameters, credentials, URLs and sticky-note
text never reach the output, because real workflows often hold API keys in parameters.

## Finding: the latest version of the collection was broken

Before trusting any category counts, node types were compared across the collection's git
history. Two commits had damaged it:

- `f293c236` added thousands of disconnected `stopAndError` nodes: 8,791 disconnected nodes in
  total.
- `3c0a92c4` turned LangChain nodes into `noOp` nodes but kept their names (320 nodes still
  named "OpenAI Chat Model", 180 named "AI Agent") and broke connections (2,123 disconnected
  HTTP Request nodes).

The last clean version, `ae8cf6dc`, has 3,959 LangChain nodes and 241 disconnected nodes. The
tool is run on that version, extracted with `git archive`. A classifier that reads node types
cannot be right on data where the types were rewritten, so finding this came before tuning
anything.

## Result

| Measure | Value |
|---|---|
| JSON files read | 2,057 |
| Workflows analysed | 2,047 |
| Unique workflows written | 1,973 |
| Duplicates removed | 74 (all exact copies with a different number in the same folder) |
| Skipped as "not a workflow" | 10 (`package.json`, `tsconfig.json`, API listings) |
| Errors | 0 |
| Run time | about 10 seconds |
| Output | 3 files, 741,857 words; each under the 450,000-word NotebookLM limit |

| Category | Workflows |
|---|---|
| Data_Integration | 1,079 |
| AI_Content | 746 |
| Orchestration_Reliability | 148 |

| Confidence | Workflows |
|---|---|
| high | 1,830 |
| medium | 47 |
| low | 37 |
| none (no scoring signal) | 59 |

Two runs with different `PYTHONHASHSEED` values gave byte-identical output.

## Accuracy, checked by hand

Three random samples of 24 workflows (8 per category), each read node by node:

| Sample | When | Correct primary category |
|---|---|---|
| A (seed 42) | Before tuning | 16 of 24 |
| B (seed 2026, independent) | After the LLM step rule | 14 of 20 with a signal (70%) |
| C (seed 777, independent) | After the scoring round | 24 of 24 with a signal |

What the samples showed, and what changed:

- **5 of the 6 errors in sample A** were workflows with one LLM call surrounded by HTTP, Sheets
  and IF nodes, which outvoted it. Rule added: any LLM step makes the workflow `AI_Content`.
  Workflows with no signal at all now get confidence `none` instead of a guess that looks real.
- **Sample B** showed three more causes: Slack and Telegram nodes gave AI points; generic IF and
  Merge nodes pulled workflows into Orchestration; most service nodes (Drive, Spotify,
  QuickBooks, Todoist) had no weight, so 312 workflows had no signal. After the scoring round,
  5 of B's 6 errors were fixed and the no-signal count fell from 312 to 52 (before duplicate
  removal).
- **The remaining known miss** is a workflow that calls an AI service through a plain HTTP
  Request (Midjourney). Seeing that would mean reading parameters, which the tool does not do by
  design. It is listed in the README limits.
- **A later cleanup** stopped nine utility node types (HTML Extract, Read PDF, TOTP, n8n's demo
  data nodes...) from counting as services. It changed 12 unique workflows, and all 12 were
  checked by hand. 10 were demos and tutorials that had looked like `high`-confidence data
  integrations; they now correctly show no signal. One moved to Orchestration, which is right
  (it serves an n8n dependency graph through a webhook). One, a scraper that serves its result
  as an RSS feed through a webhook, stayed in Orchestration with higher confidence;
  Data_Integration would be the better call.

Sample A was used for tuning, so its post-tuning result is not reported as accuracy. Samples of
24 are small; these are checks, not a benchmark.

## What the rewrite fixed

The tool started as a ~900-line pipeline that ran and produced files. Tests and a full-data run
found these bugs in it:

- An unclosed ```` ```json ```` fence: in every category file, everything after the first
  workflow was inside a code block.
- `connection_count` counted output slots, not edges, and ignored AI connections
  (`ai_languageModel`, `ai_tool`).
- Trigger detection used a fixed list and missed types like `telegramTrigger`.
- JSON files that are not workflows were counted as errors or as empty workflows.
- Files were read with `errors="ignore"`, which silently dropped bytes instead of reporting
  bad encoding.
- A typo (`httpsrequest`) and a weight key (`linkedin`) that never matched the real node type
  (`linkedIn`) meant two rules never fired.
- A third weight key, `vectorStore`, matched no real node type either: the real types are
  `vectorStoreQdrant`, `vectorStorePinecone` and so on (172 nodes). It is now a prefix match.
  All 97 workflows with a vector store already had an LLM step, so no category, secondary
  category or confidence changed; only scores and reason lines did.

The test suite has 66 tests over 34 written scenarios (tests/SCENARIOS.md), all on synthetic
fixtures. To check that the tests catch real faults, 60 deliberate bugs were planted in the
code one at a time: 56 were caught. The exercise also found four missing tests (added) and two
pieces of dead code (removed).

## Takeaways

- Look at the data before tuning the model. Here the newest data was the problem.
- An explicit "no signal" beats a confident default.
- Hand-checked samples, kept separate from the tuning sample, are what made the accuracy
  numbers honest.
