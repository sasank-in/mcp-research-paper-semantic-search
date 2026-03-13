#!/usr/bin/env python3
"""
Quick start script for the Research Paper AI Assistant UI
"""
import os
import sys
from dotenv import load_dotenv

def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("ERROR: .env file not found!")
        print("   Please copy .env.example to .env and configure it")
        return False
    
    load_dotenv()
    
    # Check Groq API key
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key or groq_key == 'your_groq_api_key_here':
        print("ERROR: GROQ_API_KEY not configured!")
        print("   Please add your Groq API key to .env")
        print("   Get one at: https://console.groq.com")
        return False
    
    # Check database config
    db_name = os.getenv('DB_NAME')
    if not db_name:
        print("ERROR: Database not configured!")
        print("   Please configure database settings in .env")
        return False
    
    # Check frontend files
    if not os.path.exists('frontend/index.html'):
        print("ERROR: Frontend files not found!")
        print("   Please ensure frontend/ directory exists")
        return False
    
    print("SUCCESS: All requirements met!")
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n" + "="*60)
    print("Starting Research Paper AI Assistant")
    print("="*60)
    print("\nAccess the application at:")
    print("   Web UI:  http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\nFeatures:")
    print("   - Semantic Search - Search papers by meaning")
    print("   - AI Chat - Interactive assistant with RAG")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    import uvicorn
    from api.app import app
    
    uvicorn.run(app, host="127.0.0.1", port=8000)

def main():
    if not check_requirements():
        print("\nPlease fix the issues above and try again")
        sys.exit(1)
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\nServer stopped. Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
