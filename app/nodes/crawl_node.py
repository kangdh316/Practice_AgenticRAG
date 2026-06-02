from app.services.web.crawl_service import (
    crawl_url
)

from app.services.vector.ingest_service import (
    ingest_document
)


async def crawl_node(state):

    docs = []

    for result in state["web_results"]:

        text = await crawl_url(
            result["url"]
        )

        if not text:
            continue

        docs.append(text)

        await ingest_document(text)

    return {
        "crawled_docs": docs
    }