from tavily import TavilyClient
from app.config import (
    TAVILY_API_KEY,
    TRUSTED_DOMAINS
)

client = TavilyClient(
    api_key=TAVILY_API_KEY
)


def _extract_metadata_from_web_result(result):
    """Tavily 검색 결과에서 메타정보 추출"""
    metadata = {
        "title": result.get("title", ""),
        "source_url": result.get("url", ""),
        "source": result.get("source", ""),
        "description": result.get("description", ""),
        "domain": result.get("url", "").split("/")[2] if result.get("url") else "",
        "category": "web_search"
    }
    return metadata


async def search_web(query: str):

    response = client.search(
        query=query,
        include_domains=TRUSTED_DOMAINS,
        max_results=5
    )

    # 메타정보를 포함하여 결과 구성
    results_with_metadata = []
    for result in response.get("results", []):
        results_with_metadata.append({
            "document": result.get("content", ""),
            "metadata": _extract_metadata_from_web_result(result),
            "score": result.get("score", 0)
        })

    return results_with_metadata