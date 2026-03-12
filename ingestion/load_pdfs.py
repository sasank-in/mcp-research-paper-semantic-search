from langchain_community.document_loaders import PyPDFLoader
import os

def load_pdfs(folder_path):
    """Load all PDF files from the specified folder"""
    documents = []
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist")
        return documents
    
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in '{folder_path}'")
        return documents
    
    print(f"Loading {len(pdf_files)} PDF files...")
    
    for file in pdf_files:
        try:
            file_path = os.path.join(folder_path, file)
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            documents.extend(docs)
            print(f"✓ Loaded: {file} ({len(docs)} pages)")
        except Exception as e:
            print(f"✗ Error loading {file}: {e}")
    
    return documents

if __name__ == "__main__":
    docs = load_pdfs("data/papers")
    print(f"\nTotal pages loaded: {len(docs)}")
