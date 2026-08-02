# Chat Agent

Chat Agent is a Dockerized multi-agent application with a React frontend and FastAPI backend. It provides Generic, Coder, Researcher, and RAG agents, document ingestion, workspace browsing, and RAG evaluation.

## Architecture

```text
Browser → React frontend (:80) → FastAPI REST API (:8001)
                                      ├─ MongoDB: sessions, messages, metadata
                                      ├─ Redis: internal agent publish/cache support
                                      ├─ Qdrant: document vectors and retrieval
                                      ├─ Docling: document parsing
                                      └─ MCP server: RAG, history, and web search tools
```

The frontend uses REST/HTTP only. It does not open a websocket connection. Redis remains an internal backend dependency.

## Project Structure

```text
Chat_agent/
├── app/
│   ├── agents/
│   │   ├── base/
│   │   │   ├── agent_executor.py
│   │   │   ├── base_agent.py
│   │   │   ├── mcp_manager.py
│   │   │   ├── redis_cache_storage.py
│   │   │   └── redis_manager.py
│   │   ├── coder/
│   │   │   ├── coder_agent.py
│   │   │   └── __init__.py
│   │   ├── generic/
│   │   │   ├── generic_agent.py
│   │   │   └── __init__.py
│   │   ├── rag/
│   │   │   ├── rag_agent.py
│   │   │   └── __init__.py
│   │   ├── researcher/
│   │   │   ├── researcher_agent.py
│   │   │   └── __init__.py
│   │   ├── instructions/
│   │   │   ├── coder_agent_instructions.py
│   │   │   ├── generic_agent_instructions.py
│   │   │   ├── rag_agent_insturctions.py
│   │   │   └── researcher_agent_instructions.py
│   │   ├── tools/
│   │   │   ├── coder_agent_tools.py
│   │   │   ├── rag_agent_tools.py
│   │   │   └── researcher_agent_tools.py
│   │   └── skills/
│   │       ├── academic-research/SKILL.md
│   │       ├── code-architecture/SKILL.md
│   │       ├── jupyter-notebook/SKILL.md
│   │       ├── python-coding/SKILL.md
│   │       ├── research-brief/SKILL.md
│   │       └── sql-coding/SKILL.md
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   └── routers/
│   │       ├── chat.py
│   │       ├── documents.py
│   │       ├── health.py
│   │       ├── metrics.py
│   │       ├── sessions.py
│   │       └── user.py
│   ├── azure_clients/
│   │   ├── azure_client.py
│   │   ├── azure_gpt5_client.py
│   │   ├── embedding_client.py
│   │   └── title_azure_client.py
│   ├── config/settings.py
│   ├── mcp/
│   │   ├── Dockerfile.mcpserver
│   │   ├── mcp_server.py
│   │   └── requirements_mcp.txt
│   ├── models/
│   │   ├── agents.py
│   │   ├── constants.py
│   │   └── mongo.py
│   ├── repositeries/mongodb_server.py
│   ├── services/
│   │   ├── chat_history_retrieval.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── qdrant_retrevial.py
│   │   ├── qdrant_store.py
│   │   └── query_embeddings.py
│   └── utils/
│       ├── file_browser.py
│       ├── logger.py
│       ├── rag_metrics.py
│       ├── script_runner.py
│       └── tools.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── config.js
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── AgentActivityPanel.jsx
│   │   │   ├── AgentPills.jsx
│   │   │   ├── AppShell.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── ChatSidebar.jsx
│   │   │   ├── FileExplorerPanel.jsx
│   │   │   ├── Logo.jsx
│   │   │   ├── PlanPrompt.jsx
│   │   │   ├── ReasoningBlock.jsx
│   │   │   ├── TaskList.jsx
│   │   │   ├── TopBar.jsx
│   │   │   ├── ToolCallCard.jsx
│   │   │   └── ui.jsx
│   │   ├── context/AppContext.jsx
│   │   ├── data/mockData.js
│   │   ├── hooks/useAgentChat.js
│   │   ├── pages/
│   │   │   ├── Chatbot.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── DocumentParser.jsx
│   │   │   ├── KnowledgeManagement.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── RagEvaluation.jsx
│   │   │   └── WorkspaceExplorer.jsx
│   │   ├── services/api.js
│   │   └── utils/
│   │       ├── fileTree.js
│   │       └── highlight.js
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── tests/
├── documentation/                # demo images, videos, and notes
├── docker-compose.yml
├── Dockerfile.chatapp
├── Dockerfile.fastapi
├── requirements.txt
└── README.md
```

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

