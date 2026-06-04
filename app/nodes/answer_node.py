from app.llm.gemini import llm
from app.container import faiss_manager

async def answer_node(state):

    print("ANSWER NODE START")

    if state.get("context_source") == "WEB":
        docs = state.get(
            "web_results",
            []
        )
        context = "\n\n".join([

            d["content"]

            for d in docs[:3]
        ])
    else :
        docs = state.get(
            "reranked_docs",
            []
        ) 
        context = "\n\n".join([

            d["document"]

            for d in docs[:3]
        ])


    prompt = f"""
        아래 Context를 기반으로 질문에 답변해라.
        높은 우선도를 갖는 문서를 최우선으로 모든 Context를 고려하되,
        Score가 지나치게 낮은 Context는 제외한다.
        
        Context: {context}
        Question: {state["question"]} """

    result = await llm.ainvoke( prompt )

    if state.get("context_source") == "WEB":
        faiss_manager.save_temp_documents(docs)

    return {
        "answer": result.content
    }