import faiss
import numpy as np

# 실제 문서 저장
documents = []

# metadata 저장
metadatas = []

# FAISS index
index = None

# embedding dimension
embedding_dim = None

def initialize_index(dim: int):
    global index
    global embedding_dim

    embedding_dim = dim

    # cosine similarity용
    index = faiss.IndexFlatIP(dim)

def normalize_vectors(vectors):
    norms = np.linalg.norm(
        vectors,
        axis=1,
        keepdims=True
    )

    return vectors / norms

def add_embeddings(
    embeddings,
    docs,
    metadata_list=None
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

    vectors = normalize_vectors(vectors)

    index.add(vectors)

    documents.extend(docs)

    if metadata_list:
        metadatas.extend(metadata_list)
    else:
        metadatas.extend([ {} for _ in docs ])

def similarity_search(
    query_embedding,
    top_k=5
):
    # query_embedding(임베딩 모델에 의해 벡터화된 질의) 기준으로 유사한 문서 top_k개를 반환
    # index(메모리에 적재된 벡터 데이터)
    # > prod_index와 stage_index로 분리, Web 검색 결과를 stage_index에 적재
    # > stage_index에서 특정 index를 지정하면 그 index만 prod_index에 추가
    global index

    if index is None:

        return []

    if index.ntotal == 0:

        return []

    query_vector = np.array(
        [query_embedding],
        dtype="float32"
    )

    query_vector = normalize_vectors( query_vector )

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
            "score": float(dist),
            "metadata": metadatas[idx]
        })

    return results

#============= 테스트용 기능: 인덱스와 문서 저장/로드 ==============

from importlib.resources import path
import json

def save_index(path):
    global index
    if index is None:
        return
    faiss.write_index(index, path)

def load_index(path):
    global index
    index = faiss.read_index(path)

def save_documents(path):
    data = []
    for doc, meta in zip( documents, metadatas ):
        data.append({ "document": doc, "metadata": meta })
    with open( path, "w", encoding="utf-8" ) as f:
        json.dump( data, f, ensure_ascii=False, indent=2 )

def load_documents(path):
    global documents
    global metadatas
    
    with open( path, "r", encoding="utf-8" ) as f:
        data = json.load(f)
        
    documents = [ d["document"] for d in data ]
    metadatas = [ d["metadata"] for d in data ]