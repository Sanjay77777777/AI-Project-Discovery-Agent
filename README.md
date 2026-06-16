# AI Project Discovery Agent

A local AI-powered repository intelligence and question answering system that indexes, searches, summarizes, and answers questions about software repositories using Retrieval-Augmented Generation (RAG).

---

## Overview

AI Project Discovery Agent helps developers understand unfamiliar codebases quickly. The system processes source files, generates vector embeddings, stores them in ChromaDB, performs semantic retrieval, and uses a local LLM to provide grounded answers based on repository content.

All processing runs locally using Ollama and ChromaDB — no external API calls, no data leaves your machine.

---

## Features

### Document Processing
- Recursive repository scanning
- Smart file filtering (`.git`, `node_modules`, `__pycache__`, etc.)
- Code, documentation, and config classification
- Chunk generation with configurable overlap

### Vector Search
- Embedding generation via Ollama (`nomic-embed-text`)
- Persistent storage in ChromaDB
- Semantic similarity search
- Repository-scoped collections

### Repository Question Answering
- Retrieve relevant chunks for any query
- Generate grounded answers using a local LLM (`qwen2.5-coder:7b`)
- Source attribution with file paths and relevance scores
- Hallucination guardrails — LLM answers from context only

### Repository Intelligence
- High-level repository summaries
- Architecture overview extraction
- Technology stack identification
- Automatic selection of high-value files (README, pyproject.toml, docs, etc.)

### Production Hardening
- Repository existence validation
- ChromaDB collection validation
- Empty retrieval fallback (no LLM call)
- LLM error handling with 503 status codes
- Configurable timeout protection
- Structured logging
- Clone URL validation (only `http`/`https` allowed — `file://`, `ssh://`, `git://` blocked)
- Shallow clone with configurable timeout and disk space check
- Sanitized error responses (no stack traces or filesystem paths leaked)

---

## Architecture

```text
Repository Files
       │
       ▼
Document Processor
  (walk + filter + classify)
       │
       ▼
Chunk Generator
  (overlap-aware splitting)
       │
       ▼
Ollama Embeddings
  (nomic-embed-text)
       │
       ▼
ChromaDB
  (persistent vector store)
       │
       ▼
RAGRetriever
  (semantic search)
       │
       ▼
Repository QA  ───  Repository Summary
       │                     │
       ▼                     ▼
Qwen 2.5 Coder          Qwen 2.5 Coder
       │                     │
       ▼                     ▼
Answer + Sources       Summary + Architecture + Tech Stack
```

---

## Tech Stack

### Backend
- **FastAPI** — async web framework
- **Python 3.12** — core language
- **Pydantic** — request/response models

### AI Components
- **Ollama** — local model runner
- **nomic-embed-text** — embeddings (768d)
- **qwen2.5-coder:7b** — answer generation

### Vector Database
- **ChromaDB** — persistent vector store

### Repository Management
- **GitPython** — git clone operations

---

## Project Structure

```text
├── main.py                        # FastAPI entry point
├── app/
│   ├── config.py                  # Global configuration
│   ├── api/
│   │   ├── rag.py                 # RAG endpoints
│   │   └── repository.py          # Repository management endpoints
│   ├── services/
│   │   ├── rag_service.py         # DocumentProcessor, RepositoryIndexer, RAGRetriever
│   │   ├── repository_qa.py       # RepositoryQA (RAG + LLM)
│   │   ├── repository_summary.py  # RepositorySummary (high-level overviews)
│   │   ├── ollama_service.py      # ask_llm wrapper
│   │   └── repository_service.py  # Clone / manage repos
│   └── models/
│       ├── rag.py                 # RAG request/response models
│       └── repository.py          # Repository models
├── repositories/                  # Cloned repos
└── vectordb/                      # ChromaDB persistent data
    └── chroma/
```

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| **RAM** | 8 GB | 16 GB |
| **Disk Space** | 5 GB | 10 GB+ |
| **CPU** | x86_64, 4 cores | x86_64, 8 cores |
| **OS** | Windows 10+, Linux, macOS 12+ | — |
| **Python** | 3.12 | 3.12 |
| **Ollama** | Installed and running | Latest version |

*Disk usage scales with the number and size of repositories indexed. Each repository typically requires 50–500 MB for ChromaDB storage plus the cloned source files.*

---

