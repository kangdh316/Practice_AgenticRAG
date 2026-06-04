from app.services.vector.retrieval_service import retrieve_documents

async def retrieve_node(state):

    print("RETRIEVE NODE START")
    
    try:
        docs = await retrieve_documents( state["question"] )
    except Exception as e:
        print(f"Error occurred while retrieving documents: {e}")
        docs = []

    return { "retrieved_docs": docs }  