from app.services.rerank.rerank_service import rerank_documents
from app.config import SIMILARITY_THRESHOLD
from app.llm.embedding import embeddings
from app.services.vector.vector_store import add_embeddings


async def web_rerank_node(state):
    """
    Rerank web search results to match RAG document format and scoring.
    Save results with score >= SIMILARITY_THRESHOLD to raw vector store.
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
    
    # threshold 이상의 결과를 raw에 저장
    approved_results = []
    for result in reranked:
        if result["score"] >= SIMILARITY_THRESHOLD:
            approved_results.append(result)
            
            # 문서를 임베딩하고 raw에 추가
            doc_embedding = embeddings.embed_documents([result["document"]])
            metadata = result.get("metadata", {})
            metadata["score"] = result["score"]
            metadata["source_type"] = "web_search"
            
            add_embeddings(
                doc_embedding,
                [result["document"]],
                [metadata],
                to_approved=False  # raw에 저장
            )
    
    return {
        "reranked_web_results": reranked,
        "web_results_approved": approved_results
    }
