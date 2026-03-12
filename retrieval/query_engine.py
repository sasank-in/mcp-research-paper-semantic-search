import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection import get_db_connection
from ingestion.build_embeddings import load_embedding_model
from dotenv import load_dotenv

load_dotenv()

def search_similar_papers(query, top_k=5):
    """Search for papers similar to the query"""
    try:
        table_name = os.getenv('DB_TABLE', 'paper_chunks')
        
        # Load model and generate query embedding
        model = load_embedding_model()
        query_embedding = model.encode(query).tolist()
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Perform similarity search using cosine distance
        cursor.execute(
            f"""
            SELECT content, source, 1 - (embedding <=> %s::vector) as similarity
            FROM {table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k)
        )
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
    
    except Exception as e:
        print(f"Error during search: {e}")
        return []

def display_results(results):
    """Display search results in a readable format"""
    if not results:
        print("No results found")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(results)} results:")
    print(f"{'='*80}\n")
    
    for i, (content, source, similarity) in enumerate(results, 1):
        print(f"Result {i} (Similarity: {similarity:.4f})")
        print(f"Source: {source}")
        print(f"Content: {content[:300]}...")
        print(f"{'-'*80}\n")

if __name__ == "__main__":
    # Example query
    query = "attention mechanism in neural networks"
    print(f"Searching for: '{query}'")
    
    results = search_similar_papers(query, top_k=5)
    display_results(results)
