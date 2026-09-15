"""Central configuration loaded from the environment."""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_NAME = os.getenv("DB_NAME", "vector_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# LangChain PGVector uses a collection name rather than a bare table.
COLLECTION_NAME = os.getenv("DB_COLLECTION", os.getenv("DB_TABLE", "paper_chunks"))

# psycopg3 driver URL, required by langchain-postgres
CONNECTION_STRING = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Models
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
)
EMBEDDING_DIM = 768

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Ingestion
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Paths
PAPERS_DIR = os.getenv("PAPERS_DIR", "data/papers")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "data/uploads")


def require_groq_key() -> str:
    """Return the Groq API key, raising a clear error if it is missing."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to .env "
            "(get one at https://console.groq.com)."
        )
    return GROQ_API_KEY
