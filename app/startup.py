from pathlib import Path
from app.services.vector.vector_store import ( load_index, load_documents )

def initialize_vector_store():
    index_path = "data/faiss/index.bin"
    doc_path = "data/faiss/documents.json"

    if not Path(index_path).exists():
        print("FAISS index not found")
        return
    
    load_index(index_path)
    load_documents(doc_path)
    
    print("FAISS loaded")