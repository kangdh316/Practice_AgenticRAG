from app.llm.embedding import ( query_embeddings )
from app.services.vector.vector_store import ( similarity_search )

#============= 테스트용 기능: 인덱스와 문서 로드 ==============

from app.services.vector.vector_store import ( load_index, load_documents )
load_index( "data/faiss/index.bin" )
load_documents( "data/faiss/documents.json" )

#==========================================================

query = "학교 태블릿 구매 승인 절차"
query_vector = ( query_embeddings.embed_query( query ) )
results = similarity_search( query_vector, top_k=3 )

print()
print("=== SEARCH RESULTS ===")
print()

for i, r in enumerate(results, 1):
    print(f"[Result {i}]")
    print(f"SCORE: {r['score']:.4f}")
    print()
    
    metadata = r.get("metadata", {})
    if metadata:
        print("=== METADATA ===")
        if metadata.get("title"):
            print(f"제목: {metadata['title']}")
        if metadata.get("author"):
            print(f"저자: {metadata['author']}")
        if metadata.get("year"):
            print(f"연도: {metadata['year']}")
        if metadata.get("source"):
            print(f"출처: {metadata['source']}")
        if metadata.get("source_url"):
            print(f"URL: {metadata['source_url']}")
        if metadata.get("category"):
            print(f"카테고리: {metadata['category']}")
        if metadata.get("section"):
            print(f"섹션: {metadata['section']}")
        if metadata.get("tags"):
            print(f"태그: {', '.join(metadata['tags'])}")
        print()
    
    print("=== DOCUMENT CONTENT ===")
    print(r["document"])
    print()
    print("-" * 60)
    print()