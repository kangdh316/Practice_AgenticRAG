from tavily import TavilyClient
from app.config import (
    TAVILY_API_KEY,
    TRUSTED_DOMAINS
)

client = TavilyClient(
    api_key=TAVILY_API_KEY
)


async def search_web(query: str):

    response = client.search(
        query=query,
        include_domains=TRUSTED_DOMAINS,
        max_results=5
    )

    return response["results"]