from app.services.rerank.reranker import ( reranker )

async def rerank_documents( question, docs, content_field="document" ):
    if not docs:
        return []
    
    pairs = [ [question, d[content_field]] for d in docs ]
    scores = reranker.predict( pairs )
    reranked = []

    for doc, score in zip( docs, scores ):
        reranked.append({ "document": doc[content_field], "metadata": doc.get("metadata", {}), "score": float(score) })
        
    reranked.sort( key=lambda x: x["score"], reverse=True )

    return reranked