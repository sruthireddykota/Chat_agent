# Agents Module Documentation

## Presentation Link

[view presentation](https://gamma.app/docs/Multi-Agent-Chatbot-System-86qc53lupy60giu)


## Overview

The agents module provides a collection of specialized AI agents designed to handle different types of user queries and tasks. Each agent is optimized for a specific use case — from general conversation to code analysis, document retrieval, and web research. Users select the desired agent from the sidebar based on their query requirements.

| Agent | Purpose | Key Features |
|-------|---------|--------------|
| **Generic Agent** | General conversation and file analysis | Multi-modal input, Redis message history |
| **Coder Agent** | Code analysis, debugging, and execution | Code interpreter, syntax analysis, runtime testing |
| **RAG Agent** | Document retrieval and Q&A | Knowledge base search, citation tracking, context awareness |
| **Researcher Agent** | Real-time web search and research | Brave Search integration, multi-source synthesis |

---

## System Architecture

All agents share a consistent architecture built on three core components: an **Azure Client** for LLM connectivity, the **Microsoft Agent Framework** for agent creation, tool integration, and streaming responses, and **Message Stores** supporting in-memory, Redis-backed, and MongoDB conversation history.

### Data Flow

1. User input arrives with optional file attachments
2. Uploaded files are detected and handled based on type (text, image, document)
3. The appropriate message store is selected (in-memory, Redis, or MongoDB via MCP)
4. The `ChatAgent` is initialized with instructions, tools, and the message store
5. The agent executes and streams response chunks to the caller
6. Exceptions are logged and managed throughout the pipeline

### Executor Pattern

Each agent implements an executor function that creates a new event loop for async operations, manages the async generator lifecycle, yields response chunks to the caller, and ensures proper cleanup and logging.

---

## Agent Modules

### Generic Agent — `Generic.py`

Handles general-purpose conversations and basic file analysis. Serves as the default agent for queries that do not require specialized tools or knowledge retrieval.

**Features:** multi-modal input (text, images, documents), Redis-backed conversation history, file content analysis, and session-based message storage with configurable history limits.

**Method: `generic_agent(query, session_id)`**

- Detects file attachments and creates multi-modal messages using `DataContent`
- Uses in-memory `ChatMessageStore` for file-based queries to avoid storing binary data in Redis
- Uses `RedisChatMessageStore` for text-only queries to maintain conversation history
- Streams responses through the `ChatAgent` framework

**Instructions:** analyze file context before responding when files are present; provide answers strictly from the given context; maintain simplicity and accuracy.

---

### Coder Agent — `Coder.py`

Specializes in code analysis, debugging, and execution through integrated tools and structured response formatting.

**Features:** `HostedCodeInterpreterTool` for code execution, structured markdown responses, text and image file handling, and Redis-backed conversation history for iterative debugging.

**Method: `coder_agent(query, session_id)`**

File handling logic:
- **Text files** — decoded as UTF-8, embedded in code blocks, stored in Redis for conversation history
- **Image files** — processed as `DataContent` with media type, stored in-memory to avoid Redis binary storage

**Response structure:**
1. **Summary** — brief explanation of actions taken
2. **Code Analysis** — findings with severity levels
3. **Solution** — code fixes in Python blocks
4. **Execution** — runtime results and output
5. **Next Steps** — recommendations for improvements

The `HostedCodeInterpreterTool` is invoked when the user requests code execution or testing, when solution verification is needed, or when runtime analysis is required.

**Behavior guidelines:** if a file is provided, analyze it thoroughly before responding; if a query accompanies a file, use the file as context; if only a file is provided, give a comprehensive unprompted analysis.

---

### RAG Agent — `RAG_agent.py`

Answers questions using a knowledge base via MCP integration. Retrieves relevant documents, tracks citations, and provides responses grounded strictly in retrieved content.

**Features:** MCP integration for document retrieval, conversation history for follow-up questions, citation tracking, and hallucination prevention.

**Available tools:**

- `rag_retrieval(query: str)` — retrieves top-ranked document chunks from the knowledge base via semantic similarity
- `get_history()` — fetches previous conversation turns to support context-aware follow-ups

**Query processing logic:**

1. Classify the query as a follow-up or a new question
   - Follow-up: call `get_history()` then `rag_retrieval()`
   - New query: call `rag_retrieval()` immediately
2. If retrieved context is irrelevant, return `"No relevant data found for the query, try again later"`; otherwise generate a structured response with citations

---

### Researcher Agent — `Researcher.py`

Provides real-time web search via the Brave Search API, synthesizing information from multiple sources for current events and research queries.

**Features:** real-time web search, time-based result filtering, source citation, and Redis conversation history.

**Tool: `web_search(query: str, freshness: str)`**

The `freshness` parameter filters results by recency: `pd` (past day), `pw` (past week), `pm` (past month), `py` (past year).

**Search strategy:**

| Query Type | Strategy |
|------------|----------|
| Current events | Search directly with an appropriate freshness filter |
| Technical topics | Search Wikipedia first for background, then recent sources for updates |
| Comparisons | Search each item separately for comprehensive coverage |
| Latest/recent queries | Use `pd` or `pw` freshness filters |

---

## Dependencies and Configuration

**Core framework:** `agent_framework` (ChatAgent, ChatMessage, Role, DataContent), `agent_framework.redis` (RedisChatMessageStore), `azure_clients.azure_client` (get_client)

**Tools and services:** `HostedCodeInterpreterTool` (Coder Agent), `MCPStreamableHTTPTool` (RAG and Researcher Agents)

**Utilities:** `utils.logger` via `get_logger()`, `asyncio` for event loop management

**Redis** — URL: `redis://localhost:6379`, max messages: 5, thread ID format: `session_{session_id}`

**MCP Server** — URL: `http://localhost:8000/mcp`, tools: `rag_retrieve`, `get_chat_history`, `brave_web_search`

**Azure Client** — all agents use the centralized client from `azure_clients.azure_client.get_client()`


# Pages Module Documentation

## Overview

The `pages/` module contains the three main Streamlit UI pages of the Chat Agent system. Each page is a self-contained interface responsible for a distinct part of the user workflow.

| File | Page Title | Purpose |
|------|------------|---------|
| `chatbot.py` | Chat Agent | Conversational interface for interacting with AI agents |
| `docling_parser.py` | Document Parser | Upload and parse documents for ingestion into the knowledge base |
| `knowledge_management.py` | Knowledge Management | View and manage documents stored in the knowledge base |

---

## `chatbot.py` — Chat Interface

The main conversational UI page. Users can select an AI agent, start new chat sessions, switch between previous sessions, and stream responses in real time. All messages are persisted to MongoDB.

**Sidebar** contains a home button, agent selector, new/clear chat buttons, and a session list. The input widget accepts both text and file attachments.

**Message flow** when a query is submitted:
1. Build a user message dict
2. If an image file is attached, encode it as base64 and store it
3. Display the user message immediately in the chat UI
4. Save the user message to MongoDB

---

## `docling_parser.py` — Document Parser

A pipeline UI for parsing documents (files or URLs) using a Docling-compatible REST API, then generating chunks, embeddings, and storing them in Qdrant and MongoDB. Supports multiple output formats and configurable parsing options.

### Sidebar Settings

| Setting | Widget | Default | Description |
|---------|--------|---------|-------------|
| Output format | `selectbox` | `md` | Output format: `md`, `json`, `html`, `text` |
| Enable OCR | `checkbox` | Off | Optical character recognition |
| Enable Table Extraction | `checkbox` | On | Extracts table structure |
| Enable Picture Description | `checkbox` | On | Generates image descriptions via Vision API |
| Enable Code Enrichment | `checkbox` | Off | Enriches code blocks |
| Enable Formula Enrichment | `checkbox` | Off | Enriches mathematical formulas |
| Image Scale | `slider` | `2` | Image resolution scale (1–3) |
| Table Extraction Mode | `selectbox` | `Fast` | `Fast` or `Accurate` |

### URL Processing (Tab 2)

Accepts one or more URLs. On "Process URL" click, the input is split and stripped into individual URLs.

### Document Pipeline

The `document_pipeline()` function is shared between both tabs and implements a sequential, guided workflow — each step only appears after the previous button is clicked:

```
Parse Result
    └──▶ View Content
         └──▶ Generate Chunks
              └──▶ View Chunks
                   └──▶ Generate Embeddings
                        └──▶ View Embedding Count
                             └──▶ Store Embeddings
                                  └──▶ Qdrant + MongoDB storage
```

---

## `knowledge_management.py` — Knowledge Management

A document management dashboard that lists all documents stored in the knowledge base. Users can view document metadata and delete individual documents, which removes them from both MongoDB and Qdrant simultaneously.

# Chat_agent

## Project Structure
```
Chat_agent/
│
├── Mongodb/
│   └── mongodb_server.py
│
├── agents/
│   ├── Coder.py
│   ├── Generic.py
│   ├── RAG_agent.py
│   └── Researcher.py
│
├── azure_clients/
│
├── logs/
│
├── mcp_service/
│   ├── Dockerfile.mcpserver
│   ├── mcp_server.py
│   └── requirements_mcp.txt
│
├── pages/
│   ├── chatbot.py
│   ├── docling_parser.py
│   └── knowledge_management.py
│
├── services/
│   ├── chat_history_retrieval.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── qdrant_retrevial.py
│   ├── qdrant_store.py
│   └── query_embeddings.py
│
├── utils/
│   └── logger.py
│
├── docker-compose.yml
├── login page logo.png
├── main.py
├── Dockerfile.chatapp
├── Dockerfile.fastapi
├── fastapi_chatapp.py
└── requirements.txt
└── LICENSE
└── README.md

```
