import trafilatura


async def crawl(url: str):

    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return None

    text = trafilatura.extract(downloaded)

    return text