from app.llm.embedding import ( query_embeddings )
from app.services.vector.vector_store import ( similarity_search )

async def retrieve_documents( question: str, top_k=5, from_approved=True ):
    """
    문서 검색
    
    Args:
        question: 검색 쿼리
        top_k: 반환할 결과 개수
        from_approved: True면 approved에서 검색, False면 raw에서 검색
    """
    query_vector = ( query_embeddings.embed_query( question ) )
    results = similarity_search( query_vector, top_k=top_k, from_approved=from_approved )
    
    return results