from app.services.vector.faiss_manager import FAISSManager


faiss_manager = FAISSManager(
    dim=1024,
    base_dir="./vector_store",
)