# Chat Agent — Multi-Agent AI Chatbot System

A modular, multi-agent AI chatbot built with Streamlit and FastAPI, featuring specialized agents for general conversation, code analysis, document retrieval (RAG), and real-time web research. Supports multi-modal input, streaming responses, Redis-backed conversation history, and a full document ingestion pipeline backed by Qdrant and MongoDB.

[view presentation](https://multi-agent-chatbot-syst-70gddpc.gamma.site/)

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
- **Agent Skills** - Specialized skills for Coder and Researcher
- **Streaming responses** via the Microsoft Agent Framework
- **Multi-modal input** — text, images, and documents
- **Redis-backed conversation history** with configurable message limits
- **MongoDB** for persistent chat session storage
- **Qdrant** vector database for semantic document retrieval
- **Document ingestion pipeline** — parse, chunk, embed, and store documents
- **MCP integration** for RAG retrieval, chat history, and Brave web search
- **Coder workspace** — isolated per-session filesystem with inline file browser and full explorer page
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
│   ├── workspace_explorer.py       # Full-page Coder workspace file browser
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
│   ├── file_browser.py             # Workspace file browser component (inline + explorer)
│   ├── logger.py                   # Centralized logging via get_logger()
│   ├── rag_metrics.py              # RAG evaluation metrics
│   └── __init__.py
│
├── assets/                         # Static assets (images, logos)
├── logs/                           # Application logs
├── qdrant_storage/                 # Local Qdrant storage volume
├── agent_data/                     # Coder agent workspace (bind-mounted to /workspace)
│   └── filemanager/
│       └── <session_id>/           # Isolated workspace per chat session
│           ├── src/                # Python source files
│           ├── tests/              # Test files
│           ├── requirements.txt
│           └── README.md
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

Specialized for code analysis, debugging, and execution with an isolated per-session filesystem workspace.

- `HostedCodeInterpreterTool` for live code execution
- `MCPStdioTool` with `@modelcontextprotocol/server-filesystem` for file I/O
- Isolated workspace per session at `CODER_BASE_PATH/<session_id>/`
- Enforces project structure: `src/` for modules, `tests/` for test files
- Skill-driven development: loads `python-coding` or `sql-coding` skill before every task
- Lint and validation scripts run automatically after code generation
- Redis-backed history for iterative debugging sessions
- Structured markdown responses: Summary → Script Output → Solution → Issues → Next Steps

#### Coder Workspace Flow

```
User submits query (Coder agent selected)
  → _create_workspace(session_id) creates /workspace/filemanager/<session_id>/
  → MCPStdioTool mounts that directory as the agent's filesystem root
  → Agent writes files using relative paths (e.g. src/main.py)
  → Streaming response completes
  → Inline file browser appears below the response
  → User can click any file to preview with syntax highlighting
  → "Workspace Explorer" button in sidebar opens full-page explorer

New query submitted
  → Inline file browser is hidden until next response completes
  → File selection is reset

Agent switched away from Coder
  → All file browser state is cleared
  → Browser never renders for non-Coder agents
```

#### Workspace structure enforced by agent

```
/workspace/filemanager/<session_id>/
├── src/
│   └── <module>.py
├── tests/
│   └── test_<module>.py
├── requirements.txt
└── README.md
```

### RAG Agent — `agents/RAG_agent.py`

Answers questions from a knowledge base via MCP-integrated document retrieval.

- `rag_retrieval(query)` — semantic similarity search over document chunks
- `get_history()` — fetches prior conversation turns for follow-up awareness
- Classifies each query as new or follow-up before retrieval
- Citation tracking and hallucination prevention
- Returns `"No relevant data found"` when context is insufficient

### Researcher Agent — `agents/Researcher.py`

Real-time web research using the Brave Search API and Hugging Face MCP.

- `web_search(query, freshness)` with recency filters: `pd` / `pw` / `pm` / `py`
- `repo_search`, `papers_search`, `spaces_search`, `documentation_search`, `repository_details` via Hugging Face MCP
- Redis conversation history across research sessions
- Search strategy by query type:

| Query Type | Strategy |
|---|---|
| Current events | Direct web search with freshness filter |
| Scientific / technical | Academic research + web search |
| Machine learning / AI | Hugging Face MCP + academic research |
| Literature review | Academic research first, then HF MCP / web search |

---

## Pages

### `pages/chatbot.py` — Chat Interface

Main conversational UI. Supports agent selection, session management, and real-time streaming.

- Sidebar: agent selector (Generic / Coder / Researcher / RAG), new/clear chat, session history list
- Sidebar: **Workspace Explorer** button appears when Coder agent is active
- Input: text + file attachments (images encoded as base64)
- All messages persisted to MongoDB
- Inline file browser rendered below agent response (Coder only, resets on new query)

### `pages/workspace_explorer.py` — Workspace Explorer

Full-page file browser for the Coder agent's session workspace. Accessible via the sidebar button in the chat page.

- Sidebar navigation: Home and Back to Chat buttons
- Left panel: grouped directory tree with folder headers and file buttons
- Right panel: syntax-highlighted preview for Python, SQL, Markdown, JSON, YAML, shell scripts, and more
- CSV files rendered as interactive dataframes
- Per-file download button with file size display
- Scoped entirely to the active session — switching sessions resets selection
- Guard: redirects non-Coder sessions with a warning

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

## Utils

### `utils/file_browser.py` — File Browser Component

Reusable workspace file browser used by both the inline chat view and the full explorer page.

| Function | Used by | Description |
|---|---|---|
| `render_file_browser(workspace, session_id)` | `chatbot.py` | Inline two-column browser below agent response |
| `_collect_files(workspace)` | Both | Walks workspace, skips `__pycache__`, `.git`, `.venv` |
| `_render_content(path, ext, lang_hint)` | Both | Renders preview: code block / dataframe / markdown / text |
| `LANG_MAP` | Both | Maps file extensions to language labels and syntax hints |
| `ICON_MAP` | Both | Maps file extensions to display icons |

**State management:**
- Selected file stored in `st.session_state` under key `fb_sel_<session_id>`
- Resets to `None` after each new agent response
- Cleared entirely when switching away from the Coder agent
- Never bleeds between sessions — all keys are session-scoped

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

The Coder agent uses a separate local MCP server — `@modelcontextprotocol/server-filesystem` — spawned as a stdio subprocess per session, scoped to that session's workspace directory.

---

## Configuration

**File:** `config/settings.py`

| Setting | Value |
|---|---|
| Redis URL | `redis://localhost:6379` |
| Redis max messages | `8` |
| MCP server URL | `http://localhost:8000/mcp` |
| Coder base path | `/workspace/filemanager` (container) |
| Azure Client | `azure_clients.azure_client.get_client()` |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Redis
- MongoDB
- Qdrant
- Docling serve
- Node.js 20+ (for Coder agent MCP filesystem server)
- Brave Search API key (for Researcher agent)

### Installation

```bash
cd Chat_agent

python -m venv myvenv
source myvenv/bin/activate  # Windows: myvenv\Scripts\activate

pip install -r requirements.txt

# Install MCP filesystem server globally (required for Coder agent)
npm install -g @modelcontextprotocol/server-filesystem
```

### Running Locally

```bash
# Start the MCP server
cd mcp_service
pip install -r requirements_mcp.txt
python mcp_server.py

# Start the FastAPI backend
python fastapi_chatapp.py

# Create the coder workspace directory
mkdir -p ./agent_data/filemanager

# Start the Streamlit app
streamlit run main.py
```

---

## Docker

All services are orchestrated via `docker-compose.yml`.

```bash
# Create workspace directory before first run
mkdir -p ./agent_data/filemanager

docker-compose up --build
```

**Dockerfiles:**

| File | Service |
|---|---|
| `Dockerfile.chatapp` | Streamlit UI + Coder agent (includes Node.js 20 + MCP filesystem server) |
| `Dockerfile.fastapi` | FastAPI backend |
| `mcp_service/Dockerfile.mcpserver` | MCP server |

**Volume mounts:**

| Host path | Container path | Purpose |
|---|---|---|
| `./agent_data` | `/workspace` | Coder agent session workspaces |
| `./qdrant_storage` | `/qdrant/storage` | Qdrant vector data |

---

## Dependencies

Core dependencies from `requirements.txt`:

- `streamlit` — UI framework
- `fastapi` / `uvicorn` — API backend
- `agent_framework` — Microsoft Agent Framework (Agent, streaming, tools)
- `agent_framework_redis` — Redis-backed conversation history provider
- `redis` — conversation history
- `pymongo` — MongoDB integration
- `qdrant-client` — vector store
- `asyncio` — async agent execution

---

## Presentation

[view presentation](https://docs.google.com/presentation/d/1-Fq1xk-EuLj7SGsEnSPTA03t266wOiaD/edit?usp=sharing&ouid=102516658501058113497&rtpof=true&sd=true)

[view gamma presentation](https://multi-agent-chatbot-syst-70gddpc.gamma.site/)

---

## License

See [LICENSE](./LICENSE) for details.
