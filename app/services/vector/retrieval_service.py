from app.llm.embedding import ( query_embeddings )
from app.container import faiss_manager

async def retrieve_documents( question: str, top_k=5, from_approved=True ):
    """
    문서 검색
    
    Args:
        question: 검색 쿼리
        top_k: 반환할 결과 개수
        from_approved: True면 approved에서 검색, False면 raw에서 검색
    """
    query_vector = ( query_embeddings.embed_query( question ) )
    results = faiss_manager.similarity_search( query_vector, top_k=top_k )
    
    return results