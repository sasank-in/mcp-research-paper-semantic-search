# Setup Guide

## Prerequisites

1. Python 3.8 or higher
2. PostgreSQL 12 or higher with pgvector extension

## Installation Steps

### 1. Install PostgreSQL and pgvector

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo apt install postgresql-server-dev-all
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### On macOS:
```bash
brew install postgresql
brew install pgvector
```

#### On Windows:
Download PostgreSQL from https://www.postgresql.org/download/windows/
Then install pgvector following: https://github.com/pgvector/pgvector#windows

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Edit the `.env` file with your PostgreSQL credentials:
```
DB_NAME=vector_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Setup Database

```bash
python main.py setup
```

This will:
- Create the database
- Enable pgvector extension
- Create the paper_chunks table
- Create vector index

### 5. Run Ingestion Pipeline

```bash
python main.py ingest
```

This will:
- Load PDFs from data/papers/
- Split documents into chunks
- Generate embeddings
- Store in PostgreSQL

### 6. Test Search

```bash
python main.py search "attention mechanism in neural networks"
```

### 7. Start API Server (Optional)

```bash
python main.py api
```

Access the API at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs

## Usage Examples

### Command Line Search
```bash
python main.py search "deep learning for computer vision" --top-k 10
```

### API Search
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer architecture", "top_k": 5}'
```

## Troubleshooting

### pgvector not found
Make sure pgvector is properly installed and PostgreSQL is restarted.

### Connection refused
Check if PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

### Out of memory
Reduce batch_size in ingestion/pipeline.py
