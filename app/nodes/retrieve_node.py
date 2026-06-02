from app.llm.embedding import query_embeddings as embeddings
from app.services.vector_store import (
    similarity_search
)


async def retrieve_node(state):

    query_embedding = embeddings.embed_query(
        state["question"]
    )

    results = similarity_search(
        query_embedding,
        top_k=10
    )

    return {
        "retrieved_docs": results
    }