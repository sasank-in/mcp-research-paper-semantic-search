from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents, chunk_size=800, chunk_overlap=100):
    """Split documents into smaller chunks for embedding"""
    if not documents:
        print("No documents to split")
        return []
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks")
    
    return chunks

if __name__ == "__main__":
    from load_pdfs import load_pdfs
    
    docs = load_pdfs("data/papers")
    chunks = split_documents(docs)
    print(f"\nTotal chunks: {len(chunks)}")
    if chunks:
        print(f"Sample chunk length: {len(chunks[0].page_content)} characters")
