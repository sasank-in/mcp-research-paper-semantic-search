# Project Structure

```
.
├── api/
│   └── app.py                 # FastAPI application for REST API
│
├── data/
│   └── papers/                 # PDF research papers (6 papers included)
│       ├── attention-1706.03762v7.pdf
│       ├── auto-encoding-1312.6114v11.pdf
│       ├── bert-N19-1423.pdf
│       ├── imagenet-Paper.pdf
│       ├── resnet-1512.03385v1.pdf
│       └── yolo-1506.02640v5.pdf
│
├── ingestion/
│   ├── load_pdfs.py            # PDF loading functionality
│   ├── chunk_documents.py      # Document chunking logic
│   ├── build_embeddings.py     # Embedding generation
│   └── pipeline.py             # Complete ingestion pipeline
│
├── retrieval/
│   └── query_engine.py         # Semantic search functionality
│
├── utils/
│   ├── db_setup.py             # Database initialization
│   └── db_connection.py        # Database connection helper
│
├── main.py                     # Main CLI entry point
├── test_system.py              # System test suite
│
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── .env.example                # Example environment file
├── .gitignore                  # Git ignore rules
│
├── Readme.md                   # Project overview and architecture
├── QUICKSTART.md               # 5-minute setup guide
├── SETUP.md                    # Detailed installation instructions
├── USAGE.md                    # Comprehensive usage guide
└── PROJECT_STRUCTURE.md        # This file
```

## Module Descriptions

### Core Modules

**main.py**
- Unified CLI interface
- Commands: setup, ingest, search, api
- Entry point for all operations

**api/app.py**
- FastAPI REST API
- Endpoints: /, /health, /search
- Interactive documentation at /docs

### Ingestion Pipeline

**ingestion/load_pdfs.py**
- Loads PDF files from data/papers/
- Uses PyPDFLoader from langchain
- Returns list of Document objects

**ingestion/chunk_documents.py**
- Splits documents into smaller chunks
- Uses RecursiveCharacterTextSplitter
- Default: 800 chars with 100 char overlap

**ingestion/build_embeddings.py**
- Loads sentence-transformers model
- Model: all-mpnet-base-v2 (768 dimensions)
- Generates vector embeddings from text

**ingestion/pipeline.py**
- Orchestrates complete ingestion process
- Batch processing for efficiency
- Stores embeddings in PostgreSQL

### Retrieval

**retrieval/query_engine.py**
- Semantic similarity search
- Uses cosine distance for ranking
- Returns top-k most similar chunks

### Utilities

**utils/db_setup.py**
- Creates database and tables
- Enables pgvector extension
- Creates vector indexes

**utils/db_connection.py**
- Database connection helper
- Loads credentials from .env
- Reusable connection function

### Testing

**test_system.py**
- Verifies all components work
- Tests imports, PDF loading, chunking, embeddings, database
- Run before first use

## Data Flow

```
PDFs → Load → Chunk → Embed → Store → Search
                                  ↓
                            PostgreSQL + pgvector
```

## Database Schema

```sql
CREATE TABLE paper_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(768),
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX paper_chunks_embedding_idx 
ON paper_chunks 
USING ivfflat (embedding vector_cosine_ops);
```

## Key Technologies

- **Python 3.8+**: Core language
- **LangChain**: Document processing
- **Sentence Transformers**: Embedding generation
- **PostgreSQL**: Database
- **pgvector**: Vector similarity search
- **FastAPI**: REST API framework
- **PyPDF**: PDF text extraction

## Configuration

All configuration is in `.env`:
- Database credentials
- Connection parameters
- No hardcoded secrets

## Commands Reference

```bash
# Setup
python main.py setup

# Ingest papers
python main.py ingest

# Search
python main.py search "query" --top-k 5

# Start API
python main.py api

# Test system
python test_system.py
```

## Extension Points

Want to extend the system? Here are the key areas:

1. **Add new document types**: Modify `ingestion/load_pdfs.py`
2. **Change embedding model**: Update `ingestion/build_embeddings.py`
3. **Adjust chunking**: Modify `ingestion/chunk_documents.py`
4. **Add API endpoints**: Extend `api/main.py`
5. **Custom search logic**: Modify `retrieval/query_engine.py`

## Performance Considerations

- Batch size: 50 chunks per database commit
- Chunk size: 800 characters (adjustable)
- Embedding dimensions: 768 (model-dependent)
- Index type: IVFFlat (good for 10K-1M vectors)
- Search complexity: O(n) without index, O(log n) with index
