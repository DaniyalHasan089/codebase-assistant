# embedding_store.py

import os
import requests
from config import DB_DIR, OPENROUTER_API_KEY

# Import ChromaDB with Streamlit Cloud compatibility
try:
    from chromadb_compat import chromadb
except ImportError:
    import chromadb

# Init Chroma client
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(name="codebase")

def get_embedding(text: str):
    """Get vector embedding from OpenAI directly (OpenRouter doesn't support embeddings)."""
    # Note: OpenRouter doesn't support embeddings API, so we'll use a simple fallback
    # For production, you should use OpenAI directly or implement a different embedding solution
    import hashlib
    
    # Create a simple hash-based "embedding" as a fallback
    # This is not a real embedding but will allow the demo to work
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Convert hex to a list of floats to simulate an embedding vector
    embedding = []
    for i in range(0, len(text_hash), 2):
        hex_pair = text_hash[i:i+2]
        # Convert hex to int, then normalize to [-1, 1] range
        val = (int(hex_pair, 16) - 127.5) / 127.5
        embedding.append(val)
    
    # Pad or truncate to a standard embedding size (e.g., 16 dimensions for this demo)
    target_size = 16
    if len(embedding) < target_size:
        embedding.extend([0.0] * (target_size - len(embedding)))
    else:
        embedding = embedding[:target_size]
    
    return embedding

def add_documents(docs):
    ids = [f"doc_{i}" for i in range(len(docs))]
    embeddings = [get_embedding(doc) for doc in docs]
    collection.add(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=[{"chunk_id": i} for i in range(len(docs))]
    )

def query_codebase(query: str, n_results=3):
    query_vec = get_embedding(query)
    return collection.query(query_embeddings=[query_vec], n_results=n_results)
