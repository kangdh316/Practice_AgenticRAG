from app.llm.gemini import llm
from app.container import faiss_manager

def _format_document_with_metadata(doc_item, is_web=False):
    """문서와 메타정보를 함께 포맷팅"""
    content = doc_item.get("document", "")
    metadata = doc_item.get("metadata", {})
    score = doc_item.get("score", 0)
    
    formatted_parts = []
    
    # 메타정보 헤더 구성
    metadata_info = []
    
    if metadata.get("title"):
        metadata_info.append(f"제목: {metadata['title']}")
    
    if metadata.get("author"):
        metadata_info.append(f"저자: {metadata['author']}")
    
    if metadata.get("year"):
        metadata_info.append(f"연도: {metadata['year']}")
    elif metadata.get("publish_date"):
        metadata_info.append(f"발행일: {metadata['publish_date']}")
    
    if metadata.get("source"):
        metadata_info.append(f"출처: {metadata['source']}")
    elif metadata.get("source_url"):
        metadata_info.append(f"출처: {metadata['source_url']}")
    elif metadata.get("domain"):
        metadata_info.append(f"도메인: {metadata['domain']}")
    
    if metadata.get("category"):
        metadata_info.append(f"카테고리: {metadata['category']}")
    
    if metadata.get("section"):
        metadata_info.append(f"섹션: {metadata['section']}")
    
    if is_web:
        if metadata.get("page_number"):
            metadata_info.append(f"페이지: {metadata['page_number']}")
        if metadata.get("description"):
            metadata_info.append(f"설명: {metadata['description']}")
    
    # 신뢰도 스코어 표시
    if score:
        metadata_info.append(f"신뢰도: {score:.3f}")
    
    if metadata_info:
        formatted_parts.append("[메타정보]")
        formatted_parts.extend(metadata_info)
        formatted_parts.append("")
    
    if metadata.get("description") and not is_web:
        formatted_parts.append(f"설명: {metadata['description']}")
        formatted_parts.append("")
    
    formatted_parts.append("[내용]")
    formatted_parts.append(content)
    
    return "\n".join(formatted_parts)


async def answer_node(state):

    print("ANSWER NODE START")

    if state.get("context_source") == "WEB":
        docs = state.get(
            "reranked_web_results",
            []
        )
        context = "\n\n---\n\n".join([
            _format_document_with_metadata(d, is_web=True)
            for d in docs[:3]
        ])
    else:
        docs = state.get(
            "reranked_docs",
            []
        ) 
        context = "\n\n---\n\n".join([
            _format_document_with_metadata(d, is_web=False)
            for d in docs[:3]
        ])

    prompt = f"""
        아래 Context를 기반으로 질문에 답변해라.
        높은 우선도를 갖는 문서를 최우선으로 모든 Context를 고려하되,
        Score가 지나치게 낮은 Context는 제외한다.
        메타정보(제목, 저자, 연도, 출처 등)를 참고하여 신뢰도 높은 정보를 우선으로 답변한다.
        
        Context:
        {context}
        
        Question: {state["question"]} """

    result = await llm.ainvoke( prompt )

    if state.get("context_source") == "WEB":
        faiss_manager.save_temp_documents(docs)

    return {
        "answer": result.content
    }