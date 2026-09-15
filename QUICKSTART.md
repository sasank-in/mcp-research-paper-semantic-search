#  Quick Start Guide

## Prerequisites

- Conda environment `environ` (Python 3.12)
- PostgreSQL 12+ with the `pgvector` extension
- A Groq API key — https://console.groq.com

## 1. Install

```bash
conda activate environ
pip install -r requirements.txt
cp .env.example .env
```

## 2. Configure

Edit `.env`:

```
DB_NAME=vector_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_COLLECTION=paper_chunks

GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

## 3. Create the tables

```bash
python cmd_basis.py setup
```

## 4. Add and index papers

Drop PDFs into `data/papers/`, then:

```bash
python cmd_basis.py ingest
```

Re-running `ingest` replaces a paper's chunks rather than duplicating them,
so it is safe to run repeatedly.

## 5. Use it

```bash
# Semantic search (no LLM)
python cmd_basis.py search "attention mechanism in transformers"

# Ask a question, answered with citations
python cmd_basis.py ask "How does multi-head attention work?"

# Restrict either to one paper
python cmd_basis.py ask "What is the main result?" --file attention.pdf

# List what is indexed
python cmd_basis.py list
```

## 6. Start the server

```bash
python main.py
```

Then open http://127.0.0.1:8000 — the web UI and the REST API are both served
there, with interactive API docs at `/docs`.

`main.py` verifies your `.env`, API key, frontend files, and database
connection *before* binding the port, so a misconfiguration is reported with a
fix rather than surfacing later as a failed search. Use it unless you need a
different address:

```bash
python cmd_basis.py api --port 8080
python cmd_basis.py api --host 0.0.0.0    # reachable from other machines
```

Note that CORS is wide open by default, so tighten it before binding to a
public interface.

## 7. Use as an MCP server

Expose your papers as tools to an MCP client such as Claude Desktop:

```bash
python cmd_basis.py mcp     # or: python -m mcp_server.server
```

Copy `mcp_server/claude_desktop_config.example.json` into your Claude Desktop
config (`%APPDATA%\Claude\claude_desktop_config.json` on Windows) and restart
the app. Four tools become available:

| Tool | Purpose |
|---|---|
| `search_papers` | Raw passages with source and similarity score |
| `ask_papers` | Synthesized answer with citations |
| `list_papers` | What is indexed, and what is on disk but not yet indexed |
| `ingest_pdf` | Index a PDF sitting in `data/papers` or `data/uploads` |

## Troubleshooting

**`certificate verify failed` / `SSL_CERT_FILE` FileNotFoundError**
Conda sets `SSL_CERT_FILE` to a path that may not exist. Point it at certifi:

```bash
export SSL_CERT_FILE="$(python -c 'import certifi;print(certifi.where())')"
```

This repo's `environ` env already has an activation hook doing this.

**`model does not exist or you do not have access to it`**
Groq retires models regularly. List what your key can use:

```bash
python -c "from groq import Groq; from core import config; print([m.id for m in Groq(api_key=config.GROQ_API_KEY).models.list().data])"
```

then set `GROQ_MODEL` in `.env` accordingly.

**`pgvector extension not found`**
Install it: https://github.com/pgvector/pgvector#installation

**Search returns nothing**
Check that papers are indexed with `python cmd_basis.py list`.