## Chat flow

1. Select Generic, Coder, Researcher, or RAG in the React chatbot.
2. The frontend sends `POST /api/v1/agent/run`.
3. FastAPI creates and invokes the selected agent.
4. User and assistant messages are saved to MongoDB.
5. The completed REST response is rendered in the UI.

Chat attachments are converted to base64 and sent in `query.files`. The Coder agent uses an isolated workspace at `CODER_BASE_PATH/<session_id>`. Generated files are loaded by `GET /api/v1/workspace/{session_id}`.

## Document ingestion flow

The Document Parser follows the original staged process:

```text
File or URL
  → Docling parse
  → Display parsed content
  → Generate token chunks
  → Generate embeddings
  → Store vectors in Qdrant
  → Store document metadata in MongoDB
```

The React page supports PDF, DOCX, XLSX, CSV, JPEG, and PNG files, plus document URLs. It exposes separate actions for parsing, chunking, embedding, and storage.

Endpoints:

```text
POST /api/v1/documents/parse
POST /api/v1/documents/parse-url
POST /api/v1/documents/chunks
POST /api/v1/documents/embeddings
POST /api/v1/documents/store-embeddings
POST /api/v1/documents/store
GET  /api/v1/documents/get
```

## RAG flow and evaluation

Documents are embedded into the `Documents` Qdrant collection. The RAG agent calls the MCP `rag_retrive` tool, which returns both a formatted response and the retrieved `chunks`. Those chunks are preserved as `context` and passed to RAG evaluation.

The RAG Evaluation page accepts a CSV containing a `Questions`, `question`, or `Question` column. It runs each question through the RAG agent, calculates Answer Relevance, Context Relevance, and Groundedness with DeepEval, saves scores to MongoDB, and displays the results.

```csv
Questions
What is the main topic of the document?
Summarize the key findings.
```

Evaluation endpoint:

```text
POST /api/v1/metrics/evaluate
GET  /api/v1/metrics/averages
```

## Services

| Service | Port | Purpose |
|---|---:|---|
| React frontend | 80 | Browser UI |
| FastAPI | 8001 | REST API and agent orchestration |
| MongoDB | 27017 | Sessions, messages, metadata, evaluation records |
| Mongo Express | 8081 | MongoDB browser |
| Redis | 6379 | Internal agent publishing and cache support |
| Qdrant | 6333 | Vector storage and retrieval |
| Docling | 5001 | Document conversion |
| MCP server | 8000 | RAG, history, and web-search tools |

## Configuration

Create a root `.env` file and do not commit secrets.
Refer `.env_example`

## Docker commands

Start or rebuild the complete stack:

```bash
docker compose up -d --build
```

Rebuild only the backend or frontend:

```bash
docker compose up -d --build fastapi
docker compose up -d --build frontend
```

Open the UI at [http://localhost](http://localhost). Check the API at [http://localhost:8001/api/v1/health](http://localhost:8001/api/v1/health).


## Presentation

[view presentation](https://docs.google.com/presentation/d/1-Fq1xk-EuLj7SGsEnSPTA03t266wOiaD/edit?usp=sharing&ouid=102516658501058113497&rtpof=true&sd=true)

[view gamma presentation](https://multi-agent-chatbot-syst-70gddpc.gamma.site/)

---

## License

See [LICENSE](./LICENSE) for details.