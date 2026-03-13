import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.load_pdfs import load_pdfs
from ingestion.chunk_documents import split_documents
from ingestion.build_embeddings import load_embedding_model
from utils.db_connection import get_db_connection

load_dotenv()

class FileService:
    def __init__(self):
        self.papers_dir = "data/papers"
        self.uploads_dir = "data/uploads"
        
        # Create uploads directory if it doesn't exist
        os.makedirs(self.uploads_dir, exist_ok=True)
    
    def get_available_files(self):
        """Get list of all available PDF files"""
        files = []
        
        # Get files from papers directory
        if os.path.exists(self.papers_dir):
            for file in os.listdir(self.papers_dir):
                if file.endswith('.pdf'):
                    files.append({
                        'name': file,
                        'path': os.path.join(self.papers_dir, file),
                        'type': 'existing',
                        'size': os.path.getsize(os.path.join(self.papers_dir, file))
                    })
        
        # Get files from uploads directory
        if os.path.exists(self.uploads_dir):
            for file in os.listdir(self.uploads_dir):
                if file.endswith('.pdf'):
                    files.append({
                        'name': file,
                        'path': os.path.join(self.uploads_dir, file),
                        'type': 'uploaded',
                        'size': os.path.getsize(os.path.join(self.uploads_dir, file))
                    })
        
        return files
    
    async def save_uploaded_file(self, file):
        """Save uploaded PDF file"""
        try:
            # Generate safe filename
            filename = file.filename
            file_path = os.path.join(self.uploads_dir, filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                # Add timestamp to make unique
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"
                file_path = os.path.join(self.uploads_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            return {
                "message": "File uploaded successfully",
                "filename": filename,
                "path": file_path,
                "size": os.path.getsize(file_path)
            }
        
        except Exception as e:
            raise Exception(f"Error saving file: {str(e)}")
    
    def process_file(self, filename):
        """Process a single PDF file and add to database"""
        try:
            # Find the file
            file_path = None
            if os.path.exists(os.path.join(self.papers_dir, filename)):
                file_path = os.path.join(self.papers_dir, filename)
            elif os.path.exists(os.path.join(self.uploads_dir, filename)):
                file_path = os.path.join(self.uploads_dir, filename)
            else:
                raise Exception(f"File not found: {filename}")
            
            # Load and process the file
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise Exception("No content extracted from PDF")
            
            # Split into chunks
            from ingestion.chunk_documents import split_documents
            chunks = split_documents(documents)
            
            if not chunks:
                raise Exception("No chunks created from document")
            
            # Load embedding model
            from ingestion.build_embeddings import load_embedding_model
            model = load_embedding_model()
            
            # Store in database
            table_name = os.getenv('DB_TABLE', 'paper_chunks')
            conn = get_db_connection()
            cursor = conn.cursor()
            
            chunks_inserted = 0
            for chunk in chunks:
                try:
                    text = chunk.page_content
                    embedding = model.encode(text).tolist()
                    source = chunk.metadata.get("source", filename)
                    
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (content, embedding, source)
                        VALUES (%s, %s, %s)
                        """,
                        (text, embedding, source)
                    )
                    chunks_inserted += 1
                except Exception as e:
                    print(f"Error inserting chunk: {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "message": "File processed successfully",
                "filename": filename,
                "chunks_created": len(chunks),
                "chunks_inserted": chunks_inserted
            }
        
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def get_file_content(self, filename):
        """Get content from a specific file"""
        try:
            table_name = os.getenv('DB_TABLE', 'paper_chunks')
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all chunks from this file
            cursor.execute(
                f"""
                SELECT content FROM {table_name}
                WHERE source LIKE %s
                ORDER BY id
                """,
                (f"%{filename}%",)
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not results:
                return None
            
            # Combine chunks
            content = "\n\n".join([row[0] for row in results])
            return content
        
        except Exception as e:
            raise Exception(f"Error getting file content: {str(e)}")

# Global file service instance
file_service = FileService()
