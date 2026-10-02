# Data_Integration

Combined NotebookLM source file.
Word limit per file: 450000

---

# Folder: Manual

Workflows analysed in this folder: 1

---
workflow_id: 951e2d2be122aa947ec0a08430655bd5ebe736c6
source_file: Manual/0943_Manual_Xml_Automation_Triggered.json
workflow_name: XML Conversion
primary_category: Data_Integration
secondary_category: null
category_confidence: none
project_purpose: Automation for collecting, transforming and reporting data.
architectural_complexity: Low
freelance_value: Useful for clients who need automated reporting, lead collection,
  scraping or data synchronisation.
client_problem_type:
- Automated reporting
- Lead collection
- Data synchronisation
node_count: 3
connection_count: 2
branching_factor: 0
trigger_nodes:
- On clicking 'execute'
external_services: []
key_patterns: []
dedup_fingerprint: 3b859abee0cb4c4c5dcb7bb2e468776607bdd533
analysis_version: 2.1.1
---

# Workflow: XML Conversion

## 1. Executive Summary
Automation for collecting, transforming and reporting data.

## 2. Why This Matters
Useful for clients who need automated reporting, lead collection, scraping or data synchronisation.

## 3. Node Inventory
- On clicking 'execute' (n8n-nodes-base.manualTrigger)
- Set (n8n-nodes-base.set)
- XML (n8n-nodes-base.xml)

## 4. Integration Surface
None detected

## 5. Detected Patterns
- none

## 6. Architecture Notes
Primary category: **Data_Integration**  
Secondary category: **None**  
Complexity: **Low**

## 7. Reusable Insight
Client problems this pattern can answer: Automated reporting, Lead collection, Data synchronisation

## 8. Workflow Metrics
- Node count: 3
- Connection count: 2
- Branching factor: 0
- Confidence: none

## 9. Classification Reasons
- No scoring signal; placed in Data_Integration by default

## 10. Normalized JSON Excerpt
```json
{
  "name": "XML Conversion",
  "nodes": [
    {
      "name": "on clicking 'execute'",
      "type": "n8n-nodes-base.manualTrigger"
    },
    {
      "name": "set",
      "type": "n8n-nodes-base.set"
    },
    {
      "name": "xml",
      "type": "n8n-nodes-base.xml"
    }
  ]
}
```

---

# Folder: Splitout

Workflows analysed in this folder: 1

---
workflow_id: 298454d35658e5dc596f62a7445538f56decf9ab
source_file: Splitout/1564_Splitout_Manual_Create_Webhook.json
workflow_name: Search LinkedIn companies and add them to Airtable CRM
primary_category: Data_Integration
secondary_category: Orchestration_Reliability
category_confidence: high
project_purpose: Automation for collecting, transforming and reporting data.
architectural_complexity: Medium
freelance_value: Useful for clients who need automated reporting, lead collection,
  scraping or data synchronisation.
client_problem_type:
- Automated reporting
- Lead collection
- Data synchronisation
node_count: 10
connection_count: 12
branching_factor: 2
trigger_nodes:
- When clicking ‘Test workflow’
external_services:
- Airtable
- HTTP API
key_patterns:
- api_ingestion
dedup_fingerprint: 3ebeae2331c98587ac31cc5093866aea39b82492
analysis_version: 2.1.1
---

# Workflow: Search LinkedIn companies and add them to Airtable CRM

## 1. Executive Summary
Automation for collecting, transforming and reporting data.

## 2. Why This Matters
Useful for clients who need automated reporting, lead collection, scraping or data synchronisation.

## 3. Node Inventory
- When clicking ‘Test workflow’ (n8n-nodes-base.manualTrigger)
- Process Each Company (n8n-nodes-base.splitInBatches)
- Get Company Info (n8n-nodes-base.httpRequest)
- Filter Valid Companies (n8n-nodes-base.if)
- Check If Company Exists (n8n-nodes-base.airtable)
- Is New Company? (n8n-nodes-base.if)
- Add Company to CRM (n8n-nodes-base.airtable)
- Set Variables (n8n-nodes-base.set)
- Search Companies (n8n-nodes-base.httpRequest)
- Extract Company Data (n8n-nodes-base.splitOut)

## 4. Integration Surface
Airtable, HTTP API

## 5. Detected Patterns
- api_ingestion

## 6. Architecture Notes
Primary category: **Data_Integration**  
Secondary category: **Orchestration_Reliability**  
Complexity: **Medium**

## 7. Reusable Insight
Client problems this pattern can answer: Automated reporting, Lead collection, Data synchronisation

## 8. Workflow Metrics
- Node count: 10
- Connection count: 12
- Branching factor: 2
- Confidence: high

## 9. Classification Reasons
- n8n-nodes-base.httpRequest -> Data_Integration +3
- n8n-nodes-base.httpRequest -> Orchestration_Reliability +1
- n8n-nodes-base.airtable -> Data_Integration +3
- n8n-nodes-base.airtable -> Data_Integration +3
- n8n-nodes-base.httpRequest -> Data_Integration +3
- n8n-nodes-base.httpRequest -> Orchestration_Reliability +1
- HTTP Request found -> Data_Integration +2

## 10. Normalized JSON Excerpt
```json
{
  "name": "Search LinkedIn companies and add them to Airtable CRM",
  "nodes": [
    {
      "name": "add company to crm",
      "type": "n8n-nodes-base.airtable"
    },
    {
      "name": "check if company exists",
      "type": "n8n-nodes-base.airtable"
    },
    {
      "name": "get company info",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "name": "search companies",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "name": "filter valid companies",
      "type": "n8n-nodes-base.if"
    },
    {
      "name": "is new company?",
      "type": "n8n-nodes-base.if"
    },
    {
      "name": "when clicking ‘test workflow’",
      "type": "n8n-nodes-base.manualTrigger"
    },
    {
      "name": "set variables",
      "type": "n8n-nodes-base.set"
    },
    {
      "name": "process each company",
      "type": "n8n-nodes-base.splitInBatches"
    },
    {
      "name": "extract company data",
      "type": "n8n-nodes-base.splitOut"
    }
  ]
}
```
