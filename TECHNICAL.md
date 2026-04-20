# Snow NLU Agent — Technical Overview

## What It Does

Converts natural language questions into ServiceNow queries and returns human-readable answers.

**Example:**
- Input: "How many P1 incidents are breached?"
- Output: "3 active incidents matched and have breached SLA."

---

## Supported Query Types

| Type | Example | Answer From |
|------|---------|-------------|
| **Live Table** | "Who is assigned to INC001?" | ServiceNow API |
| **Knowledge** | "What is SLA for P1?" | ChromaDB (vector search) |
| **Hybrid** | "Show active incidents and explain policy" | Both |

---

## Flow / Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUESTION                            │
│              "How many P1 incidents are breached?"              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. ROUTER (router.py)                                          │
│     └─ Classify intent via regex patterns                       │
│        • LIVE: "inc", "breach", "assigned", "priority"         │
│        • KNOWLEDGE: "what is", "explain", "policy"             │
│        • HYBRID: matches both                                   │
│                                                                 │
│     Result: "live_table_query"                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────┐
│  LIVE PATH          │               │  KNOWLEDGE PATH     │
│ (live_data_service) │               │ (knowledge_service) │
└────────┬────────────┘               └──────────┬──────────┘
         │                                       │
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. QUERY PARSER (query_parser.py)                              │
│     └─ Use LLM (GPT-4.1-mini) to convert natural language      │
│        to structured JSON:                                      │
│        {                                                         │
│          "table": "incident",                                   │
│          "filters": {"priority": "1", "breached": true},       │
│          "aggregation": "count"                                 │
│        }                                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. BUILD SNOW QUERY                                            │
│     └─ Convert JSON filters to ServiceNow query string:        │
│        "priority=1^active=true"                                 │
│        (ServiceNow uses ^ for AND, not JSON)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. CALL SERVICENOW API (sn_get function)                       │
│     └─ GET /api/now/table/incident                              │
│        Params: sysparm_query, sysparm_fields, sysparm_limit    │
│        Auth: HTTPBasicAuth (SN_USER, SN_PASSWORD)              │
│                                                                 │
│     Returns: Raw incident records                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. SLA BREACH CHECK (if breached=true)                         │
│     └─ Query task_sla table: "has_breached=true^active=true"  │
│        Filter incidents to only breached ones                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. FORMAT ANSWER                                               │
│     └─ clean_incident_record() → normalize fields              │
│        format_count_answer() → "3 active incidents matched..." │
│                                                                 │
│     Final Response:                                             │
│     {                                                           │
│       "answer": "3 active incidents matched...",              │
│       "records": [...]                                         │
│     }                                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Processing Summary

| Step | Component | What Happens |
|------|-----------|--------------|
| 1 | Router | Classifies question type (live/knowledge/hybrid) |
| 2 | Query Parser | LLM converts question → JSON query spec |
| 3 | Query Builder | JSON → ServiceNow query string |
| 4 | ServiceNow API | Fetches real-time data |
| 5 | SLA Filter | Joins with task_sla for breach check |
| 6 | Formatter | Cleans data + returns answer |

---

## API Endpoint

```
POST /ask
Body: { "question": "..." }
```

Returns:
```json
{
  "intent": "live_table_query",
  "answer": "3 active incidents matched...",
  "records": [...]
}
```

---

## Tech Stack

- **FastAPI** — Web server
- **OpenAI GPT-4.1-mini** — Query parsing + embeddings
- **ChromaDB** — Knowledge base vector store
- **ServiceNow REST API** — Live data
- **Docker** — Containerization

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SN_INSTANCE` | ServiceNow URL |
| `SN_USER` | ServiceNow username |
| `SN_PASSWORD` | ServiceNow password |
| `OPENAI_API_KEY` | OpenAI for LLM + embeddings |