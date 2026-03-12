# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  CLI (main.py)              │         REST API (FastAPI)    │
│  - setup                    │         - POST /search        │
│  - ingest                   │         - GET /health         │
│  - search                   │         - GET /docs           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Ingestion Pipeline          │      Query Engine            │
│  ├─ load_pdfs.py            │      └─ query_engine.py      │
│  ├─ chunk_documents.py      │                               │
│  ├─ build_embeddings.py     │                               │
│  └─ pipeline.py             │                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PostgreSQL + pgvector                                       │
│  └─ paper_chunks table                                       │
│     ├─ id (SERIAL)                                           │
│     ├─ content (TEXT)                                        │
│     ├─ embedding (vector(768))                               │
│     ├─ source (TEXT)                                         │
│     └─ created_at (TIMESTAMP)                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Ingestion Pipeline

```
┌──────────┐
│   PDFs   │
│ (6 files)│
└────┬─────┘
     │
     ▼
┌─────────────────┐
│  load_pdfs.py   │  ← PyPDFLoader extracts text
│  Returns: List  │
│  of Documents   │
└────┬────────────┘
     │
     ▼
┌──────────────────┐
│chunk_documents.py│  ← RecursiveCharacterTextSplitter
│  Chunk size: 800 │     Overlap: 100 chars
│  Returns: Chunks │
└────┬─────────────┘
     │
     ▼
┌───────────────────┐
│build_embeddings.py│  ← Sentence Transformers
│  Model: all-mpnet │     Dimensions: 768
│  Returns: Vectors │
└────┬──────────────┘
     │
     ▼
┌──────────────────┐
│   pipeline.py    │  ← Batch insert (50 chunks)
│  Store in DB     │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│  PostgreSQL DB   │
│  + pgvector      │
└──────────────────┘
```

### Search Pipeline

```
┌──────────────┐
│ User Query   │
│ "attention   │
│  mechanism"  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Generate Query   │  ← Sentence Transformers
│ Embedding        │     768-dimensional vector
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Vector Similarity│  ← Cosine distance
│ Search in DB     │     ORDER BY embedding <=> query
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Top-K Results    │  ← Default: 5 results
│ with Similarity  │     Scores: 0.0 - 1.0
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Display Results  │
└──────────────────┘
```

## Component Interaction

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│             │         │              │         │             │
│  CLI/API    │────────▶│  Business    │────────▶│  Database   │
│  Interface  │         │  Logic       │         │  Layer      │
│             │◀────────│              │◀────────│             │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │                        │                        │
   Commands              Processing                 Storage
   Results               Embeddings                 Retrieval
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
├─────────────────────────────────────────────────────────────┤
│  • CLI (argparse)                                            │
│  • FastAPI (REST API)                                        │
│  • Swagger UI (API docs)                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
├─────────────────────────────────────────────────────────────┤
│  • Python 3.8+                                               │
│  • LangChain (document processing)                           │
│  • Sentence Transformers (embeddings)                        │
│  • psycopg2 (database driver)                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        Database                              │
├─────────────────────────────────────────────────────────────┤
│  • PostgreSQL 12+                                            │
│  • pgvector extension                                        │
│  • IVFFlat index                                             │
└─────────────────────────────────────────────────────────────┘
```

## Embedding Model Architecture

```
Input Text
    │
    ▼
┌─────────────────┐
│  Tokenization   │  ← Convert text to tokens
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Transformer    │  ← all-mpnet-base-v2
│  Encoder        │    (12 layers, 768 hidden)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Mean Pooling   │  ← Average token embeddings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Normalization  │  ← L2 normalization
└────────┬────────┘
         │
         ▼
   768-dim Vector
```

## Database Schema Details

```sql
-- Main table
CREATE TABLE paper_chunks (
    id SERIAL PRIMARY KEY,           -- Auto-incrementing ID
    content TEXT NOT NULL,            -- Chunk text content
    embedding vector(768),            -- 768-dimensional vector
    source TEXT,                      -- Source PDF filename
    created_at TIMESTAMP DEFAULT NOW  -- Insertion timestamp
);

-- Vector index for fast similarity search
CREATE INDEX paper_chunks_embedding_idx 
ON paper_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Analyze for query optimization
ANALYZE paper_chunks;
```

## Search Algorithm

```
1. Input: User query string
2. Generate query embedding (768-dim vector)
3. Calculate cosine distance to all stored embeddings
4. Sort by distance (ascending)
5. Return top-K results with similarity scores
6. Similarity = 1 - cosine_distance

Cosine Distance Formula:
distance = 1 - (A · B) / (||A|| × ||B||)

Where:
A = query embedding
B = stored embedding
· = dot product
|| || = L2 norm
```

## Performance Characteristics

```
Operation          | Time Complexity | Space Complexity
-------------------|-----------------|------------------
Embedding Gen      | O(n)           | O(768)
Vector Insert      | O(1)           | O(768)
Similarity Search  | O(n) or O(log n)| O(k)
Index Build        | O(n log n)     | O(n)

Where:
n = number of stored vectors
k = number of results (top-k)
```

## Scalability Considerations

```
Dataset Size       | Index Type    | Expected Performance
-------------------|---------------|---------------------
< 10K vectors      | No index      | < 100ms
10K - 100K         | IVFFlat       | < 500ms
100K - 1M          | IVFFlat       | < 1s
> 1M               | HNSW          | < 2s

Note: Times are approximate for top-5 search
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Environment Variables (.env)                             │
│     └─ Database credentials not hardcoded                    │
│                                                               │
│  2. Database Authentication                                  │
│     └─ PostgreSQL user/password authentication               │
│                                                               │
│  3. Input Validation                                         │
│     └─ Query parameter validation in API                     │
│                                                               │
│  4. SQL Injection Prevention                                 │
│     └─ Parameterized queries (psycopg2)                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Options

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Local      │     │    Docker    │     │    Cloud     │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ • Dev/Test   │     │ • Portable   │     │ • Production │
│ • Quick      │     │ • Isolated   │     │ • Scalable   │
│   Setup      │     │ • Consistent │     │ • Managed    │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Extension Points

```
1. Document Loaders
   └─ Add support for: DOCX, TXT, HTML, Markdown

2. Embedding Models
   └─ Swap models: OpenAI, Cohere, custom models

3. Vector Stores
   └─ Alternative: Pinecone, Weaviate, Milvus

4. Search Algorithms
   └─ Add: Hybrid search, reranking, filtering

5. API Features
   └─ Add: Authentication, rate limiting, caching
```
