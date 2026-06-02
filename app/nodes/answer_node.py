from app.llm.gemini import llm

async def answer_node(state):

    print("ANSWER NODE START")

    context = "\n\n".join([ d["document"] for d in state["reranked_docs"][:3] ])
    prompt = f"""
        아래 Context를 기반으로 질문에 답변해라.
        높은 우선도를 갖는 문서를 최우선으로 모든 Context를 고려하되,
        Score가 지나치게 낮은 Context는 제외한다.
        
        Context: {context}
        Question: {state["question"]} """

    result = await llm.ainvoke( prompt )

    return { "answer": result.content }