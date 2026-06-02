from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.graph import graph
from app.startup import ( initialize_vector_store )

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_vector_store()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(req: dict):

    result = await graph.ainvoke({
        "question": req["question"]
    })

    return result