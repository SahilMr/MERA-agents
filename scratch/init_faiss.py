import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
dataset = [
    {"atomic_query_id": "AQ_001", "text": "What is the status of my passport application?"},
    {"atomic_query_id": "AQ_002", "text": "How many days does it take to process a refund?"},
    {"atomic_query_id": "AQ_003", "text": "Who is the nodal officer for the education department?"},
    {"atomic_query_id": "AQ_004", "text": "Details regarding the new tax policy amendments."}
]
texts = [item["text"] for item in dataset]
query_ids = [item["atomic_query_id"] for item in dataset]
embeddings = model.encode(texts)
embedding_dim = embeddings.shape[1]
index_flat = faiss.IndexFlatL2(embedding_dim)
index = faiss.IndexIDMap(index_flat)
int_ids = np.arange(len(embeddings)).astype(np.int64)
id_mapping = {int(k): v for k, v in zip(int_ids, query_ids)}
index.add_with_ids(embeddings, int_ids)
faiss.write_index(index, "data/atomic_queries.index")
with open("data/id_mapping.pkl", "wb") as f:
    pickle.dump(id_mapping, f)
print("Dummy FAISS created.")
