from app.services.vector.retrieval_service import retrieve_documents

async def retrieve_node(state):

    print("RETRIEVE NODE START")
    
    docs = await retrieve_documents( state["question"] )

    return { "retrieved_docs": docs }  