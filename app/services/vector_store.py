import faiss
import numpy as np

documents = []

index = None

def initialize_index(dim: int):

    global index
    global embedding_dim

    embedding_dim = dim

    index = faiss.IndexFlatL2(dim)
    
def add_embeddings(
    embeddings,
    docs
):

    global index

    if not embeddings:
        return

    if index is None:

        dim = len(embeddings[0])

        initialize_index(dim)

    vectors = np.array(
        embeddings,
        dtype="float32"
    )

    index.add(vectors)

    documents.extend(docs)
def similarity_search(
    query_embedding,
    top_k=5
):

    global index

    if index is None:

        return []

    if index.ntotal == 0:

        return []

    query_vector = np.array(
        [query_embedding],
        dtype="float32"
    )

    distances, indices = index.search(
        query_vector,
        top_k
    )

    results = []

    for idx, dist in zip(
        indices[0],
        distances[0]
    ):

        if idx < 0:
            continue

        if idx >= len(documents):
            continue

        results.append({
            "document": documents[idx],
            "score": float(dist)
        })

    return results