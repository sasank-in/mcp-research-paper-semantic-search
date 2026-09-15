import shutil
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import config, ingest, rag, vectorstore
from core.paths import resolve_pdf, safe_filename, upload_path

app = FastAPI(
    title="Research Paper Semantic Search API",
    description=(
        "Semantic search and RAG chat over research papers, built on "
        "LangChain + pgvector. Also exposed as an MCP server."
    ),
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static = Path("frontend/static")
if _static.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static)), name="static")


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5
    selected_file: Optional[str] = None


class SearchResult(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    similarity: float


class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    top_k: int = 5
    selected_file: Optional[str] = None
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    model: str
    context_used: bool
    sources: list[str] = []


@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the web UI."""
    index = Path("frontend/index.html")
    if index.is_file():
        return index.read_text(encoding="utf-8")
    return (
        "<html><body><h1>Research Paper AI Assistant</h1>"
        '<p>Frontend not found. See <a href="/docs">/docs</a>.</p>'
        "</body></html>"
    )


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "3.0.0", "model": config.GROQ_MODEL}


@app.post("/api/search", response_model=list[SearchResult])
def search(query: SearchQuery):
    """Semantic search over indexed papers."""
    try:
        results = rag.search(
            query.query, top_k=query.top_k, source=query.selected_file
        )
        return [SearchResult(**r) for r in results]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Chat with the assistant, grounded in the papers when use_rag is set."""
    try:
        if request.use_rag:
            result = rag.ask(
                request.message,
                session_id=request.session_id,
                top_k=request.top_k,
                source=request.selected_file,
            )
            return ChatResponse(
                response=result["answer"],
                model=result["model"],
                context_used=result["context_used"],
                sources=result["sources"],
            )

        history = rag.get_history(request.session_id)
        answer = rag.get_llm().invoke(
            history.messages + [("human", request.message)]
        ).content
        history.add_user_message(request.message)
        history.add_ai_message(answer)
        return ChatResponse(
            response=answer,
            model=config.GROQ_MODEL,
            context_used=False,
            sources=[],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat/clear")
def clear_chat(session_id: str = "default"):
    """Clear one session's chat history."""
    rag.clear_history(session_id)
    return {"message": "Chat history cleared"}


@app.get("/api/chat/history")
def get_chat_history(session_id: str = "default"):
    """Return one session's chat history."""
    messages = rag.get_history(session_id).messages
    return {
        "history": [
            {"role": m.type, "content": m.content} for m in messages
        ]
    }


@app.get("/api/files")
def get_files():
    """List PDFs on disk, flagging which are indexed."""
    try:
        indexed = set(vectorstore.list_sources())
        files = []
        for directory, kind in (
            (config.PAPERS_DIR, "existing"),
            (config.UPLOADS_DIR, "uploaded"),
        ):
            folder = Path(directory)
            if not folder.is_dir():
                continue
            for pdf in sorted(folder.glob("*.pdf")):
                files.append(
                    {
                        "name": pdf.name,
                        "path": str(pdf),
                        "type": kind,
                        "size": pdf.stat().st_size,
                        "indexed": pdf.name in indexed,
                    }
                )
        return {"files": files}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF into the uploads directory."""
    try:
        dest = upload_path(file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "message": "File uploaded successfully",
            "filename": dest.name,
            "size": dest.stat().st_size,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/files/process/{filename}")
def process_file(filename: str):
    """Index an uploaded PDF so it becomes searchable."""
    try:
        safe_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    path = resolve_pdf(filename)
    if path is None:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    try:
        result = ingest.ingest_pdf(path)
        return {
            "message": "File processed successfully",
            "filename": result["filename"],
            "pages": result["pages"],
            "chunks_inserted": result["chunks"],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
