from langgraph.graph import (
    StateGraph,
    END
)

from app.schemas.state import AgentState

from app.nodes.retrieve_node import retrieve_node
from app.nodes.rerank_node import rerank_node
from app.nodes.answer_node import answer_node
from app.nodes.web_search_node import web_search_node
from app.nodes.threshold_node import threshold_router

builder = StateGraph(AgentState)

builder.add_node(
    "retrieve",
    retrieve_node
)

builder.add_node(
    "rerank",
    rerank_node
)

builder.add_node(
    "RAG_answer",
    answer_node
)

builder.add_node(
    "web_search",
    web_search_node
)

builder.set_entry_point("retrieve")

builder.add_edge(
    "retrieve",
    "rerank"
)

builder.add_conditional_edges(
    "rerank",
    threshold_router,
    {
        "answer": "RAG_answer",
        "web_search": "web_search"
    }
)

builder.add_edge(
    "RAG_answer",
    END
)

builder.add_edge(
    "web_search",
    "RAG_answer"
)

graph = builder.compile()