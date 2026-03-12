#!/usr/bin/env python3
"""
Quick test script to verify the system is working
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from ingestion.load_pdfs import load_pdfs
        from ingestion.chunk_documents import split_documents
        from ingestion.build_embeddings import load_embedding_model
        from retrieval.query_engine import search_similar_papers
        from utils.db_connection import get_db_connection
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_pdf_loading():
    """Test PDF loading"""
    print("\nTesting PDF loading...")
    try:
        from ingestion.load_pdfs import load_pdfs
        docs = load_pdfs("data/papers")
        if docs:
            print(f"✓ Loaded {len(docs)} pages from PDFs")
            return True
        else:
            print("✗ No documents loaded")
            return False
    except Exception as e:
        print(f"✗ PDF loading error: {e}")
        return False

def test_chunking():
    """Test document chunking"""
    print("\nTesting document chunking...")
    try:
        from ingestion.load_pdfs import load_pdfs
        from ingestion.chunk_documents import split_documents
        docs = load_pdfs("data/papers")
        chunks = split_documents(docs)
        if chunks:
            print(f"✓ Created {len(chunks)} chunks")
            return True
        else:
            print("✗ No chunks created")
            return False
    except Exception as e:
        print(f"✗ Chunking error: {e}")
        return False

def test_embedding_model():
    """Test embedding model loading"""
    print("\nTesting embedding model...")
    try:
        from ingestion.build_embeddings import load_embedding_model
        model = load_embedding_model()
        test_text = "This is a test"
        embedding = model.encode(test_text)
        print(f"✓ Model loaded, embedding shape: {embedding.shape}")
        return True
    except Exception as e:
        print(f"✗ Embedding model error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    try:
        from utils.db_connection import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"✓ Connected to PostgreSQL")
        return True
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        print("  Make sure PostgreSQL is running and .env is configured")
        return False

def main():
    print("="*80)
    print("System Test Suite")
    print("="*80)
    
    tests = [
        test_imports,
        test_pdf_loading,
        test_chunking,
        test_embedding_model,
        test_database_connection
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*80)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*80)
    
    if all(results):
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python main.py setup")
        print("2. Run: python main.py ingest")
        print("3. Run: python main.py search 'your query'")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
