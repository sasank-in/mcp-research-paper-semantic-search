# AI Research Paper Semantic Search System

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-green.svg)](https://python.langchain.com/)
[![MCP](https://img.shields.io/badge/MCP-2.x-purple.svg)](https://modelcontextprotocol.io/)

Semantic search and retrieval-augmented question answering over a local corpus
of research papers. Drop PDFs in, and query them by meaning — through a web UI,
a REST API, a CLI, or as MCP tools inside Claude Desktop.

## What it does

Papers are chunked, embedded with `all-mpnet-base-v2`, and stored in PostgreSQL
with pgvector. Queries are embedded the same way and matched by cosine
similarity, so *"how do models attend to different positions"* finds the passage
about multi-head attention without sharing a single keyword with it.

Two query modes sit on top of that:

- **Semantic search** returns the matching passages themselves, with scores.
  No LLM, so it is fast and cheap.
- **Ask** retrieves passages and has an LLM synthesize an answer that cites the
  papers it used. Follow-up questions resolve against conversation history, so
  *"what BLEU score did it achieve?"* knows what "it" refers to.

## Quick start

```bash
conda activate environ
pip install -r requirements.txt
cp .env.example .env          # then add your Groq API key

python cmd_basis.py setup     # create extension + tables
# drop PDFs into data/papers/
python cmd_basis.py ingest

python cmd_basis.py search "attention mechanism in transformers"
python cmd_basis.py ask "How does multi-head attention work?"
python main.py                # web UI at http://127.0.0.1:8000
```

Full setup and troubleshooting: **[QUICKSTART.md](QUICKSTART.md)**

## Interfaces

| Interface | Start with | Reference |
|---|---|---|
| Web UI | `python main.py` | http://127.0.0.1:8000 |
| REST API | `python main.py` | [API_DOCUMENTATION.md](API_DOCUMENTATION.md#rest-api) |
| MCP server | `python cmd_basis.py mcp` | [API_DOCUMENTATION.md](API_DOCUMENTATION.md#mcp-tools) |
| CLI | `python cmd_basis.py --help` | [API_DOCUMENTATION.md](API_DOCUMENTATION.md#cli) |
| Python | `from core import rag` | [API_DOCUMENTATION.md](API_DOCUMENTATION.md#python-api) |

### Use it from Claude Desktop

The MCP server exposes the corpus as four tools — `search_papers`,
`ask_papers`, `list_papers`, and `ingest_pdf` — so Claude can query your papers
directly. Copy
[mcp_server/claude_desktop_config.example.json](mcp_server/claude_desktop_config.example.json)
into your Claude Desktop config and restart it. Details in
[API_DOCUMENTATION.md](API_DOCUMENTATION.md#mcp-tools).

## Architecture

```
                 PDFs in data/papers/ and data/uploads/
                                  │
                                  ▼
                    PyPDFLoader  →  RecursiveCharacterTextSplitter
                                    (800 chars, 100 overlap)
                                  │
                                  ▼
                    HuggingFaceEmbeddings (all-mpnet-base-v2, 768-dim)
                                  │
                                  ▼
                    PostgreSQL + pgvector  ←  LangChain PGVector store
                                  │
                      ┌───────────┴───────────┐
                      ▼                       ▼
              similarity search        LCEL retrieval chain
              (cosine, top-k)          (history-aware + ChatGroq)
                      │                       │
                      └───────────┬───────────┘
                                  ▼
                 REST API  ·  MCP server  ·  CLI  ·  Web UI
```

Everything routes through one core, so all four interfaces answer identically.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for more detail.

## Project structure

```
core/                    Shared engine — all interfaces build on this
  config.py              Environment-backed settings
  vectorstore.py         PGVector store + cached embedding model
  ingest.py              PDF loading, chunking, indexing
  rag.py                 LCEL retrieval chain, sessions, search
  paths.py               Filename sanitization
api/app.py               FastAPI REST API + web UI
mcp_server/server.py     MCP server (stdio)
frontend/                Web UI (vanilla HTML/CSS/JS)
cmd_basis.py             CLI entry point
main.py                  Server launcher (preflight checks, then serves)
data/papers/             Source PDFs
data/uploads/            Uploaded PDFs
```

## Technology stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Orchestration | LangChain 1.x (LCEL) |
| Vector store | PostgreSQL 12+ with pgvector |
| Embeddings | Sentence Transformers `all-mpnet-base-v2` (768-dim) |
| LLM | Groq (`openai/gpt-oss-120b` by default) |
| Agent interface | MCP 2.x |
| Web API | FastAPI + Uvicorn |
| PDF parsing | pypdf |

## Configuration

Settings live in `.env` — see [.env.example](.env.example) and the
[configuration table](API_DOCUMENTATION.md#configuration).

The essentials:

```
DB_NAME=vector_db
DB_USER=postgres
DB_PASSWORD=your_password
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Groq retires models regularly. If chat fails with *"model does not exist"*,
list what your key can use and update `GROQ_MODEL` — see
[Troubleshooting](QUICKSTART.md#troubleshooting).

## Documentation

| Document | Contents |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Installation, configuration, troubleshooting |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | REST, MCP, Python and CLI reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and data flow |
| [docs/FILE_MANAGEMENT_GUIDE.md](docs/FILE_MANAGEMENT_GUIDE.md) | Web UI walkthrough |

## Notes

- Re-indexing a paper replaces its chunks rather than duplicating them, so
  `ingest` is safe to re-run.
- Changing `EMBEDDING_MODEL` or `CHUNK_SIZE` requires re-indexing, since
  existing vectors were built with the previous settings.
- Chat history is in-memory and keyed by `session_id`; it clears on restart.
- The API allows all CORS origins by default — tighten this before exposing
  the server beyond localhost.
