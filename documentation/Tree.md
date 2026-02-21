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
└── requirements.txt
```