from typing import TypedDict, List


class AgentState(TypedDict):

    question: str

    retrieved_docs: List[dict]

    reranked_docs: List[dict]

    confidence_score: float

    web_results: List[str]

    crawled_docs: List[str]

    entities: List[str]

    graph_context: List[str]

    answer: str