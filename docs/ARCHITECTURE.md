# System Architecture

## High-level overview

One shared core, four interfaces. Everything routes through `core/`, so the
REST API, MCP server, CLI, and Python API all answer identically.

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Web UI     │   REST API   │  MCP server  │     CLI      │
│  frontend/   │  api/app.py  │ mcp_server/  │ cmd_basis.py │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │
       └──────────────┴──────┬───────┴──────────────┘
                             ▼
                  ┌─────────────────────┐
                  │        core/        │
                  │  rag · ingest ·     │
                  │  vectorstore ·      │
                  │  paths · config     │
                  └──────────┬──────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌────────────────────┐        ┌────────────────────┐
   │ PostgreSQL         │        │ Groq               │
   │ + pgvector         │        │ (ChatGroq)         │
   │ via LangChain      │        │                    │
   │ PGVector           │        │                    │
   └────────────────────┘        └────────────────────┘
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `core/config.py` | Environment-backed settings; single source of truth |
| `core/vectorstore.py` | PGVector store, cached embedding model, metadata queries |
| `core/ingest.py` | PDF loading, chunking, indexing |
| `core/rag.py` | LCEL retrieval chain, sessions, search |
| `core/paths.py` | Filename sanitization and lookup |
| `api/app.py` | HTTP surface and web UI hosting |
| `mcp_server/server.py` | MCP tool definitions over stdio |

`core/` has no knowledge of HTTP or MCP, so an interface can be added or
removed without touching retrieval logic.

---

## Ingestion pipeline

```
PDF file
   │
   ▼  PyPDFLoader
Documents (one per page)
   │    metadata: {filename, source, page}
   ▼  RecursiveCharacterTextSplitter
Chunks (800 chars, 100 overlap)
   │    separators: ["\n\n", "\n", " ", ""]
   ▼  delete_source(filename)      ← replaces prior chunks
   │
   ▼  HuggingFaceEmbeddings.embed_documents (batched)
768-dim vectors, L2-normalized
   │
   ▼  PGVector.add_documents
langchain_pg_embedding
```

Two properties worth noting:

**Idempotent.** Each chunk carries `filename` in its metadata, and ingestion
deletes existing chunks for that filename before inserting. Re-indexing a paper
replaces rather than duplicates, so `ingest` is safe to re-run.

**Batched.** Embeddings are generated in one `add_documents` call per file
rather than per chunk, and the model is loaded once per process
(`lru_cache`) rather than per request.

---

## Query pipelines

### Semantic search — no LLM

```
query string
   │
   ▼  cached embedding model
query vector (768-dim)
   │
   ▼  PGVector.similarity_search_with_relevance_scores
   │     optional metadata filter: {"filename": {"$eq": ...}}
   ▼
[(Document, score), ...]  →  [{content, source, page, similarity}, ...]
```

The file filter is pushed into the SQL query, not applied afterwards. Scoping
to one paper returns the top-k chunks *from that paper*, rather than filtering a
global top-k down to whatever remains.

### RAG — LCEL chain

```
{input, chat_history}
   │
   ├─ chat_history empty? ──── yes ──→ use input verbatim
   │                                          │
   └─ no ──→ contextualize prompt │ LLM ──────┤  (resolves "it", "that", ...)
                                              ▼
                                      standalone question
                                              │
                                              ▼  retriever (top-k, optional filter)
                                        [Document, ...]
                                              │
                                              ▼  format_docs → cited context blocks
                                              ▼  answer prompt │ ChatGroq │ StrOutputParser
                                       {answer, context}
```

The contextualize step is skipped when there is no history, avoiding a wasted
LLM round-trip on the first turn of every conversation.

Built from `langchain-core` primitives rather than the legacy `langchain.chains`
helpers, which moved to the `langchain-classic` compatibility package in
LangChain 1.x.

---

## Database schema

LangChain's PGVector manages two tables. Collections namespace the corpus;
embeddings hold the chunks.

```sql
CREATE TABLE langchain_pg_collection (
    uuid       UUID PRIMARY KEY,
    name       VARCHAR NOT NULL UNIQUE,   -- DB_COLLECTION, default paper_chunks
    cmetadata  JSON
);

CREATE TABLE langchain_pg_embedding (
    id             VARCHAR PRIMARY KEY,
    collection_id  UUID REFERENCES langchain_pg_collection(uuid),
    embedding      vector(768),
    document       VARCHAR,               -- chunk text
    cmetadata      JSONB                  -- {filename, source, page}
);

CREATE INDEX ix_cmetadata_gin
    ON langchain_pg_embedding USING gin (cmetadata jsonb_path_ops);
```

