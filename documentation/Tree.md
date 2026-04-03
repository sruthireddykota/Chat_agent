# Chat_agent

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