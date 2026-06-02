from app.services.rerank.rerank_service import rerank_documents


async def web_rerank_node(state):
    """
    Rerank web search results to match RAG document format and scoring.
    Converts web results structure to match reranker expectations.
    """
    print("WEB RERANK NODE START")
    
    web_results = state.get("web_results", [])
    
    if not web_results:
        return {
            "reranked_web_results": []
        }
    
    # Convert web results to rerank-compatible format
    web_docs = [
        {
            "document": result.get("content", ""),
            "metadata": {
                "url": result.get("url"),
                "title": result.get("title"),
                "source": result.get("source")
            }
        }
        for result in web_results
    ]
    
    reranked = await rerank_documents(
        state["question"],
        web_docs
    )
    
    return {
        "reranked_web_results": reranked
    }
