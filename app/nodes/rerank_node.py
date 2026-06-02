from app.llm.reranker import reranker


async def rerank_node(state):

    docs = state["retrieved_docs"]

    pairs = [
        [
            state["question"],
            d["document"]
        ]
        for d in docs
    ]

    if not pairs:
        return {
            "reranked_docs": [],
            "confidence_score": 0
        }
    else:
        scores = reranker.predict(pairs)

        reranked = []

        for doc, score in zip(docs, scores):

            reranked.append({
                "document": doc["document"],
                "score": float(score)
            })

        reranked.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return {
            "reranked_docs": reranked[:5],
            "confidence_score": reranked[0]["score"]
        }