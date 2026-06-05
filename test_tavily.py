import os
from tavily import TavilyClient

tavily_client = TavilyClient(api_key = os.getenv("TAVILY_API_KEY"))
response = tavily_client.search("python+dict+%EC%83%88+%EC%86%8D%EC%84%B1+%EC%B6%94%EA%B0%80")

print(response)