Chunk provenance lives in `cmetadata`, which is what makes per-file scoping and
idempotent re-indexing work. The GIN index makes those metadata filters fast.

### Vector indexing

**LangChain does not create a vector index.** Similarity search runs an exact
scan, which is accurate and fine for hundreds or low thousands of chunks. At
larger scale, add an approximate index manually:

```sql
CREATE INDEX ON langchain_pg_embedding
USING hnsw (embedding vector_cosine_ops);

ANALYZE langchain_pg_embedding;
```

HNSW gives better recall-versus-speed than IVFFlat and needs no training step
or `lists` tuning. Either way the index is approximate — it trades a little
recall for a large speed gain, so add one when scan time becomes the
bottleneck, not before.

---

## Retrieval mechanics

Similarity is cosine distance, via pgvector's `<=>` operator:

```
distance   = 1 - (A · B) / (‖A‖ × ‖B‖)
similarity = 1 - distance
```

Embeddings are L2-normalized at generation time, so the magnitude terms cancel
and cosine distance reduces to a dot product.

Scores are relative to the corpus. An absolute value is only meaningful
compared against other results for the same query — 0.45 may be the best match
in one corpus and mediocre in another.

---

## Design decisions

**Why chunk at 800 characters?** Long enough to hold a complete idea, short
enough that a single embedding represents it faithfully. A whole page averages
into a vector that matches everything weakly and nothing precisely. The 100-char
overlap keeps a sentence spanning a boundary retrievable from either side.

**Why `all-mpnet-base-v2`?** Strong quality-per-cost on semantic similarity,
runs on CPU, and 768 dimensions keeps storage and scan cost reasonable. Changing
it requires re-indexing, since existing vectors were built under the old model.

**Why cache the embedding model?** It is several hundred MB and takes seconds to
load. Loading per request — as the original implementation did — dominated
query latency.

**Why sessions rather than one global history?** A module-level history is
shared by every concurrent user of the API, so one person's conversation leaks
into another's. Histories are keyed by `session_id` and isolated.

---

## Security model

**Filename handling.** Every client-supplied filename is reduced to a bare
basename before use, and the resolved path is confirmed to sit inside an
allowed directory. `../../etc/passwd.pdf` becomes `passwd.pdf` and is looked up
only in `data/papers` and `data/uploads`; non-`.pdf` names are rejected. This
applies to uploads, the process endpoint, and the `ingest_pdf` MCP tool alike.

**SQL.** All queries are parameterized. Collection and filename values are
bound, never interpolated.

**Secrets.** Credentials come from `.env`, which is gitignored. Nothing is
committed.

**Current limitations** — the API has no authentication and allows all CORS
origins, so it assumes a trusted local network. Tighten both before exposing it
beyond localhost. Uploaded PDFs are parsed but not scanned.

---

## Performance characteristics

| Operation | Cost | Notes |
|---|---|---|
| Embedding model load | seconds | Once per process, then cached |
| Embed one query | ~10–50 ms | CPU |
| Similarity search | O(n) scan | Fast to ~10⁴ chunks; add HNSW beyond |
| Metadata-filtered search | O(n) scan | GIN index narrows the candidate set |
| Ingest one paper | seconds | Dominated by embedding generation |
| RAG answer | 1–3 s | One or two LLM calls plus retrieval |

A RAG answer costs two LLM calls when history needs resolving, one otherwise.

---

## Extension points

**Different LLM.** Swap `ChatGroq` in `core/rag.py` for any LangChain chat
model. The chain is provider-agnostic.

**Different embeddings.** Change `EMBEDDING_MODEL` in `.env` and re-index.
Update the `vector(n)` dimension if the new model differs from 768.

**Hybrid search.** Combine the vector retriever with a keyword retriever using
LangChain's `EnsembleRetriever` in `core/vectorstore.py`.

**Reranking.** Wrap the retriever in `ContextualCompressionRetriever` with a
cross-encoder to reorder candidates before they reach the prompt.

**More MCP tools.** Add a decorated function in `mcp_server/server.py`; it is
discovered automatically. Keep the docstring precise — clients use it to decide
when to call the tool.

**HTTP transport for MCP.** `MCPServer` supports `streamable-http` alongside
stdio, for remote clients.
