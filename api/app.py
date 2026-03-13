from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.query_engine import search_similar_papers
from api.chat_service import chat_service
from api.file_service import file_service

app = FastAPI(
    title="Research Paper Semantic Search API",
    description="API for semantic search over research papers using vector embeddings and AI chat assistant",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    content: str
    source: str
    similarity: float

class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    top_k: int = 3
    selected_file: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    context_used: bool
    sources: list[str] = []

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>Research Paper AI Assistant API</h1>
                <p>Frontend not found. API is running at:</p>
                <ul>
                    <li><a href="/docs">/docs</a> - API Documentation</li>
                    <li><a href="/health">/health</a> - Health Check</li>
                </ul>
            </body>
        </html>
        """

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}

@app.post("/api/search", response_model=list[SearchResult])
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

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Chat with AI assistant using RAG"""
    try:
        result = chat_service.chat_with_context(
            user_message=request.message,
            use_rag=request.use_rag,
            top_k=request.top_k,
            selected_file=request.selected_file
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/clear")
def clear_chat():
    """Clear chat history"""
    try:
        chat_service.clear_history()
        return {"message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history")
def get_chat_history():
    """Get chat history"""
    try:
        return {"history": chat_service.get_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
def get_files():
    """Get list of available PDF files"""
    try:
        files = file_service.get_available_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a new PDF file"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save file
        result = await file_service.save_uploaded_file(file)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/process/{filename}")
def process_file(filename: str):
    """Process uploaded file and add to database"""
    try:
        result = file_service.process_file(filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Research Paper AI Assistant...")
    print("Access the UI at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
