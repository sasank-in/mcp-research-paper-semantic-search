# Usage Guide

## Command Line Interface

The system provides a unified CLI through `main.py`:

### 1. Setup Database

```bash
python main.py setup
```

This command:
- Creates the `vector_db` database
- Enables the pgvector extension
- Creates the `paper_chunks` table
- Creates a vector index for fast similarity search

### 2. Ingest Documents

```bash
python main.py ingest
```

This command:
- Loads all PDFs from `data/papers/`
- Splits documents into 800-character chunks with 100-character overlap
- Generates 768-dimensional embeddings using all-mpnet-base-v2
- Stores embeddings in PostgreSQL

Expected output:
```
[1/4] Loading PDF documents...
✓ Loaded: attention-1706.03762v7.pdf (15 pages)
...
[2/4] Splitting documents into chunks...
Split 89 documents into 456 chunks
[3/4] Loading embedding model...
✓ Model loaded successfully
[4/4] Generating embeddings and storing in database...
Processed 456/456 chunks
Pipeline completed successfully!
```

### 3. Search Papers

```bash
python main.py search "attention mechanism in neural networks"
```

Optional parameters:
```bash
python main.py search "deep learning" --top-k 10
```

Example output:
```
Result 1 (Similarity: 0.8542)
Source: data/papers/attention-1706.03762v7.pdf
Content: The attention mechanism allows the model to focus on...
```

### 4. Start API Server

```bash
python main.py api
```

Access:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Usage

### Search Endpoint

**POST** `/search`

Request body:
```json
{
  "query": "transformer architecture",
  "top_k": 5
}
```

Response:
```json
[
  {
    "content": "The Transformer model architecture...",
    "source": "data/papers/attention-1706.03762v7.pdf",
    "similarity": 0.8542
  }
]
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "convolutional neural networks for image classification",
    "top_k": 3
  }'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "attention mechanism",
        "top_k": 5
    }
)

results = response.json()
for result in results:
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Source: {result['source']}")
    print(f"Content: {result['content'][:200]}...\n")
```

## Testing

Run the test suite:

```bash
python test_system.py
```

This verifies:
- All imports work correctly
- PDFs can be loaded
- Documents can be chunked
- Embedding model loads
- Database connection works

## Adding New Papers

1. Place PDF files in `data/papers/`
2. Run ingestion:
```bash
python main.py ingest
```

The system will automatically process new papers and add them to the database.

## Database Management

### View stored chunks

```sql
SELECT COUNT(*) FROM paper_chunks;
```

### Clear all data

```sql
TRUNCATE TABLE paper_chunks;
```

### Check index status

```sql
SELECT * FROM pg_indexes WHERE tablename = 'paper_chunks';
```

## Troubleshooting

### "No module named 'sentence_transformers'"
```bash
pip install -r requirements.txt
```

### "could not connect to server"
Check if PostgreSQL is running:
```bash
# Linux/Mac
sudo systemctl status postgresql

# Windows
# Check Services app for PostgreSQL service
```

### "extension 'vector' does not exist"
Install pgvector extension (see SETUP.md)

### Slow search queries
Run ANALYZE to update statistics:
```sql
ANALYZE paper_chunks;
```

### Out of memory during ingestion
Reduce batch_size in `ingestion/pipeline.py`:
```python
batch_size = 25  # Default is 50
```

## Performance Tips

1. Use appropriate top_k values (5-10 is usually sufficient)
2. Keep chunk_size around 500-1000 characters
3. Run ANALYZE after large ingestions
4. Consider using IVFFlat index for datasets > 10,000 chunks
5. Monitor PostgreSQL memory settings for large datasets

## Example Queries

Good semantic search queries:
- "attention mechanism in neural networks"
- "convolutional architectures for image classification"
- "transformer models for natural language processing"
- "residual connections in deep learning"
- "variational autoencoders for generative modeling"

The system understands semantic meaning, so queries don't need exact keyword matches.
