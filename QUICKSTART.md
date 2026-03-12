# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- 2GB free disk space

## Installation

### 1. Clone and Install

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Configure Database

Edit `.env` with your PostgreSQL credentials:
```
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. Setup

```bash
# Create database and tables
python main.py setup
```

### 4. Ingest Papers

```bash
# Process PDFs and create embeddings
python main.py ingest
```

This takes 2-5 minutes depending on the number of papers.

### 5. Search

```bash
# Search for papers
python main.py search "attention mechanism in transformers"
```

## That's it!

You now have a working semantic search system.

## Optional: Start API

```bash
python main.py api
```

Visit http://localhost:8000/docs for interactive API documentation.

## Next Steps

- Add more PDFs to `data/papers/` and run `python main.py ingest` again
- Read `USAGE.md` for detailed usage instructions
- Check `SETUP.md` for troubleshooting

## Common Issues

**"pgvector extension not found"**
- Install pgvector: https://github.com/pgvector/pgvector#installation

**"Connection refused"**
- Start PostgreSQL: `sudo systemctl start postgresql`

**"No PDFs found"**
- Ensure PDFs are in `data/papers/` directory

## Test Your Setup

```bash
python test_system.py
```

This runs a quick diagnostic to verify everything is working.
