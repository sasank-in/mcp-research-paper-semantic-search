from sentence_transformers import SentenceTransformer

def load_embedding_model():
    """Load the sentence transformer model for embeddings"""
    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    print("✓ Model loaded successfully")
    return model

def generate_embeddings(texts, model):
    """Generate embeddings for a list of texts"""
    if not texts:
        return []
    
    print(f"Generating embeddings for {len(texts)} texts...")
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

if __name__ == "__main__":
    model = load_embedding_model()
    
    # Test embedding
    test_text = "Deep learning for image recognition"
    embedding = model.encode(test_text)
    print(f"\nTest embedding shape: {embedding.shape}")
    print(f"Embedding dimensions: {len(embedding)}")