## Installation

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) (must be installed and running)

### Setup

```bash
git clone <your-repository-url>
cd AI-Project-Discovery-Agent

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Pull Ollama Models

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5-coder:7b
ollama list
```

---

## Usage

### Start the Server

```bash
uvicorn main:app --reload
```

Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Index a Repository

```bash
curl -X POST http://127.0.0.1:8000/rag/index-repository \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "fastapi"}'
```

### Ask a Question

```bash
curl -X POST http://127.0.0.1:8000/rag/qa \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "fastapi", "query": "What is APIRouter?", "top_k": 5}'
```

### Retrieve Chunks (No LLM)

```bash
curl -X POST http://127.0.0.1:8000/rag/ask-repository \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "fastapi", "query": "What is APIRouter?", "top_k": 5}'
```

### Generate Repository Summary

```bash
curl -X POST http://127.0.0.1:8000/rag/repository-summary \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "fastapi"}'
```

### List Collections

```bash
curl http://127.0.0.1:8000/rag/collections
```

### Delete Collection

```bash
curl -X DELETE http://127.0.0.1:8000/rag/collection/fastapi
```

---

## API Endpoints

### Repository Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/clone-repository?url=<git_url>` | Clone a remote repository |

### RAG — Repository Search & QA

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rag/index-repository` | Index a repository into ChromaDB |
| `POST` | `/rag/ask-repository` | Retrieve relevant chunks (no LLM) |
| `POST` | `/rag/qa` | Question answering with LLM |
| `POST` | `/rag/repository-summary` | Generate repository summary |
| `GET` | `/rag/collections` | List all indexed collections |
| `DELETE` | `/rag/collection/{repo_name}` | Delete an indexed collection |

### Error Codes

| Code | When |
|------|------|
| `404` | Repository not found on disk or not indexed |
| `503` | LLM unavailable (Ollama down or model missing) |
| `500` | Unexpected internal error |

---

## Example Results

### QA Response

```json
{
  "repo_name": "fastapi",
  "query": "What is APIRouter?",
  "answer": "APIRouter is a FastAPI class used to organize and structure API routes into reusable components. It supports HTTP methods (get, post, put, delete, etc.), WebSocket handling, and sub-router inclusion via include_router().",
  "sources": [
    {
      "content": "...",
      "file_path": "repositories/fastapi/docs/en/docs/reference/apirouter.md",
      "category": "docs",
      "chunk_id": "93d5bf39-...",
      "chunk_number": 1,
      "relevance_score": 0.8887
    }
  ],
  "source_summary": [
    {
      "file_path": "repositories/fastapi/docs/en/docs/reference/apirouter.md",
      "category": "docs",
      "relevance_score": 0.8887
    }
  ]
}
```

### Repository Summary Response

```json
{
  "repo_name": "fastapi",
  "summary": "FastAPI is a modern, high-performance web framework for building APIs with Python type hints...",
  "architecture": "FastAPI follows a layered architecture: Application Layer, Dependency Management, Validation (Pydantic), Routing & Serialization, Documentation...",
  "technologies": ["Python", "FastAPI", "Starlette", "Pydantic", "Uvicorn"],
  "sources": ["README.md", "pyproject.toml", "docs/en/docs/index.md"]
}
```

---

## Performance

Tested on the **FastAPI** repository:

| Metric | Value |
|--------|-------|
| Files processed | 1,800+ |
| Chunks indexed | 8,607 |
| Embedding dimensions | 768 |
| Chunk size | 2,000 chars |
| Chunk overlap | 200 chars |
| Retrieval backend | ChromaDB (cosine similarity) |
| Embedding model | nomic-embed-text |
| Answer generation | qwen2.5-coder:7b |

---

## Project Status

**Status:** Stable Release

**Version:** `v1.0`

---

## Future Improvements (Version 2 Roadmap)

- Language-aware retrieval
- Incremental indexing (re-index only changed files)
- Code-aware chunking (AST-based splitting)
- Retrieval re-ranking (cross-encoder scoring)
- Streaming responses
- Repository statistics endpoint
- Multi-repository search
- Cross-repository question answering
- Enhanced source citations with line numbers

---

## License

MIT License

---

## Author

**R. Sanjay**

AI Project Discovery Agent — Repository Intelligence using Local RAG, ChromaDB, Ollama, and FastAPI.
