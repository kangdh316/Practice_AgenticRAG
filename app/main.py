from fastapi import FastAPI
from app.graph import graph

app = FastAPI()


@app.post("/chat")
async def chat(req: dict):

    result = await graph.ainvoke({
        "question": req["question"]
    })

    return result