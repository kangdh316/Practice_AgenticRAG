from app.services.rerank.reranker import ( reranker )

async def rerank_documents( question, docs ):
    if not docs:
        return []
    
    pairs = [ [question, d["document"]] for d in docs ]
    scores = reranker.predict( pairs )
    reranked = []

    for doc, score in zip( docs, scores ):
        reranked.append({ "document": doc["document"], "metadata": doc["metadata"], "score": float(score) })
        
    reranked.sort( key=lambda x: x["score"], reverse=True )

    return reranked