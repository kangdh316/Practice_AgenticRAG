from app.llm.gemini import llm


async def extract_entities(text: str):

    prompt = f"""
    아래 문장에서 핵심 Entity를 추출해라.

    텍스트:
    {text}

    JSON 배열만 반환.
    """

    result = await llm.ainvoke(prompt)

    return result.content