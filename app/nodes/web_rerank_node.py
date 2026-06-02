from app.services.rerank.rerank_service import rerank_documents


async def web_rerank_node(state):
    """
    Rerank web search results to match RAG document format and scoring.
    The web_search_node now returns results in {document, metadata, score} format,
    so we can directly pass them to the reranker while preserving metadata.
    """
    print("WEB RERANK NODE START")
    
    web_results = state.get("web_results", [])
    
    if not web_results:
        return {
            "reranked_web_results": []
        }
    
    # web_results are already in the correct format from web_search_node
    # {document, metadata, score}, but we need to rerank them
    reranked = await rerank_documents(
        state["question"],
        web_results,
        content_field="document"
    )
    
    return {
        "reranked_web_results": reranked
    }
