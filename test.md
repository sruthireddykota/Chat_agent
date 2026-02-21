
## Overview

The `pages/` folder contains the Streamlit UI components for the Chat Agent application. These modules provide the user-facing interface for interacting with various AI agents and managing the knowledge base.

---

## File Structure

```
pages/
├── chatbot.py              # Main chat interface with multi-agent routing
├── docling_parser.py       # Document parsing and processing UI
└── knowledge_management.py # Knowledge base management interface
```

---

## 1. chatbot.py

### Purpose
Main chat interface that provides an intelligent routing system to direct user queries to specialized agents (RAG, Coder, Researcher, or Generic).

### Key Components

#### Agent Router
```python
def route_query(user_query: str, session_id: str) -> str
```
- **Purpose**: Analyzes user queries and routes them to the appropriate specialized agent
- **Routing Logic**:
  - **RAG Agent**: Document-related queries, knowledge base questions
  - **Coder Agent**: Code analysis, debugging, programming help
  - **Researcher Agent**: Web search, current events, research tasks
  - **Generic Agent**: General conversation, other queries

#### Session Management
- Unique session IDs for each user conversation
- Session-based chat history tracking
- Redis-backed message persistence (where applicable)

#### Agent Executors
The chatbot integrates with four specialized agents:

1. **rag_executor(query, session_id)**
   - Handles document retrieval and Q&A
   - Accesses knowledge base via MCP tools
   - Returns citation-backed answers

2. **coder_executor(query, session_id)**
   - Processes code analysis requests
   - Supports file uploads (code files, images)
   - Executes code via HostedCodeInterpreterTool

3. **researcher_executor(query, session_id)**
   - Performs web searches using Brave Search
   - Handles current events and research queries
   - Supports freshness filtering

4. **generic_executor(query, session_id)**
   - Handles general conversational queries
   - Processes file-based questions
   - Maintains conversation context

### UI Features

#### Chat Interface
- Streamlit-based chat display
- Message history with user/assistant differentiation
- Real-time streaming responses
- File upload support

#### File Handling
Supports multiple file types and integrates with query context

---

## 2. docling_parser.py

### Purpose
Provides a user interface for parsing documents using the Docling library and preparing them for ingestion into the knowledge base.

### Key Components

#### Document Parser Integration
- Supports multiple document formats (PDF, DOCX, PPTX, etc.)
- Extracts structured content (text, tables, images)
- Preserves document hierarchy

#### Document Processing Pipeline

1. **Upload Documents** - File uploader widget, multiple file support
2. **Parse Documents** - Convert to structured format, extract metadata
3. **Preview Results** - Display parsed content, show document structure
4. **Export for Ingestion** - Save to MongoDB, prepare for chunking

### Supported Formats
- PDF documents
- Microsoft Word (.docx)
- PowerPoint (.pptx)
- Plain text (.txt)
- Markdown (.md)

### UI Workflow

```
Upload → Parse → Preview → Store
  ↓       ↓        ↓        ↓
Files   Docling   Display  Qdrant
        Engine    Results  
```

---

## 3. knowledge_management.py

### Purpose
Administrative interface for managing the document knowledge base, including upload, deletion, and monitoring of stored documents.

### Key Components

#### Document Upload
- Batch document upload
- Format validation
- Metadata extraction
- Progress tracking

#### Document Management

**View Documents**
- List all stored documents
- Display metadata (title, upload date, size)
- Preview document content
- Search functionality

**Delete Documents**
- Select documents to remove
- Cascade deletion (MongoDB + Qdrant)
- Confirmation dialogs
- Audit logging

**Update Documents**
- Re-index existing documents
- Update metadata
- Refresh embeddings

#### Knowledge Base Statistics

Provides metrics including:
- Total documents count
- Total chunks
- Storage size
- Available collections

### UI Sections

#### 1. Dashboard
- Total documents count
- Storage usage
- Recent uploads
- System status

#### 2. Document Browser
Search and manage documents with metadata display

#### 3. Upload Interface
- Drag-and-drop file upload
- Batch processing status
- Real-time progress bars
- Error/success notifications

#### 4. Settings
- Chunk size configuration
- Overlap settings
- Embedding model selection
- Vector store parameters

### Integration Points

#### MongoDB Integration

#### Qdrant Integration
```python
from services.qdrant_store import QdrantStore

# Store vector embeddings
qdrant_store.add_vectors(
    document_id=str,
    vectors=List[float],
    metadata=dict
)
```

#### Processing Pipeline
```python
# Document → Chunks → Embeddings → Storage
from services.chunking import chunk_document
from services.embeddings import generate_embeddings

chunks = chunk_document(content)
embeddings = generate_embeddings(chunks)
store_vectors(embeddings)
```

---

## Common Dependencies

### External Libraries
```python
import streamlit as st          # UI framework
import asyncio                  # Async operations
from typing import Dict, List   # Type hints
```

### Internal Modules
```python
from agents.RAG_agent import rag_executor
from agents.Coder import coder_executor
from agents.Researcher import researcher_executor
from agents.Generic import generic_executor
from utils.logger import get_logger
```

---

## Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=chat_agent_db

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# MCP Service
MCP_SERVICE_URL=http://localhost:8000/mcp

---

---

## Deployment Considerations

### Performance
- Use st.cache_data for expensive operations
- Implement pagination for large document lists
- Async processing for long-running tasks
- Connection pooling for database access

### Security
- Input validation for file uploads
- SQL injection prevention
- XSS protection in user inputs
- Rate limiting on API calls

### Scalability
- Session state management
- Efficient database queries
- Vector store optimization
- Load balancing considerations

---

---

## Maintenance

### Monitoring
- Log file analysis
- Performance metrics
- Error rate tracking
- User session analytics

### Updates
- Dependency version management
- Security patches
- Feature additions
- Bug fixes

### Backup
- Document metadata backup
- Vector embeddings backup
- Configuration backup
- Session history backup

---

## Future Enhancements

### Planned Features
1. Multi-language support - UI translation
2. Advanced search - Filters, facets, and relevance ranking
3. Document versioning - Track document changes
4. Collaborative features - Shared knowledge bases
5. Analytics dashboard - Usage statistics and insights
6. Export functionality - Download processed documents
7. Batch operations - Bulk document management
8. Custom agents - User-defined agent configurations

### Performance Optimizations
- Caching layer for frequently accessed documents
- Lazy loading for large document lists
- Parallel processing for batch operations
- Database query optimization

---

## Support

### Troubleshooting

**Issue: Documents not appearing after upload**
- Check MongoDB connection
- Verify Qdrant service status
- Review processing logs
- Validate file format

**Issue: Slow query responses**
- Check Redis connection
- Review agent selection logic
- Monitor database performance
- Optimize vector similarity search

**Issue: File upload failures**
- Verify file size limits
- Check supported formats
- Review network connectivity
- Examine server logs

---

## Appendix

### Key Terms
- **Agent**: Specialized AI component for specific tasks
- **Router**: Query classification and agent selection logic
- **Session**: User conversation context and history
- **MCP**: Model Context Protocol for tool integration
- **RAG**: Retrieval Augmented Generation
- **Embedding**: Vector representation of text

### References
- Streamlit Documentation: https://docs.streamlit.io
- Agent Framework: Internal documentation
- Docling Library: Document parsing documentation
- Redis: https://redis.io/docs
- Qdrant: https://qdrant.tech/documentation

---

*Document Version: 1.0*  
*Last Updated: February 2024*  
*Maintained by: Development Team*
