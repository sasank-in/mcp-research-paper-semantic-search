# API Documentation

Complete reference for the Research Paper Semantic Search system, which
exposes three interfaces over the same LangChain + pgvector core:

| Interface | Transport | Use it for |
|---|---|---|
| [REST API](#rest-api) | HTTP, default `http://127.0.0.1:8000` | Web UI, scripts, external services |
| [MCP tools](#mcp-tools) | stdio (JSON-RPC) | Claude Desktop, Claude Code, any MCP client |
| [Python API](#python-api) | in-process | Notebooks, custom pipelines |

For installation and configuration, see [QUICKSTART.md](QUICKSTART.md).

---

## Conventions

**Base URL** — `http://127.0.0.1:8000` unless `--host`/`--port` are changed.

**Content type** — all request and response bodies are `application/json`,
except file upload, which is `multipart/form-data`.

**Similarity scores** — cosine relevance in the range `0.0`–`1.0`, where
higher is more similar. Scores are relative to the corpus, so an absolute
value is only meaningful compared against other results for the same query.

**Filenames** — every client-supplied filename is reduced to a bare basename
before use. `../../etc/passwd.pdf` is treated as `passwd.pdf` and looked up
only inside `data/papers` and `data/uploads`. Non-`.pdf` names are rejected.

**Sessions** — chat history is keyed by `session_id`. Sessions are independent
and held in memory, so they are cleared when the server restarts. The web UI
generates one id per browser tab, so tabs do not share a conversation.

---

## REST API

### `GET /health`

Liveness check and effective configuration.

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "healthy",
  "version": "3.0.0",
  "model": "openai/gpt-oss-120b"
}
```

---

### `POST /api/search`

Semantic search over indexed papers. No LLM is involved, so this is the
fastest and cheapest way to retrieve evidence.

**Request**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Natural-language search text |
| `top_k` | integer | no | `5` | Number of passages to return |
| `selected_file` | string \| null | no | `null` | Restrict to one paper, e.g. `attention.pdf` |

**Response** — an array of results, most similar first.

| Field | Type | Description |
|---|---|---|
| `content` | string | The passage text |
| `source` | string | Source filename |
| `page` | integer \| null | Zero-based page number |
| `similarity` | number | Cosine relevance, `0.0`–`1.0` |

```bash
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "multi-head attention", "top_k": 1}'
```

```json
[
  {
    "content": "Multi-head attention allows the model to jointly attend to\ninformation from different representation subspaces...",
    "source": "attention.pdf",
    "page": 1,
    "similarity": 0.6195
  }
]
```

An empty array means no matches — usually an empty corpus. Check with
`GET /api/files` or `python cmd_basis.py list`.

---

### `POST /api/chat`

Ask a question answered by an LLM. With `use_rag` enabled (the default) the
answer is grounded in retrieved passages and cites its sources.

Follow-up questions are resolved against the session's history, so
*"What BLEU score did it achieve?"* correctly resolves *"it"* from the
previous turn before retrieval runs.

**Request**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | string | yes | — | The question |
| `use_rag` | boolean | no | `true` | Ground the answer in the papers |
| `top_k` | integer | no | `5` | Passages to retrieve as context |
| `selected_file` | string \| null | no | `null` | Restrict retrieval to one paper |
| `session_id` | string | no | `"default"` | Conversation this turn belongs to |

**Response**

| Field | Type | Description |
|---|---|---|
| `response` | string | The answer, with inline citations |
| `model` | string | Model that produced it |
| `context_used` | boolean | Whether passages were retrieved |
| `sources` | string[] | Filenames cited |

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many attention heads are used?", "top_k": 2}'
```

```json
{
  "response": "The model uses **8 parallel attention heads** (h = 8)【attention.pdf】.",
  "model": "openai/gpt-oss-120b",
  "context_used": true,
  "sources": ["attention.pdf"]
}
```

Setting `use_rag: false` skips retrieval entirely and answers from the model's
own knowledge; `context_used` is then `false` and `sources` is empty.

---

### `GET /api/chat/history`

Return one session's conversation.

| Query param | Type | Default |
|---|---|---|
| `session_id` | string | `"default"` |

```bash
curl "http://127.0.0.1:8000/api/chat/history?session_id=alice"
```

```json
{
  "history": [
    { "role": "human", "content": "How many heads?" },
    { "role": "ai", "content": "The model uses **8 parallel attention heads**..." }
  ]
}
```

`role` is `human` or `ai`.

---

### `POST /api/chat/clear`

Discard one session's history. Other sessions are unaffected.

| Query param | Type | Default |
|---|---|---|
| `session_id` | string | `"default"` |

```bash
curl -X POST "http://127.0.0.1:8000/api/chat/clear?session_id=alice"
```

```json
{ "message": "Chat history cleared" }
```

---

### `GET /api/files`

List PDFs on disk and whether each is indexed.

| Field | Type | Description |
|---|---|---|
| `name` | string | Filename |
| `path` | string | Path on disk |
| `type` | string | `existing` (`data/papers`) or `uploaded` (`data/uploads`) |
| `size` | integer | Bytes |
| `indexed` | boolean | Whether it is searchable |

```json
{
  "files": [
    {
      "name": "attention.pdf",
      "path": "data\\papers\\attention.pdf",
      "type": "existing",
      "size": 1743,
      "indexed": true
    }
  ]
}
```

A file with `"indexed": false` is on disk but not yet searchable — index it
with `POST /api/files/process/{filename}`.

---

### `POST /api/files/upload`

Upload a PDF into `data/uploads`. Uploading does **not** index the file;
call the process endpoint afterwards.

**Request** — `multipart/form-data` with a single `file` field.

```bash
curl -X POST http://127.0.0.1:8000/api/files/upload \
  -F "file=@/path/to/paper.pdf"
```

```json
{
  "message": "File uploaded successfully",
  "filename": "paper.pdf",
  "size": 284119
}
```

If the name is already taken, a timestamp is appended
(`paper_20260915_124533.pdf`); the response reports the name actually used.

---

### `POST /api/files/process/{filename}`

Index a PDF so it becomes searchable. The file must already exist in
`data/papers` or `data/uploads`.

Re-processing a paper **replaces** its previous chunks rather than duplicating
them, so this is safe to call repeatedly.

```bash
curl -X POST http://127.0.0.1:8000/api/files/process/paper.pdf
```

```json
{
  "message": "File processed successfully",
  "filename": "paper.pdf",
  "pages": 2,
  "chunks_inserted": 2
}
```

---

### `GET /`

Serves the web UI. Falls back to a minimal HTML page linking to `/docs` if
`frontend/index.html` is missing.

### `GET /docs`

Interactive OpenAPI documentation, generated by FastAPI.

---

## Error responses

Errors return a JSON body with a `detail` string.

```json
{ "detail": "File not found: nope.pdf" }
```

| Status | Meaning | Common cause |
|---|---|---|
| `400` | Bad request | Non-PDF filename, or a name that sanitizes to nothing |
| `404` | Not found | Named PDF is not in `data/papers` or `data/uploads` |
| `422` | Unprocessable | Malformed body, or a PDF with no extractable text (see below) |
| `500` | Server error | Database unreachable, or the LLM provider rejected the call |

A `500` mentioning `model ... does not exist` means `GROQ_MODEL` names a model
your key cannot use — see [Troubleshooting](QUICKSTART.md#troubleshooting).

A `422` from the process endpoint saying no text could be extracted means the
PDF has no text layer — its pages are images. Scanned papers must be run
through OCR before they can be indexed:

```bash
ocrmypdf scanned.pdf searchable.pdf
```

Then upload and process `searchable.pdf` instead.

---

## MCP Tools

The MCP server exposes the corpus to MCP clients such as Claude Desktop and
Claude Code over stdio.

**Start it**

```bash
python cmd_basis.py mcp
# equivalently: python -m mcp_server.server
```

**Register it** — copy [mcp_server/claude_desktop_config.example.json](mcp_server/claude_desktop_config.example.json)
into your client config (`%APPDATA%\Claude\claude_desktop_config.json` on
Windows) and restart the client:

```json
{
  "mcpServers": {
    "research-papers": {
      "command": "C:\\path\\to\\python.exe",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:\\path\\to\\mcp-research-paper-semantic-search"
    }
  }
}
```

Replace both paths with your own. `command` must be the interpreter of the
environment where `requirements.txt` is installed, and `cwd` must be this
repository — the server resolves `data/papers` and `data/uploads` relative to
it. To find your values:

```bash
conda activate environ
python -c "import sys; print(sys.executable)"   # -> command
pwd                                             # -> cwd
```

On Windows, escape backslashes in the JSON (`C:\Users\...`).

### `search_papers`

Raw passages with source and similarity. Prefer this when you want evidence
rather than prose.

| Param | Type | Required | Default |
|---|---|---|---|
| `query` | string | yes | — |
| `top_k` | integer | no | `5` |
| `filename` | string \| null | no | `null` |

```
[1] attention.pdf, page 1 (similarity 0.4767)
Multi-head attention allows the model to jointly attend to
information from different representation subspaces at different
positions. We employ h = 8 parallel attention layers, or heads.
```

### `ask_papers`

A synthesized answer with citations. Costs an LLM call.

| Param | Type | Required | Default |
|---|---|---|---|
| `question` | string | yes | — |
| `top_k` | integer | no | `5` |
| `filename` | string \| null | no | `null` |

```
Positional information is added to the token embeddings through positional
encoding, which injects knowledge of each token's relative or absolute
position using sine and cosine functions [attention.pdf].

Sources: attention.pdf
```

This tool does not carry conversation history — each call is independent, so
questions must be self-contained.

### `list_papers`

No parameters. Reports what is indexed, and separately what is on disk but
not yet indexed.

```
Indexed and queryable:
  - attention.pdf

On disk but not indexed (run ingest_pdf):
  - bert.pdf
```

### `ingest_pdf`

Index a PDF already present in `data/papers` or `data/uploads`. Replaces
existing chunks for that filename rather than duplicating.

| Param | Type | Required |
|---|---|---|
| `filename` | string | yes |

```
Indexed attention.pdf: 2 pages, 2 chunks.
```

Tools report failures as readable text rather than raising, so a missing file
returns `'nope.pdf' not found in data/papers or data/uploads.`

---

## Python API

Import the core modules directly for notebooks or custom pipelines.

### `core.rag`

```python
from core import rag

# Semantic search — no LLM
results = rag.search("attention mechanism", top_k=5, source=None)
# -> [{"content": ..., "source": ..., "page": ..., "similarity": ...}, ...]

# Question answering with citations
answer = rag.ask(
    "How does multi-head attention work?",
    session_id="default",   # conversation to attach this turn to
    top_k=5,
    source=None,            # or "attention.pdf" to restrict
    use_history=True,       # False makes the call stateless
)
# -> {"answer": ..., "sources": [...], "model": ..., "context_used": True}

rag.clear_history("default")
```

### `core.ingest`

```python
from core import ingest

ingest.ingest_pdf("data/papers/attention.pdf")
# -> {"filename": "attention.pdf", "pages": 2, "chunks": 2}

ingest.ingest_directory("data/papers")
# -> {"processed": [...], "failed": [...], "total_chunks": 12}
```

`ingest_pdf(..., replace=False)` appends instead of replacing.

### `core.vectorstore`

```python
from core import vectorstore

vectorstore.list_sources()              # -> ["attention.pdf", ...]
vectorstore.delete_source("old.pdf")    # -> number of chunks removed
vectorstore.get_retriever(top_k=5)      # LangChain retriever, for custom chains
vectorstore.get_vectorstore()           # the underlying PGVector store
```

The embedding model and vector store are cached per process, so repeated calls
do not reload the model.

---

## CLI

Start the server with `python main.py` — it runs the same app as
`cmd_basis.py api` but checks your configuration and database connection
first. Use the `api` subcommand below only when you need a non-default host or
port.

```bash
python cmd_basis.py setup                      # create extension + tables
python cmd_basis.py ingest                     # index data/papers
python cmd_basis.py ingest --file paper.pdf    # index one file
python cmd_basis.py search "query" --top-k 5   # semantic search
python cmd_basis.py ask "question"             # answer with citations
python cmd_basis.py list                       # list indexed papers
python cmd_basis.py api --port 8080            # web UI + REST API, custom port
python cmd_basis.py mcp                        # MCP server over stdio
```

`search` and `ask` both accept `--file <name>` to restrict to one paper.

---

## Configuration

Read from `.env` (see [.env.example](.env.example)).

| Variable | Default | Description |
|---|---|---|
| `DB_NAME` | `vector_db` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `password` | Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_COLLECTION` | `paper_chunks` | LangChain collection name |
| `GROQ_API_KEY` | — | Required for chat and `ask` |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Chat model |
| `EMBEDDING_MODEL` | `sentence-transformers/all-mpnet-base-v2` | 768-dim embeddings |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `PAPERS_DIR` | `data/papers` | Source PDFs |
| `UPLOADS_DIR` | `data/uploads` | Uploaded PDFs |

Changing `EMBEDDING_MODEL` or `CHUNK_SIZE` requires re-indexing, since existing
vectors were built with the previous settings.
