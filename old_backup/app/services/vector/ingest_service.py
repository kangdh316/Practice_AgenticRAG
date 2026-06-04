from app.services.chunk_service import (
    split_text
)

from app.llm.embedding import embeddings

from app.services.vector.vector_store import (
    add_embeddings
)


async def ingest_document(text, metadata=None, to_approved=True):
    """
    문서를 임베딩하여 벡터 저장소에 추가
    
    Args:
        text: 문서 내용
        metadata: 각 청크에 적용할 메타정보 (딕셔너리 또는 딕셔너리 리스트)
        to_approved: True면 approved에 저장, False면 raw에 저장
    """

    chunks = split_text(text)

    vectors = embeddings.embed_documents(
        chunks
    )

    # 메타정보 처리
    metadata_list = None
    if metadata:
        if isinstance(metadata, dict):
            # 같은 메타정보를 모든 청크에 적용
            metadata_list = [metadata.copy() for _ in chunks]
        elif isinstance(metadata, list):
            # 청크별 개별 메타정보
            metadata_list = metadata

    add_embeddings(
        vectors,
        chunks,
        metadata_list,
        to_approved=to_approved
    )

    return chunks