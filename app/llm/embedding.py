from sentence_transformers import SentenceTransformer

import numpy as np

_model = SentenceTransformer("BAAI/bge-m3")

def document_embeddings(text: str,) -> list[float]:

    embedding = _model.encode(f"passage: {text}", normalize_embeddings=True,)

    return embedding.tolist()

def query_embeddings(text: str,) -> list[float]:

    embedding = _model.encode(f"query: {text}", normalize_embeddings=True,)

    return embedding.tolist()