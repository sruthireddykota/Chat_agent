# Chat Agent — Multi-Agent AI Chatbot System

A modular, multi-agent AI chatbot built with Streamlit and FastAPI, featuring specialized agents for general conversation, code analysis, document retrieval (RAG), and real-time web research. Supports multi-modal input, streaming responses, Redis-backed conversation history, and a full document ingestion pipeline backed by Qdrant and MongoDB.

[view presentation](https://gamma.app/docs/Multi-Agent-Chatbot-System-86qc53lupy60giu)

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Agents](#agents)
- [Pages](#pages)
- [Services](#services)
- [MCP Server](#mcp-server)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Docker](#docker)
- [Dependencies](#dependencies)

---

## Features

- **4 specialized AI agents** — Generic, Coder, RAG, and Researcher
- **Streaming responses** via the Microsoft Agent Framework
- **Multi-modal input** — text, images, and documents
- **Redis-backed conversation history** with configurable message limits
- **MongoDB** for persistent chat session storage
- **Qdrant** vector database for semantic document retrieval
- **Document ingestion pipeline** — parse, chunk, embed, and store documents
- **MCP integration** for RAG retrieval, chat history, and Brave web search
- **FastAPI backend** for agent orchestration
- **Dockerized** deployment with `docker-compose`

---

## Project Structure

```
Chat_agent/
│
├── agents/                         # Specialized AI agent modules
│   ├── Coder.py                    # Code analysis, debugging & execution agent
│   ├── Generic.py                  # General-purpose conversation agent
│   ├── RAG_agent.py                # Document retrieval & Q&A agent
│   ├── Researcher.py               # Real-time web search & research agent
│   ├── rag_agent_evaluation.py     # RAG agent evaluation utilities
│   └── __init__.py
│
├── azure_clients/                  # Azure LLM client setup
│
├── config/                         # App configuration
│   ├── settings.py                 # Centralized settings (Redis, MCP, Azure URLs)
│   └── __init__.py
│
├── mcp_service/                    # MCP server for tools
│   ├── mcp_server.py               # Exposes rag_retrieve, get_chat_history, brave_web_search
│   ├── requirements_mcp.txt
│   ├── Dockerfile.mcpserver
│   └── __init__.py
│
├── Mongodb/                        # MongoDB integration
│   ├── mongodb_server.py           # Chat session persistence
│   └── __init__.py
│
├── pages/                          # Streamlit UI pages
│   ├── chatbot.py                  # Main chat interface
│   ├── docling_parser.py           # Document parsing & ingestion pipeline
│   ├── knowledge_management.py     # View & manage knowledge base documents
│   ├── rag_evaluation.py           # RAG evaluation dashboard
│   └── __init__.py
│
├── services/                       # Core backend services
│   ├── chat_history_retrieval.py   # Fetch conversation history
│   ├── chunking.py                 # Document chunking logic
│   ├── embeddings.py               # Embedding generation
│   ├── qdrant_retrevial.py         # Semantic search in Qdrant
│   ├── qdrant_store.py             # Store embeddings in Qdrant
│   ├── query_embeddings.py         # Query embedding utilities
│   └── __init__.py
│
├── utils/
│   ├── logger.py                   # Centralized logging via get_logger()
│   ├── rag_metrics.py              # RAG evaluation metrics
│   └── __init__.py
│
├── assets/                         # Static assets (images, logos)
├── logs/                           # Application logs
├── qdrant_storage/                 # Local Qdrant storage volume
├── tests/                          # Test suite
│
├── main.py                         # Streamlit app entry point
├── fastapi_chatapp.py              # FastAPI backend for agent orchestration
├── docker-compose.yml              # Multi-service Docker orchestration
├── Dockerfile.chatapp              # Streamlit app container
├── Dockerfile.fastapi              # FastAPI backend container
├── requirements.txt
└── README.md
```

---

## Agents

All agents share a consistent architecture: an **Azure Client** for LLM connectivity, the **Microsoft Agent Framework** for agent creation and streaming, and configurable **message stores** (in-memory, Redis, or MongoDB).

### Generic Agent — `agents/Generic.py`

General-purpose conversational agent. Default for queries that don't require specialized tools.

- Multi-modal input (text, images, documents)
- Redis-backed conversation history for text queries
- In-memory store for file-based queries (avoids storing binary data in Redis)
- Session-based history with configurable limits

### Coder Agent — `agents/Coder.py`

Specialized for code analysis, debugging, and execution.

- `HostedCodeInterpreterTool` for live code execution
- Structured markdown responses: Summary → Code Analysis → Solution → Execution → Next Steps
- Text files embedded in code blocks and stored in Redis
- Image files processed as `DataContent` with in-memory storage
- Redis-backed history for iterative debugging sessions

### RAG Agent — `agents/RAG_agent.py`

Answers questions from a knowledge base via MCP-integrated document retrieval.

- `rag_retrieval(query)` — semantic similarity search over document chunks
- `get_history()` — fetches prior conversation turns for follow-up awareness
- Classifies each query as new or follow-up before retrieval
- Citation tracking and hallucination prevention
- Returns `"No relevant data found"` when context is insufficient

### Researcher Agent — `agents/Researcher.py`

Real-time web research using the Brave Search API.

- `web_search(query, freshness)` with recency filters: `pd` / `pw` / `pm` / `py`
- Redis conversation history across research sessions
- Search strategy by query type:

| Query Type | Strategy |
|---|---|
| Current events | Direct search with freshness filter |
| Technical topics | Wikipedia first, then recent sources |
| Comparisons | Search each item separately |
| Latest/recent | Use `pd` or `pw` freshness |

---

## Pages

### `pages/chatbot.py` — Chat Interface

Main conversational UI. Supports agent selection, session management, and real-time streaming.

- Sidebar: agent selector, new/clear chat, session history list
- Input: text + file attachments (images encoded as base64)
- All messages persisted to MongoDB

### `pages/docling_parser.py` — Document Parser

Pipeline UI for ingesting documents (files or URLs) into the knowledge base.

**Sidebar settings:** output format (`md`/`json`/`html`/`text`), OCR, table extraction, picture description, code enrichment, formula enrichment, image scale, and table extraction mode.

**Pipeline flow:**

```
Parse → View Content → Generate Chunks → View Chunks
     → Generate Embeddings → View Count → Store (Qdrant + MongoDB)
```

### `pages/knowledge_management.py` — Knowledge Management

Dashboard for viewing and managing stored documents. Supports deletion from both MongoDB and Qdrant simultaneously.

### `pages/rag_evaluation.py` — RAG Evaluation

Dashboard for evaluating RAG agent performance using metrics from `utils/rag_metrics.py`.

---

## Services

| Service | File | Description |
|---|---|---|
| Chat History | `chat_history_retrieval.py` | Retrieve prior conversation turns |
| Chunking | `chunking.py` | Split documents into chunks for embedding |
| Embeddings | `embeddings.py` | Generate vector embeddings from text |
| Qdrant Retrieval | `qdrant_retrevial.py` | Semantic search over stored embeddings |
| Qdrant Store | `qdrant_store.py` | Persist embeddings into Qdrant |
| Query Embeddings | `query_embeddings.py` | Embed user queries for retrieval |

---

## MCP Server

**File:** `mcp_service/mcp_server.py`  
**URL:** `http://localhost:8000/mcp`

Exposes three tools used by agents:

| Tool | Used By | Description |
|---|---|---|
| `rag_retrieve` | RAG Agent | Semantic search over the knowledge base |
| `get_chat_history` | RAG Agent | Fetch prior conversation turns |
| `brave_web_search` | Researcher Agent | Real-time web search via Brave API |

---

## Configuration

**File:** `config/settings.py`

| Setting | Value |
|---|---|
| Redis URL | `redis://localhost:6379` |
| Redis max messages | `5` |
| Redis thread ID format | `session_{session_id}` |
| MCP server URL | `http://localhost:8000/mcp` |
| Azure Client | `azure_clients.azure_client.get_client()` |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Redis
- MongoDB
- Qdrant
- Docling serve
- Brave Search API key (for Researcher agent)

### Installation

```bash
git clone https://github.com/your-org/Chat_agent.git
cd Chat_agent

python -m venv myvenv
source myvenv/bin/activate  # Windows: myvenv\Scripts\activate

pip install -r requirements.txt
```

### Running Locally

```bash
# Start the MCP server
cd mcp_service
pip install -r requirements_mcp.txt
python mcp_server.py

# Start the FastAPI backend
python fastapi_chatapp.py

# Start the Streamlit app
streamlit run main.py
```

---

## Docker

All services are orchestrated via `docker-compose.yml`.

```bash
docker-compose up --build
```

**Dockerfiles:**

| File | Service |
|---|---|
| `Dockerfile.chatapp` | Streamlit UI |
| `Dockerfile.fastapi` | FastAPI backend |
| `mcp_service/Dockerfile.mcpserver` | MCP server |

---

## Dependencies

Core dependencies from `requirements.txt`:

- `streamlit` — UI framework
- `fastapi` / `uvicorn` — API backend
- `agent_framework` — Microsoft Agent Framework (ChatAgent, streaming, tools)
- `redis` — conversation history
- `pymongo` — MongoDB integration
- `qdrant-client` — vector store
- `asyncio` — async agent execution

---

## License

See [LICENSE](./LICENSE) for details.