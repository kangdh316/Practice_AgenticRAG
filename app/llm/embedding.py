import os

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)

document_embeddings = (
    GoogleGenerativeAIEmbeddings(
        google_api_key=os.getenv("GEMINI_API_KEY"),
        model="models/gemini-embedding-001",
        task_type="retrieval_document"
    )
)

query_embeddings = (
    GoogleGenerativeAIEmbeddings(
        google_api_key=os.getenv("GEMINI_API_KEY"),
        model="models/gemini-embedding-001",
        task_type="retrieval_query"
    )
)