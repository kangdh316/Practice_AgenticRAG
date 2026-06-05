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
        #include_domains=TRUSTED_DOMAINS,
        include_images=False,
        include_favicon=False,
        include_usage=False,
        max_results=10
    )

    return response["results"]