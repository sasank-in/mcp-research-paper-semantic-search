#!/usr/bin/env python3
"""Start the Research Paper AI Assistant web UI."""
import os
import sys


def check_requirements() -> bool:
    """Verify configuration before starting the server."""
    if not os.path.exists(".env"):
        print("ERROR: .env file not found.")
        print("  Copy .env.example to .env and configure it.")
        return False

    from core import config

    if not config.GROQ_API_KEY or config.GROQ_API_KEY == "your_api_key_here":
        print("ERROR: GROQ_API_KEY is not configured in .env")
        print("  Get a key at https://console.groq.com")
        return False

    if not os.path.exists("frontend/index.html"):
        print("ERROR: frontend/index.html not found.")
        return False

    # Confirm the database is reachable before binding the port.
    try:
        import sqlalchemy

        engine = sqlalchemy.create_engine(config.CONNECTION_STRING)
        with engine.connect():
            pass
        engine.dispose()
    except Exception as exc:
        print(f"ERROR: cannot connect to PostgreSQL: {exc}")
        print("  Check the DB_* settings in .env, then run:")
        print("    python cmd_basis.py setup")
        return False

    return True


def main():
    if not check_requirements():
        sys.exit(1)

    from core import config
    from core.vectorstore import list_sources

    papers = list_sources()

    print("=" * 60)
    print("Research Paper AI Assistant")
    print("=" * 60)
    print(f"  Web UI:   http://127.0.0.1:8000/")
    print(f"  API docs: http://127.0.0.1:8000/docs")
    print(f"  Model:    {config.GROQ_MODEL}")
    print(f"  Papers:   {len(papers)} indexed")
    if not papers:
        print("            (add PDFs to data/papers, then: "
              "python cmd_basis.py ingest)")
    print("\nPress Ctrl+C to stop.")
    print("=" * 60 + "\n")

    import uvicorn

    try:
        uvicorn.run("api.app:app", host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
