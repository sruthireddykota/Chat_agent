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