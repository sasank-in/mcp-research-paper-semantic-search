"""MCP server exposing the research-paper corpus as tools.

Run over stdio so MCP clients (Claude Desktop, Claude Code) can search and
query the indexed papers:

    python -m mcp_server.server
"""
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.mcpserver import MCPServer

from core import config, ingest, rag, vectorstore
from core.paths import resolve_pdf, safe_filename

mcp = MCPServer(
    name="research-papers",
    instructions=(
        "Search and question a local corpus of research papers indexed in "
        "pgvector. Use search_papers for raw passages, ask_papers for a "
        "synthesized cited answer."
    ),
    version="1.0.0",
)


@mcp.tool()
def search_papers(
    query: str, top_k: int = 5, filename: Optional[str] = None
) -> str:
    """Semantic search over the indexed research papers.

    Returns the most relevant passages with their source and similarity score.
    No LLM is involved, so this is the cheapest way to find raw evidence.

    Args:
        query: What to look for, in natural language.
        top_k: How many passages to return (default 5).
        filename: Restrict the search to a single paper, e.g. "attention.pdf".
    """
    results = rag.search(query, top_k=top_k, source=filename)
    if not results:
        return "No matching passages found. The corpus may be empty — use ingest_pdf first."

    lines = []
    for i, r in enumerate(results, 1):
        page = f", page {r['page']}" if r.get("page") is not None else ""
        lines.append(
            f"[{i}] {r['source']}{page} (similarity {r['similarity']})\n{r['content']}"
        )
    return "\n\n---\n\n".join(lines)


@mcp.tool()
def ask_papers(
    question: str, top_k: int = 5, filename: Optional[str] = None
) -> str:
    """Answer a question about the papers using RAG.

    Retrieves relevant passages and has an LLM synthesize a cited answer.
    Use search_papers instead when you want raw passages rather than prose.

    Args:
        question: The question to answer.
        top_k: How many passages to ground the answer in (default 5).
        filename: Restrict to a single paper, e.g. "attention.pdf".
    """
    result = rag.ask(
        question,
        session_id="mcp",
        top_k=top_k,
        source=filename,
        use_history=False,
    )
    sources = ", ".join(result["sources"]) or "none"
    return f"{result['answer']}\n\nSources: {sources}"


@mcp.tool()
def list_papers() -> str:
    """List every paper currently indexed and available to query."""
    indexed = vectorstore.list_sources()
    on_disk = sorted(
        {p.name for d in (config.PAPERS_DIR, config.UPLOADS_DIR)
         for p in Path(d).glob("*.pdf")}
        if any(Path(d).exists() for d in (config.PAPERS_DIR, config.UPLOADS_DIR))
        else set()
    )
    pending = [f for f in on_disk if f not in indexed]

    parts = []
    if indexed:
        parts.append("Indexed and queryable:\n" + "\n".join(f"  - {f}" for f in indexed))
    else:
        parts.append("No papers indexed yet.")
    if pending:
        parts.append(
            "On disk but not indexed (run ingest_pdf):\n"
            + "\n".join(f"  - {f}" for f in pending)
        )
    return "\n\n".join(parts)


@mcp.tool()
def ingest_pdf(filename: str) -> str:
    """Index a PDF so it becomes searchable.

    The file must already exist in the data/papers or data/uploads directory.
    Re-ingesting a paper replaces its previous chunks rather than duplicating.

    Args:
        filename: Name of the PDF, e.g. "attention.pdf".
    """
    path = resolve_pdf(filename)
    if path is None:
        return (
            f"'{safe_filename(filename)}' not found in {config.PAPERS_DIR} "
            f"or {config.UPLOADS_DIR}."
        )
    result = ingest.ingest_pdf(path)
    return (
        f"Indexed {result['filename']}: {result['pages']} pages, "
        f"{result['chunks']} chunks."
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
