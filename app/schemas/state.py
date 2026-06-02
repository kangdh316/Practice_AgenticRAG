from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    retrieved_docs: list
    reranked_docs: list
    confidence_score: float
    web_results: list
    reranked_web_results: list
    context_source: str
    answer: str