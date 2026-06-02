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

for r in results:
    print("SCORE:", r["score"])
    print("DOC:")
    print(r["document"])
    print("METADATA:")
    print(r["metadata"])
    print("-" * 50)