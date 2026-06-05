from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.graph import graph
from app.container import faiss_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    faiss_manager.load_memory()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/temp")
async def get_temp_vector_store():
    return faiss_manager.get_temp_documents()

@app.post("/approve")
async def approve_temp_documents(req: dict):
    faiss_manager.promote_temp_to_prod(req["index_list"])

@app.post("/chat")
async def chat(req: dict):

    result = await graph.ainvoke({
        "question": req["question"]
    })

    return result