from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.query_engine import search_similar_papers

app = FastAPI(
    title="Research Paper Semantic Search API",
    description="API for semantic search over research papers using vector embeddings",
    version="1.0.0"
)

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    content: str
    source: str
    similarity: float

@app.get("/")
def read_root():
    return {
        "message": "Research Paper Semantic Search API",
        "endpoints": {
            "/search": "POST - Search for similar papers",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/search", response_model=list[SearchResult])
def search(query: SearchQuery):
    """Search for papers similar to the query"""
    try:
        results = search_similar_papers(query.query, query.top_k)
        
        if not results:
            return []
        
        return [
            SearchResult(
                content=content,
                source=source,
                similarity=similarity
            )
            for content, source, similarity in results
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
