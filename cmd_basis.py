#!/usr/bin/env python3
"""Command-line entry point for the Research Paper Semantic Search system."""
import argparse
import sys


def cmd_setup(args):
    """Create the pgvector extension and LangChain collection tables."""
    from core.vectorstore import get_vectorstore
    from core import config
    import sqlalchemy

    engine = sqlalchemy.create_engine(config.CONNECTION_STRING)
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector"))
    engine.dispose()
    print("pgvector extension enabled")

    # Instantiating the store creates its tables.
    get_vectorstore()
    print(f"Collection '{config.COLLECTION_NAME}' ready")
    print("\nSetup complete.")


def cmd_ingest(args):
    """Index PDFs into the vector store."""
    from core.ingest import ingest_directory, ingest_pdf

    if args.file:
        result = ingest_pdf(args.file)
        print(
            f"Indexed {result['filename']}: "
            f"{result['pages']} pages, {result['chunks']} chunks"
        )
        return

    print(f"Ingesting PDFs from {args.folder}...")
    summary = ingest_directory(args.folder)
    print(
        f"\nDone: {len(summary['processed'])} file(s), "
        f"{summary['total_chunks']} chunks"
    )
    if summary["failed"]:
        print(f"Failed: {len(summary['failed'])}")
        for f in summary["failed"]:
            print(f"  {f['filename']}: {f['error']}")


def cmd_search(args):
    """Semantic search, no LLM."""
    from core.rag import search

    results = search(args.query, top_k=args.top_k, source=args.file)
    if not results:
        print("No results found.")
        return

    print(f"\nFound {len(results)} result(s) for {args.query!r}:\n")
    for i, r in enumerate(results, 1):
        page = f" page {r['page']}" if r.get("page") is not None else ""
        print(f"[{i}] {r['source']}{page}  (similarity {r['similarity']})")
        print(f"    {r['content'][:300]}\n")


def cmd_ask(args):
    """Ask a question answered over the papers with citations."""
    from core.rag import ask

    result = ask(args.question, top_k=args.top_k, source=args.file, use_history=False)
    print(f"\n{result['answer']}\n")
    print(f"Sources: {', '.join(result['sources']) or 'none'}")


def cmd_list(args):
    """List indexed papers."""
    from core.vectorstore import list_sources

    sources = list_sources()
    if not sources:
        print("No papers indexed. Run: python cmd_basis.py ingest")
        return
    print(f"{len(sources)} paper(s) indexed:")
    for s in sources:
        print(f"  - {s}")


def cmd_api(args):
    """Start the web UI and REST API."""
    import uvicorn

    print(f"Starting API on http://{args.host}:{args.port}")
    print(f"  Web UI:   http://{args.host}:{args.port}/")
    print(f"  API docs: http://{args.host}:{args.port}/docs")
    uvicorn.run("api.app:app", host=args.host, port=args.port)


def cmd_mcp(args):
    """Run the MCP server over stdio."""
    from mcp_server.server import main

    main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Research Paper Semantic Search (LangChain + pgvector + MCP)"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("setup", help="Create the pgvector extension and tables")

    p = sub.add_parser("ingest", help="Index PDFs into the vector store")
    p.add_argument("--folder", default=None, help="Folder of PDFs (default data/papers)")
    p.add_argument("--file", default=None, help="Index a single PDF instead")

    p = sub.add_parser("search", help="Semantic search over indexed papers")
    p.add_argument("query")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--file", default=None, help="Restrict to one paper")

    p = sub.add_parser("ask", help="Ask a question answered with citations")
    p.add_argument("question")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--file", default=None, help="Restrict to one paper")

    sub.add_parser("list", help="List indexed papers")

    p = sub.add_parser("api", help="Start the web UI and REST API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)

    sub.add_parser("mcp", help="Run the MCP server over stdio")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "setup": cmd_setup,
        "ingest": cmd_ingest,
        "search": cmd_search,
        "ask": cmd_ask,
        "list": cmd_list,
        "api": cmd_api,
        "mcp": cmd_mcp,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
