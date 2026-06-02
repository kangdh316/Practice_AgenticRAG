from app.llm.gemini import llm


async def answer_node(state):

    docs = state.get(
        "reranked_docs",
        []
    )

    context = "\n\n".join([
        d["document"]
        for d in docs
    ])

    prompt = f"""
    아래 Context를 기반으로 답변해라.

    Context:
    {context}

    Question:
    {state["question"]}
    """

    result = await llm.ainvoke(prompt)

    return {
        "answer": result.content
    }