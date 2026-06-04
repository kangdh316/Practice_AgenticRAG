from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from app.graph import graph
from app.container import faiss_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    faiss_manager.load_memory()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/temp")
async def get_temp_vector_store():
    return faiss_manager.get_temp_documents()

@app.post("/chat")
async def chat(req: dict):

    result = await graph.ainvoke({
        "question": req["question"]
    })

    return result


@app.get("/api/status")
async def get_vector_store_status():
    """Raw/Approved 벡터 스토어 상태 조회"""
    return get_stats()


@app.post("/api/raw/search")
async def search_raw_documents(req: SearchRequest):
    """
    Raw 폴더의 문서 검색
    
    Args:
        query: 검색 쿼리
        top_k: 반환할 결과 개수
    """
    try:
        results = await retrieve_documents(
            question=req.query,
            top_k=req.top_k,
            from_approved=False
        )
        
        # index 정보를 포함하여 반환
        formatted_results = []
        for result in results:
            formatted_results.append({
                "index": result.get("index"),
                "document": result["document"],
                "score": result["score"],
                "metadata": result["metadata"]
            })
        
        return {
            "query": req.query,
            "results": formatted_results,
            "total": len(formatted_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/raw/approve")
async def approve_raw_documents(req: ApprovalRequest):
    """
    Raw 폴더의 지정된 문서들을 Approved로 이동
    
    Args:
        indices: 이동할 문서의 인덱스 배열
    """
    try:
        from app.services.vector.vector_store import documents_raw, metadatas_raw
        from app.llm.embedding import embeddings
        from app.services.vector.vector_store import add_embeddings
        
        if not req.indices:
            return {
                "status": "success",
                "moved_count": 0,
                "indices": []
            }
        
        # 정렬된 인덱스로 역순 처리
        sorted_indices = sorted(set(req.indices), reverse=True)
        
        moved_docs = []
        moved_metas = []
        moved_embeddings = []
        valid_indices = []
        
        for idx in sorted_indices:
            if 0 <= idx < len(documents_raw):
                # 문서 추출
                doc = documents_raw[idx]
                meta = metadatas_raw[idx]
                
                # 벡터 재생성
                vec = embeddings.embed_documents([doc])[0]
                
                moved_docs.insert(0, doc)
                moved_metas.insert(0, meta)
                moved_embeddings.insert(0, vec)
                valid_indices.insert(0, idx)
                
                # raw에서 제거
                del documents_raw[idx]
                del metadatas_raw[idx]
        
        # approved에 추가 (벡터 포함)
        if moved_docs:
            add_embeddings(
                moved_embeddings,
                moved_docs,
                moved_metas,
                to_approved=True
            )
        
        return {
            "status": "success",
            "moved_count": len(moved_docs),
            "indices": valid_indices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
