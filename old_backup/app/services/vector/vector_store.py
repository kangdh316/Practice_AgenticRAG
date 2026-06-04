import faiss
import numpy as np
from typing import Optional

# ========== APPROVED 저장소 ==========
# 실제 문서 저장
documents_approved = []

# metadata 저장
metadatas_approved = []

# FAISS index
index_approved = None

# ========== RAW 저장소 ==========
# 실제 문서 저장
documents_raw = []

# metadata 저장
metadatas_raw = []

# FAISS index
index_raw = None

# embedding dimension (공통)
embedding_dim = None

def initialize_index(dim: int):
    global index_approved
    global index_raw
    global embedding_dim

    embedding_dim = dim

    # cosine similarity용
    index_approved = faiss.IndexFlatIP(dim)
    index_raw = faiss.IndexFlatIP(dim)

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
    metadata_list=None,
    to_approved=True
):
    """
    임베딩을 벡터 스토어에 추가
    
    Args:
        embeddings: 임베딩 벡터 리스트
        docs: 문서 내용 리스트
        metadata_list: 메타데이터 리스트
        to_approved: True면 approved에 추가, False면 raw에 추가
    """

    global index_approved
    global index_raw
    global documents_approved
    global metadatas_approved
    global documents_raw
    global metadatas_raw
    global embedding_dim

    if not embeddings:
        return

    # 대상 선택
    if to_approved:
        documents = documents_approved
        metadatas = metadatas_approved
    else:
        documents = documents_raw
        metadatas = metadatas_raw

    if to_approved and index_approved is None:
        dim = len(embeddings[0])
        initialize_index(dim)
    elif not to_approved and index_raw is None:
        dim = len(embeddings[0])
        initialize_index(dim)
    
    # 인덱스 선택
    index = index_approved if to_approved else index_raw

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
            "metadata": metadatas[idx],
            "index": int(idx)
        })

    return results

#============= 테스트용 기능: 인덱스와 문서 저장/로드 ==============

from importlib.resources import path
import json

def save_index(path, approved=True):
    index = index_approved if approved else index_raw
    if index is None:
        return
    faiss.write_index(index, path)

def load_index(path, approved=True):
    global index_approved
    global index_raw
    if approved:
        index_approved = faiss.read_index(path)
    else:
        index_raw = faiss.read_index(path)

def save_documents(path, approved=True):
    documents = documents_approved if approved else documents_raw
    metadatas = metadatas_approved if approved else metadatas_raw
    
    data = []
    for doc, meta in zip( documents, metadatas ):
        data.append({ "document": doc, "metadata": meta })
    with open( path, "w", encoding="utf-8" ) as f:
        json.dump( data, f, ensure_ascii=False, indent=2 )

def load_documents(path, approved=True):
    global documents_approved
    global metadatas_approved
    global documents_raw
    global metadatas_raw
    
    with open( path, "r", encoding="utf-8" ) as f:
        data = json.load(f)
        
    docs = [ d["document"] for d in data ]
    metas = [ d["metadata"] for d in data ]
    
    if approved:
        documents_approved = docs
        metadatas_approved = metas
    else:
        documents_raw = docs
        metadatas_raw = metas

def get_stats():
    """전체 상태 조회"""
    return {
        "approved": {
            "count": len(documents_approved),
            "index_size": index_approved.ntotal if index_approved else 0
        },
        "raw": {
            "count": len(documents_raw),
            "index_size": index_raw.ntotal if index_raw else 0
        }
    }

def move_to_approved(raw_indices: list):
    """
    raw의 지정된 문서들을 approved로 이동
    
    Args:
        raw_indices: 옮길 문서의 인덱스 리스트
    """
    global documents_approved, metadatas_approved
    global documents_raw, metadatas_raw
    
    if not raw_indices:
        return 0
    
    # 정렬된 인덱스로 역순 처리 (삭제 시 인덱스 변동 방지)
    sorted_indices = sorted(set(raw_indices), reverse=True)
    
    moved_docs = []
    moved_metas = []
    valid_count = 0
    
    for idx in sorted_indices:
        if 0 <= idx < len(documents_raw):
            moved_docs.insert(0, documents_raw[idx])
            moved_metas.insert(0, metadatas_raw[idx])
            del documents_raw[idx]
            del metadatas_raw[idx]
            valid_count += 1
    
    # 이동된 문서들을 approved에 추가
    if moved_docs:
        documents_approved.extend(moved_docs)
        metadatas_approved.extend(moved_metas)
    
    # raw 인덱스 재생성 (벡터는 유지되므로, 메모리 상 데이터만 동기화)
    # 주의: 벡터 인덱스는 인덱스 순서대로만 유지되므로
    # 실제로 벡터를 다시 추가해야 하는 경우 별도 처리 필요
    
    return valid_count