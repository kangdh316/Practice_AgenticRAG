from app.llm.embedding import ( document_embeddings )
from app.services.vector.vector_store import ( add_embeddings )

docs = [ """ 학교 태블릿 공동구매는 교육청 승인이 필요하다. """,
         """ 조달청 나라장터를 통해 학교 전자기기 공동구매가 가능하다. """,
         """ 교직원 법정 의무연수는 매년 정기적으로 수행해야 한다. """,
         """ 운용리스는 소유권 이전이 없는 임대 방식이다. """, ]

metadata = [ { "source": "교육청 지침" },
             { "source": "조달청" },
             { "source": "교육부" },
             { "source": "회계기준" } ]

vectors = ( document_embeddings.embed_documents( docs ) )

add_embeddings( vectors, docs, metadata )

print("=== INGEST COMPLETE ===")

#============= 테스트용 기능: 인덱스와 문서 저장 ==============

from app.services.vector.vector_store import ( save_index, save_documents )

save_index( "data/faiss/index.bin" )
save_documents( "data/faiss/documents.json" )