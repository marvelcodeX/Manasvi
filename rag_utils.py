import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load and chunk the knowledge base document
def load_knowledge_base(file_path, chunk_size=100):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Break into small overlapping chunks
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    embeddings = embedding_model.encode(chunks)

    # Create FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))

    return {
        "chunks": chunks,
        "index": index,
        "embeddings": embeddings
    }

# Search for relevant text from the knowledge base
def query_knowledge(user_query, kb_data, top_k=1):
    query_embedding = embedding_model.encode([user_query])
    distances, indices = kb_data["index"].search(np.array(query_embedding), top_k)
    results = [kb_data["chunks"][i] for i in indices[0]]
    return "\n".join(results)
