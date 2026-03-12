import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.load_pdfs import load_pdfs
from ingestion.chunk_documents import split_documents
from ingestion.build_embeddings import load_embedding_model
from utils.db_connection import get_db_connection
from dotenv import load_dotenv

load_dotenv()

def run_ingestion_pipeline(pdf_folder="data/papers"):
    """Run the complete ingestion pipeline"""
    print("="*80)
    print("Starting Ingestion Pipeline")
    print("="*80)
    
    table_name = os.getenv('DB_TABLE', 'paper_chunks')
    
    # Step 1: Load PDFs
    print("\n[1/4] Loading PDF documents...")
    documents = load_pdfs(pdf_folder)
    
    if not documents:
        print("No documents loaded. Exiting.")
        return
    
    # Step 2: Split into chunks
    print("\n[2/4] Splitting documents into chunks...")
    chunks = split_documents(documents)
    
    if not chunks:
        print("No chunks created. Exiting.")
        return
    
    # Step 3: Load embedding model
    print("\n[3/4] Loading embedding model...")
    model = load_embedding_model()
    
    # Step 4: Store embeddings in database
    print(f"\n[4/4] Generating embeddings and storing in database (table: {table_name})...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    batch_size = 50
    total_inserted = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        for chunk in batch:
            try:
                text = chunk.page_content
                embedding = model.encode(text).tolist()
                source = chunk.metadata.get("source", "unknown")
                
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} (content, embedding, source)
                    VALUES (%s, %s, %s)
                    """,
                    (text, embedding, source)
                )
                total_inserted += 1
            except Exception as e:
                print(f"Error inserting chunk: {e}")
        
        conn.commit()
        print(f"Processed {min(i+batch_size, len(chunks))}/{len(chunks)} chunks")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print(f"Pipeline completed successfully!")
    print(f"Total chunks inserted: {total_inserted}")
    print("="*80)

if __name__ == "__main__":
    run_ingestion_pipeline()
