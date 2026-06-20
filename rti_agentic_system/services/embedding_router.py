from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load local model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Dimension of all-MiniLM-L6-v2 is 384
dimension = 384
index = faiss.IndexFlatL2(dimension)

knowledge_base_texts = []

def add_to_index(texts: list[str]):
    global knowledge_base_texts
    if not texts:
        return
    embeddings = embedding_model.encode(texts)
    index.add(np.array(embeddings).astype('float32'))
    knowledge_base_texts.extend(texts)

def search_index(query: str, k: int = 3) -> list[str]:
    if index.ntotal == 0:
        return []
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding).astype('float32'), k)
    
    results = []
    for idx in indices[0]:
        if idx != -1 and idx < len(knowledge_base_texts):
            results.append(knowledge_base_texts[idx])
    return results
