from app.services.rerank.rerank_service import ( rerank_documents )

async def rerank_node(state):

    print("RERANK NODE START")
    
    reranked = await rerank_documents( state["question"], state["retrieved_docs"] )
    
    return { 
             "context_source": "RAG",
             "reranked_docs": reranked,
             "confidence_score": ( reranked[0]["score"]
                                   if reranked
                                   else 0.0 )
            }