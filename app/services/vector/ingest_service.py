from app.services.chunk_service import (
    split_text
)

from app.llm.embedding import embeddings

from app.services.vector.vector_store import (
    add_embeddings
)


async def ingest_document(text):

    chunks = split_text(text)

    vectors = embeddings.embed_documents(
        chunks
    )

    add_embeddings(
        vectors,
        chunks
    )

    return chunks