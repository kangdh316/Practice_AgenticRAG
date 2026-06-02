from sentence_transformers import ( CrossEncoder )

reranker = CrossEncoder( "BAAI/bge-reranker-base" )