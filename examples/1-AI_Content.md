# AI_Content

Combined NotebookLM source file.
Word limit per file: 450000

---

# Folder: Filter

Workflows analysed in this folder: 1

---
workflow_id: a18bf7eb733b524bb53468afaded779e6ee45147
source_file: Filter/1667_Filter_Summarize_Automation_Triggered.json
workflow_name: Store Notion's Pages as Vector Documents into Supabase with OpenAI
primary_category: AI_Content
secondary_category: Data_Integration
category_confidence: high
project_purpose: AI-assisted flow for content generation, summarising, classification
  or chat.
architectural_complexity: Medium
freelance_value: Useful for clients who want AI content generation, chatbots, knowledge
  access or social media automation.
client_problem_type:
- Content generation automation
- AI chatbot / support assistant
- RAG / company knowledge access
node_count: 8
connection_count: 7
branching_factor: 0
trigger_nodes:
- Notion - Page Added Trigger
external_services:
- Notion
- OpenAI
key_patterns:
- rag_or_vector_memory
dedup_fingerprint: 4f2402322f60718306324c9811558afc5c13d2a2
analysis_version: 2.1.0
---

# Workflow: Store Notion's Pages as Vector Documents into Supabase with OpenAI

## 1. Executive Summary
AI-assisted flow for content generation, summarising, classification or chat.

## 2. Why This Matters
Useful for clients who want AI content generation, chatbots, knowledge access or social media automation.

## 3. Node Inventory
- Embeddings OpenAI (@n8n/n8n-nodes-langchain.embeddingsOpenAi)
- Token Splitter (@n8n/n8n-nodes-langchain.textSplitterTokenSplitter)
- Notion - Page Added Trigger (n8n-nodes-base.notionTrigger)
- Notion - Retrieve Page Content (n8n-nodes-base.notion)
- Filter Non-Text Content (n8n-nodes-base.filter)
- Summarize - Concatenate Notion's blocks content (n8n-nodes-base.summarize)
- Create metadata and load content (@n8n/n8n-nodes-langchain.documentDefaultDataLoader)
- Supabase Vector Store (@n8n/n8n-nodes-langchain.vectorStoreSupabase)

## 4. Integration Surface
Notion, OpenAI

## 5. Detected Patterns
- rag_or_vector_memory

## 6. Architecture Notes
Primary category: **AI_Content**  
Secondary category: **Data_Integration**  
Complexity: **Medium**

## 7. Reusable Insight
Client problems this pattern can answer: Content generation automation, AI chatbot / support assistant, RAG / company knowledge access

## 8. Workflow Metrics
- Node count: 8
- Connection count: 7
- Branching factor: 0
- Confidence: high

## 9. Classification Reasons
- LLM step found (@n8n/n8n-nodes-langchain.embeddingsOpenAi) -> AI_Content by rule
- @n8n/n8n-nodes-langchain.embeddingsOpenAi -> AI_Content +5
- n8n-nodes-base.notion (service) -> Data_Integration +2
- n8n-nodes-base.notionTrigger (service) -> Data_Integration +2
- OpenAI node found -> AI_Content +4
- LangChain node found -> AI_Content +5
- Vector store / memory node found -> AI_Content +4
- AI or memory signal -> AI_Content +2

## 10. Normalized JSON Excerpt
```json
{
  "name": "Store Notion's Pages as Vector Documents into Supabase with OpenAI",
  "nodes": [
    {
      "name": "create metadata and load content",
      "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader"
    },
    {
      "name": "embeddings openai",
      "type": "@n8n/n8n-nodes-langchain.embeddingsOpenAi"
    },
    {
      "name": "token splitter",
      "type": "@n8n/n8n-nodes-langchain.textSplitterTokenSplitter"
    },
    {
      "name": "supabase vector store",
      "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase"
    },
    {
      "name": "filter non-text content",
      "type": "n8n-nodes-base.filter"
    },
    {
      "name": "notion - retrieve page content",
      "type": "n8n-nodes-base.notion"
    },
    {
      "name": "notion - page added trigger",
      "type": "n8n-nodes-base.notionTrigger"
    },
    {
      "name": "summarize - concatenate notion's blocks content",
      "type": "n8n-nodes-base.summarize"
    }
  ]
}
```
