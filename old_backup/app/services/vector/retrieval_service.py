from app.llm.embedding import ( query_embeddings )
from app.services.vector.vector_store import ( similarity_search )

async def retrieve_documents( question: str, top_k=5 ):
    query_vector = ( query_embeddings.embed_query( question ) )
    results = similarity_search( query_vector, top_k=top_k )
    
    return results