## Project Name
Advanced n8n Intelligence Organizer

## Mission
Build a Python-based analysis pipeline that scans folders containing n8n workflow JSON files, classifies each workflow into a primary architecture category using transparent scoring rules, enriches each workflow with reusable metadata, removes duplicates, and generates category-based consolidated Markdown knowledge files optimized for NotebookLM ingestion.

## Primary Goal
Transform raw n8n workflow JSON exports into structured, searchable, high-value training documents that can be used as:
1. A NotebookLM idea pool and architecture reference library
2. A proposal and project-scoping support library
3. A GitHub portfolio knowledge base

## Core Categories
The classifier must assign every workflow to one primary category and optionally one secondary category.

### 1) SEO_Data_N8N
Focus:
- Data pipelines
- API ingestion
- scraping
- Google Sheets
- SQL/NoSQL storage
- reporting
- ETL-like workflows

### 2) AI_Content_N8N
Focus:
- OpenAI
- LangChain
- vector stores
- AI agents
- chatbots
- content generation
- social media automation

### 3) Architecture_Security_N8N
Focus:
- Webhooks
- auth
- orchestration
- error handling
- reliability
- sub-workflows
- branching
- operational engineering quality

## Non-Goals
- Do not optimize primarily for cybersecurity analysis
- Do not build an LLM-dependent pipeline for the first version
- Do not preserve full raw JSON in the final markdown unless explicitly configured
- Do not create many small markdown files for NotebookLM ingestion; prefer large category-level compiled markdown outputs

## Mandatory Engineering Rules

### Rule 1: Deterministic classification
Classification must be rule-based and reproducible.
Avoid hidden heuristics.
All scores must be explainable.

### Rule 2: Duplicate prevention
The system must detect duplicates using both:
- raw file hash
- normalized workflow fingerprint hash

If two workflows are semantically identical after normalization, keep only one canonical entry.

### Rule 3: Markdown output quality
Generated Markdown must be:
- clean
- consistent
- sectioned
- human-readable
- optimized for NotebookLM retrieval

### Rule 4: No credential leakage
Never include credentials, secrets, tokens, headers, auth values, or private URLs in output files.

### Rule 5: Safe normalization
When summarizing workflows:
- remove credentials
- remove execution metadata
- remove volatile IDs if unnecessary
- remove canvas positions unless debugging mode is enabled

### Rule 6: Modular architecture
Code must be split into small modules:
- loader
- normalizer
- classifier
- enricher
- deduper
- markdown_writer
- config

### Rule 7: Strong typing
Prefer Python type hints, dataclasses, enums, and small pure functions.

### Rule 8: Graceful failure
Invalid JSON files must not crash the pipeline.
Log and skip unreadable files.

## Recommended Output Structure
For each workflow, generate:

1. YAML metadata block
2. Executive summary
3. Detected node inventory
4. Integration surface
5. Detected architectural patterns
6. Complexity assessment
7. Freelancer value statement
8. Reusable implementation insight
9. Small normalized workflow summary

## Folder Conventions
- input/ : raw n8n JSON files
- output/ : generated markdown files
- cache/ : hashes, dedup index, intermediate artifacts
- logs/ : warnings and processing logs
- src/ : application code
- tests/ : unit tests

## Coding Style
- Prefer readability over cleverness
- Prefer explicit mappings over magical inference
- Use constants/config files for node scoring rules
- Keep side effects isolated
- Keep markdown generation deterministic

## Classification Guidance
Use three signals:
1. Node-based weights
2. Pattern-based bonuses
3. Structural graph signals

Then compute:
- primary category
- secondary category
- confidence level
- explanation list

## Metadata Requirements
Each workflow entry must include:
- workflow_name
- source_file
- primary_category
- secondary_category
- category_confidence
- project_purpose
- architectural_complexity
- freelance_value
- node_count
- connection_count
- branching_factor
- trigger_nodes
- external_services
- key_patterns
- dedup_fingerprint
- analysis_version

## NotebookLM Optimization Rules
The generated markdown should help semantic retrieval.
That means:
- concise summaries first
- reusable architecture insights
- client problem framing
- avoid raw JSON dumps unless shortened and normalized

## Future Extensibility
Design the code so future versions can add:
- embedding-based similarity
- proposal template generation
- workflow search index
- portfolio showcase generation
- auto-tagging by business domain

## Important Constraint
The system should produce one large markdown file per category, not one markdown file per workflow, unless debug mode is enabled.

## Done Criteria
The project is complete when:
- JSON workflows can be scanned recursively
- invalid files are skipped safely
- workflows are normalized
- duplicates are removed
- category scores are computed
- metadata is generated
- category-level markdown files are written
- logs and summary stats are produced