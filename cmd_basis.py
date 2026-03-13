#!/usr/bin/env python3
"""
Main entry point for the Research Paper Semantic Search System
"""
import argparse
import sys
import os

def setup_database():
    """Setup database and tables"""
    from utils.db_setup import create_database, setup_vector_extension
    print("Setting up database...")
    create_database()
    setup_vector_extension()
    print("\nDatabase setup complete!")

def run_ingestion():
    """Run the ingestion pipeline"""
    from ingestion.pipeline import run_ingestion_pipeline
    run_ingestion_pipeline()

def run_search(query, top_k=5):
    """Run a search query"""
    from retrieval.query_engine import search_similar_papers, display_results
    print(f"\nSearching for: '{query}'")
    results = search_similar_papers(query, top_k)
    display_results(results)

def start_api():
    """Start the FastAPI server"""
    import uvicorn
    from api.app import app
    print("Starting API server on http://localhost:8000")
    print("API documentation available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

def main():
    parser = argparse.ArgumentParser(
        description="Research Paper Semantic Search System"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    subparsers.add_parser("setup", help="Setup database and tables")
    
    # Ingest command
    subparsers.add_parser("ingest", help="Run ingestion pipeline")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for papers")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    
    # API command
    subparsers.add_parser("api", help="Start API server")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup_database()
    elif args.command == "ingest":
        run_ingestion()
    elif args.command == "search":
        run_search(args.query, args.top_k)
    elif args.command == "api":
        start_api()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
