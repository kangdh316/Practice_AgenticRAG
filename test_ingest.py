from app.llm.embedding import ( document_embeddings )
from app.services.vector.vector_store import ( add_embeddings )

docs = [ """ 학교 태블릿 공동구매는 교육청 승인이 필요하다. """,
         """ 조달청 나라장터를 통해 학교 전자기기 공동구매가 가능하다. """,
         """ 교직원 법정 의무연수는 매년 정기적으로 수행해야 한다. """,
         """ 운용리스는 소유권 이전이 없는 임대 방식이다. """, ]

# 확장된 메타정보 구조
metadata = [ 
    {
        "source": "교육청 지침",
        "title": "학교 태블릿 공동구매 승인 절차",
        "author": "교육청 학생복지과",
        "year": 2024,
        "category": "교육 정책",
        "section": "학용품 구매",
        "tags": ["태블릿", "공동구매", "승인"]
    },
    {
        "source": "조달청",
        "title": "나라장터를 이용한 학교 전자기기 공동구매 가이드",
        "author": "조달청",
        "year": 2024,
        "source_url": "https://www.g2b.go.kr/",
        "category": "조달 가이드",
        "section": "전자기기",
        "tags": ["나라장터", "전자기기", "공동구매"]
    },
    {
        "source": "교육부",
        "title": "교직원 법정 의무연수 운영 규정",
        "author": "교육부 인사담당관",
        "year": 2023,
        "category": "교육 규정",
        "section": "연수 정책",
        "tags": ["의무연수", "교직원", "법정"]
    },
    {
        "source": "회계기준",
        "title": "운용리스 회계처리 기준",
        "author": "한국회계기준원",
        "year": 2022,
        "category": "회계",
        "section": "리스",
        "tags": ["운용리스", "임대", "회계"]
    }
]

vectors = ( document_embeddings.embed_documents( docs ) )

add_embeddings( vectors, docs, metadata )

print("=== INGEST COMPLETE ===")
print(f"Ingested {len(docs)} documents with enhanced metadata")

#============= 테스트용 기능: 인덱스와 문서 저장 ==============

from app.services.vector.vector_store import ( save_index, save_documents )

save_index( "data/faiss/index.bin" )
save_documents( "data/faiss/documents.json" )

print("=== INDEX AND DOCUMENTS SAVED ===" )