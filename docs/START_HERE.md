# 🎯 START HERE

Welcome! This guide will get you up and running in minutes.

## ⚡ Super Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database (make sure PostgreSQL is running)
python main.py setup

# 3. Process papers
python main.py ingest

# 4. Search!
python main.py search "attention mechanism"
```

That's it! You now have a working semantic search system.

## 📋 What You Need

Before starting, make sure you have:

- ✅ Python 3.8 or higher
- ✅ PostgreSQL 12 or higher (running)
- ✅ pgvector extension installed
- ✅ Internet connection (to download models)

## 🚦 Step-by-Step Guide

### Step 1: Check Prerequisites

```bash
# Check Python version
python --version  # Should be 3.8+

# Check PostgreSQL is running
psql --version
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- LangChain (document processing)
- Sentence Transformers (embeddings)
- FastAPI (API framework)
- psycopg2 (PostgreSQL driver)
- And more...

**Time**: 2-5 minutes

### Configuration

Edit `.env` with your PostgreSQL credentials:
```
DB_NAME=vector_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
DB_TABLE=paper_chunks
```

### Step 4: Setup Database

```bash
python main.py setup
```

This creates:
- Database named `vector_db`
- Table `paper_chunks` with vector column
- Vector index for fast search

**Time**: 10-30 seconds

### Step 5: Ingest Papers

```bash
python main.py ingest
```

This processes:
- 6 research papers from `data/papers/`
- Extracts text from PDFs
- Splits into chunks
- Generates embeddings
- Stores in database

**Time**: 2-5 minutes

### Step 6: Search Papers

```bash
python main.py search "attention mechanism in transformers"
```

You should see results like:

```
================================================================================
Found 5 results:
================================================================================

Result 1 (Similarity: 0.8542)
Source: data/papers/attention-1706.03762v7.pdf
Content: The attention mechanism allows the model to focus on...
```

### Step 7: Start API (Optional)

```bash
python main.py api
```

Then visit:
- http://localhost:8000 - API
- http://localhost:8000/docs - Interactive documentation

## ✅ Verify Everything Works

Run the test suite:

```bash
python test_system.py
```

All 5 tests should pass:
- ✓ All imports successful
- ✓ Loaded X pages from PDFs
- ✓ Created X chunks
- ✓ Model loaded, embedding shape: (768,)
- ✓ Connected to PostgreSQL

## 🎉 Success!

If you got here, your system is working! Here's what you can do next:

### Try Different Queries

```bash
python main.py search "convolutional neural networks"
python main.py search "transformer architecture"
python main.py search "residual connections"
python main.py search "variational autoencoders"
```

### Add Your Own Papers

1. Copy PDF files to `data/papers/`
2. Run: `python main.py ingest`
3. Search your new papers!

### Use the API

```bash
# Start the API
python main.py api

# In another terminal, test it
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "deep learning", "top_k": 5}'
```

## 🆘 Something Not Working?

### PostgreSQL Not Running

```bash
# Linux/Mac
sudo systemctl start postgresql

# macOS with Homebrew
brew services start postgresql

# Windows
# Start from Services app or pgAdmin
```

### pgvector Not Installed

See [SETUP.md](SETUP.md) for platform-specific installation instructions.

### Import Errors

```bash
pip install -r requirements.txt --upgrade
```

### Connection Refused

Check your `.env` file has correct credentials:
```bash
cat .env
```

### Still Stuck?

1. Check [SETUP.md](SETUP.md) for detailed instructions
2. Review [CHECKLIST.md](CHECKLIST.md) for verification steps
3. Read error messages carefully - they usually tell you what's wrong

## 📚 Learn More

Now that you're up and running, explore:

- **[README.md](README.md)** - Complete project overview
- **[USAGE.md](USAGE.md)** - Detailed usage examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - How it works
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation

## 🎯 Quick Reference

```bash
# Setup (one-time)
python main.py setup

# Ingest papers (when adding new PDFs)
python main.py ingest

# Search (anytime)
python main.py search "your query"

# Start API (optional)
python main.py api

# Run tests
python test_system.py
```

## 💡 Pro Tips

1. **Better Results**: Use descriptive queries like "attention mechanism in neural networks" instead of just "attention"

2. **More Results**: Add `--top-k 10` to get more results

3. **Check Database**: 
   ```bash
   psql -U postgres -d vector_db -c "SELECT COUNT(*) FROM paper_chunks"
   ```

4. **Monitor Performance**: First search is slower (loads model), subsequent searches are fast

5. **Add Papers Incrementally**: You can run `python main.py ingest` multiple times - it will add new papers without duplicating

## 🚀 You're Ready!

You now have a production-ready semantic search system. Start searching, add your papers, and explore the possibilities!

**Questions?** Check the documentation files or review the code - it's well-commented and easy to understand.

**Happy searching! 🔍**
