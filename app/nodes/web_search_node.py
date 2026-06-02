from app.services.web.search_service import (
    search_web
)


async def web_search_node(state):

    results = await search_web(
        state["question"]
    )

    return {
        "context_source": "WEB",
        "web_results": results
    }