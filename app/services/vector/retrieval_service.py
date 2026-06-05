from app.llm.embedding import ( query_embeddings )
from app.container import faiss_manager

async def retrieve_documents( question: str, top_k=5 ):
    query_vector = ( query_embeddings(question) )
    results = faiss_manager.similarity_search( query_vector, top_k=top_k )
    
    return results