import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.getenv('DB_NAME', 'vector_db'),))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'vector_db')}")
            print(f"Database '{os.getenv('DB_NAME', 'vector_db')}' created successfully")
        else:
            print(f"Database '{os.getenv('DB_NAME', 'vector_db')}' already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def setup_vector_extension():
    """Enable pgvector extension and create table"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'vector_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        table_name = os.getenv('DB_TABLE', 'paper_chunks')
        
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("pgvector extension enabled")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(768),
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print(f"Table '{table_name}' created successfully")
        
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
            ON {table_name} 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        print("Vector index created successfully")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    create_database()
    setup_vector_extension()
