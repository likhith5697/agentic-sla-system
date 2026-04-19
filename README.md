# Snow NLU Agent

Natural Language Understanding agent for ServiceNow. Converts user questions into ServiceNow queries and returns human-readable answers.

## Overview

This project provides a FastAPI-based service that:
1. **Classifies** user questions as knowledge, live data, or hybrid queries
2. **Parses** natural language into structured ServiceNow queries using LLM
3. **Fetches** real-time data from ServiceNow tables (incident, task_sla)
4. **Answers** questions using semantic search over knowledge base + live data

## Architecture

```
User Question
     │
     ▼
┌─────────────────┐
│  Router         │  ← Classifies intent (knowledge/live/hybrid)
│  (router.py)    │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌───────┐ ┌───────┐   ┌──────────┐
│Knowledge│ │ Live  │   │ Hybrid   │
│Service │ │ Data  │   │ Service  │
└───┬───┘ └───┬───┘   └────┬─────┘
    │         │            │
    ▼         ▼            ▼
ChromaDB   ServiceNow   Combined
(embeddings)  API        results
```

## Intent Classification

| Intent | Patterns | Example |
|--------|----------|---------|
| `live_table_query` | incident, breach, active, count, list, assigned | "How many P1 incidents are breached?" |
| `knowledge_query` | what is, how does, policy, definition, explain | "What is the SLA for P1 incidents?" |
| `hybrid_query` | Both live + knowledge patterns | "Show active incidents and explain SLA policy" |

## Services

### Query Parser (`query_parser.py`)
- Uses **GPT-4.1-mini** to convert natural language → JSON
- Extracts: table, filters (priority, active, breached), aggregation (count/list)

### Live Data Service (`live_data_service.py`)
- Executes real-time queries against ServiceNow REST API
- Tables: `incident`, `task_sla` (for SLA breach checking)
- Returns formatted answers + raw records

### Knowledge Service (`knowledge_service.py`)
- Semantic search over embedded knowledge base
- Uses **ChromaDB** + OpenAI embeddings
- Answers "what is" / "how does" questions

### Hybrid Service (`hybrid_service.py`)
- Combines knowledge + live data results
- Merges sources from both services

## API Endpoints

### `GET /`
Health check.

**Response:**
```json
{"status": "running"}
```

### `POST /ask`
Ask a question about ServiceNow data or knowledge base.

**Request:**
```json
{
  "question": "How many P1 incidents are breached?"
}
```

**Response:**
```json
{
  "intent": "live_table_query",
  "answer": "3 active incidents matched and have breached SLA.",
  "sources": [],
  "records": [
    {
      "number": "INC001234",
      "short_description": "Server down",
      "state": "In Progress",
      "priority": "1",
      "assigned_to": "John Doe",
      "assignment_group": "Infrastructure"
    }
  ]
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SN_INSTANCE` | ServiceNow instance URL (e.g., `https://dev12345.service-now.com`) |
| `SN_USER` | ServiceNow username |
| `SN_PASSWORD` | ServiceNow password |
| `OPENAI_API_KEY` | OpenAI API key for LLM + embeddings |
| `CHROMA_DB_PATH` | Path to ChromaDB (optional, default: `./chroma_db`) |

## ServiceNow Query Syntax

ServiceNow uses encoded query strings (not JSON):

```
priority=1^active=true           # P1 AND active
has_breached=true^active=true    # Breached SLAs
state=1^ORstate=2                # New OR In Progress
```

Operators: `=` (equals), `^` (AND), `^OR` (OR), `!=`, `<=`, `>=`, `LIKE`, `IN`

## Tech Stack

- **FastAPI** — Web framework
- **OpenAI** — LLM (GPT-4.1-mini) for query parsing + embeddings
- **ChromaDB** — Vector database for knowledge base
- **Requests** — ServiceNow REST API calls
- **Docker** — Containerization

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SN_INSTANCE="https://your-instance.service-now.com"
export SN_USER="admin"
export SN_PASSWORD="your-password"
export OPENAI_API_KEY="sk-..."

# Run the server
uvicorn app.main:app --reload

# Test
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many P1 incidents are breached?"}'
```

## Docker

```bash
# Build and run
docker-compose up --build

# The API will be available at http://localhost:8000
```

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── router.py            # Intent classification
│   ├── services/
│   │   ├── query_parser.py      # LLM-based query parsing
│   │   ├── live_data_service.py # ServiceNow live queries
│   │   ├── knowledge_service.py # Semantic search
│   │   └── hybrid_service.py    # Combined results
│   ├── scripts/
│   │   ├── ingest.py             # Load knowledge base
│   │   └── snow_fetch.py         # Fetch ServiceNow data
│   └── utils/
│       ├── embeddings.py         # OpenAI embedding helper
│       └── text.py               # Text utilities
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```