# Practice_AgenticRAG
AgenticRAG 개발 연습 목적의 Repository

아래 문서는 ChatGPT 무료 버전에 의해 작성된 구축 가이드로,
불완전한 부분이 다수 있을 수 있으므로 그대로 사용하지 말고 참고자료로서 활용할 것.


# Python 3.11 기반 Gemini + FastAPI + LangGraph Agentic RAG 구축 가이드

---

# 1. 목표 아키텍처

최종적으로 아래 구조를 목표로 한다.

```text
User
 ↓
FastAPI
 ↓
LangGraph Workflow
 ↓
Vector Retrieval (FAISS)
 ↓
Reranker
 ↓
Conditional Branch
 ├─ Internal KB sufficient
 │      ↓
 │   Answer
 │
 └─ 부족한 경우
        ↓
   Web Search
        ↓
   Crawling
        ↓
   Temporary RAG
        ↓
   Knowledge Expansion
        ↓
   Answer
```

---

# 2. 개발 환경

## 권장 환경

| 항목     | 권장                      |
| ------ | ----------------------- |
| Python | 3.11.x                  |
| OS     | Windows / Ubuntu / WSL2 |
| IDE    | VSCode                  |
| 가상환경   | venv                    |

---

# 3. 프로젝트 생성

## 디렉토리 생성

```bash
mkdir agentic-rag
cd agentic-rag
```

---

# 4. Python 가상환경 생성

## Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

## Linux / Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# 5. pip 업그레이드

```bash
python -m pip install --upgrade pip setuptools wheel
```

---

# 6. requirements.txt 작성

## requirements.txt

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6

langchain==0.3.7
langgraph==0.2.39
langchain-google-genai==2.0.1

google-generativeai==0.8.3

faiss-cpu==1.8.0.post1

sentence-transformers==3.2.1

trafilatura==1.12.2
beautifulsoup4==4.12.3
httpx==0.27.2

networkx==3.4.2

python-dotenv==1.0.1

numpy==1.26.4
pydantic==2.9.2
```

---

# 7. 패키지 설치

```bash
pip install -r requirements.txt
```

---

# 8. 프로젝트 구조

```text
agentic-rag/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── state.py
│   ├── graph.py
│   │
│   ├── llm/
│   │   ├── gemini.py
│   │   ├── embedding.py
│   │   └── reranker.py
│   │
│   ├── services/
│   │   ├── vector_store.py
│   │   ├── search_service.py
│   │   ├── crawl_service.py
│   │   ├── chunk_service.py
│   │   ├── entity_service.py
│   │   └── graph_service.py
│   │
│   ├── nodes/
│   │   ├── retrieve_node.py
│   │   ├── rerank_node.py
│   │   ├── threshold_node.py
│   │   ├── web_search_node.py
│   │   ├── crawl_node.py
│   │   ├── ingest_node.py
│   │   ├── entity_node.py
│   │   ├── graph_node.py
│   │   └── answer_node.py
│   │
│   ├── prompts/
│   │   └── prompts.py
│   │
│   └── schemas/
│       └── chat.py
│
├── data/
│   ├── documents/
│   └── faiss/
│
├── .env
├── requirements.txt
└── README.md
```

---

# 9. 환경 변수 설정

## .env

```env
GEMINI_API_KEY=YOUR_GEMINI_KEY
```

---

# 10. 설정 파일 작성

## app/config.py

```python
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

VECTOR_TOP_K = 10
RERANK_TOP_K = 5

SIMILARITY_THRESHOLD = 0.72

TRUSTED_DOMAINS = [
    "law.go.kr",
    "g2b.go.kr",
    "moe.go.kr",
]
```

---

# 11. Gemini LLM 구성

## app/llm/gemini.py

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0
)
```

---

# 12. Embedding 구성

## app/llm/embedding.py

```python
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004"
)
```

---

# 13. Reranker 구성

## app/llm/reranker.py

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder(
    "BAAI/bge-reranker-base"
)
```

---

# 14. Vector Store 구성

## app/services/vector_store.py

```python
import faiss
import numpy as np

documents = []

index = None


def create_index(dim: int):

    global index

    index = faiss.IndexFlatL2(dim)


def add_embeddings(embeddings, docs):

    global documents

    vectors = np.array(
        embeddings
    ).astype("float32")

    index.add(vectors)

    documents.extend(docs)


def similarity_search(query_embedding, top_k=5):

    D, I = index.search(
        np.array([query_embedding]).astype("float32"),
        top_k
    )

    results = []

    for idx, score in zip(I[0], D[0]):

        if idx >= len(documents):
            continue

        results.append({
            "document": documents[idx],
            "score": float(score)
        })

    return results
```

---

# 15. Chunking 구성

## app/services/chunk_service.py

```python
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)


def split_text(text: str):

    return splitter.split_text(text)
```

---

# 16. Crawling 구성

## app/services/crawl_service.py

```python
import trafilatura


async def crawl(url: str):

    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return None

    text = trafilatura.extract(downloaded)

    return text
```

---

# 17. Entity Extraction

## app/services/entity_service.py

```python
from app.llm.gemini import llm


async def extract_entities(text: str):

    prompt = f"""
    아래 문장에서 핵심 Entity를 추출해라.

    텍스트:
    {text}

    JSON 배열만 반환.
    """

    result = await llm.ainvoke(prompt)

    return result.content
```

---

# 18. Dynamic Graph

## app/services/graph_service.py

```python
import networkx as nx

graph = nx.Graph()


def build_graph(entities):

    for i in range(len(entities)-1):

        graph.add_edge(
            entities[i],
            entities[i+1]
        )

    return graph


def expand_entity(entity):

    if entity not in graph:
        return []

    return list(
        graph.neighbors(entity)
    )
```

---

# 19. LangGraph State

## app/state.py

```python
from typing import TypedDict, List


class AgentState(TypedDict):

    question: str

    retrieved_docs: List[dict]

    reranked_docs: List[dict]

    confidence_score: float

    web_results: List[str]

    crawled_docs: List[str]

    entities: List[str]

    graph_context: List[str]

    answer: str
```

---

# 20. Retrieval Node

## app/nodes/retrieve_node.py

```python
from app.llm.embedding import embeddings
from app.services.vector_store import (
    similarity_search
)


async def retrieve_node(state):

    query_embedding = embeddings.embed_query(
        state["question"]
    )

    results = similarity_search(
        query_embedding,
        top_k=10
    )

    return {
        "retrieved_docs": results
    }
```

---

# 21. Rerank Node

## app/nodes/rerank_node.py

```python
from app.llm.reranker import reranker


async def rerank_node(state):

    docs = state["retrieved_docs"]

    pairs = [
        [
            state["question"],
            d["document"]
        ]
        for d in docs
    ]

    scores = reranker.predict(pairs)

    reranked = []

    for doc, score in zip(docs, scores):

        reranked.append({
            "document": doc["document"],
            "score": float(score)
        })

    reranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "reranked_docs": reranked[:5],
        "confidence_score": reranked[0]["score"]
    }
```

---

# 22. Threshold Branch

## app/nodes/threshold_node.py

```python
from app.config import SIMILARITY_THRESHOLD


def threshold_router(state):

    if state["confidence_score"] >= SIMILARITY_THRESHOLD:
        return "answer"

    return "web_search"
```

---

# 23. Web Search Node

## app/nodes/web_search_node.py

```python
async def web_search_node(state):

    # 추후 Tavily API 연결

    return {
        "web_results": []
    }
```

---

# 24. Answer Node

## app/nodes/answer_node.py

```python
from app.llm.gemini import llm


async def answer_node(state):

    docs = state.get(
        "reranked_docs",
        []
    )

    context = "\n\n".join([
        d["document"]
        for d in docs
    ])

    prompt = f"""
    아래 Context를 기반으로 답변해라.

    Context:
    {context}

    Question:
    {state["question"]}
    """

    result = await llm.ainvoke(prompt)

    return {
        "answer": result.content
    }
```

---

# 25. LangGraph 구성

## app/graph.py

```python
from langgraph.graph import (
    StateGraph,
    END
)

from app.state import AgentState

from app.nodes.retrieve_node import retrieve_node
from app.nodes.rerank_node import rerank_node
from app.nodes.answer_node import answer_node
from app.nodes.web_search_node import web_search_node
from app.nodes.threshold_node import threshold_router

builder = StateGraph(AgentState)

builder.add_node(
    "retrieve",
    retrieve_node
)

builder.add_node(
    "rerank",
    rerank_node
)

builder.add_node(
    "answer",
    answer_node
)

builder.add_node(
    "web_search",
    web_search_node
)

builder.set_entry_point("retrieve")

builder.add_edge(
    "retrieve",
    "rerank"
)

builder.add_conditional_edges(
    "rerank",
    threshold_router,
    {
        "answer": "answer",
        "web_search": "web_search"
    }
)

builder.add_edge(
    "answer",
    END
)

builder.add_edge(
    "web_search",
    "answer"
)

graph = builder.compile()
```

---

# 26. FastAPI 서버

## app/main.py

```python
from fastapi import FastAPI
from app.graph import graph

app = FastAPI()


@app.post("/chat")
async def chat(req: dict):

    result = await graph.ainvoke({
        "question": req["question"]
    })

    return result
```

---

# 27. 서버 실행

```bash
uvicorn app.main:app --reload
```

---

# 28. 테스트

## Swagger 접속

```text
http://127.0.0.1:8000/docs
```

---

# 요청 예시

```json
{
  "question": "학교 태블릿 공동구매 승인 절차는?"
}
```

---

# 29. 현재 단계에서 구현된 기능

| 기능                  | 상태    |
| ------------------- | ----- |
| Gemini Chat         | 완료    |
| VectorRAG           | 완료    |
| FAISS               | 완료    |
| Rerank              | 완료    |
| LangGraph Workflow  | 완료    |
| Conditional Routing | 완료    |
| Threshold Fallback  | 완료    |
| FastAPI             | 완료    |
| Dynamic Graph       | 기본 완료 |

---

# 30. 다음 단계 확장 추천

## 1단계

Tavily 검색 연결

---

## 2단계

Web Crawling + 임시 Ingestion

---

## 3단계

User Approval 기반 Knowledge Expansion

---

## 4단계

Entity Canonicalization

---

## 5단계

Typed Relation Extraction

예:

```text
A --승인--> B
A --참조--> C
```

---

## 6단계

Neo4j 연동

---

## 7단계

Agentic Planner 추가

예:

* 검색 필요 여부 판단
* 그래프 확장 여부 판단
* 재검색 여부 판단

---

# 31. 최종 목표 구조

```text
User
 ↓
Planner Agent
 ↓
Internal VectorRAG
 ↓
Reranker
 ↓
Confidence Check
 ├─ 충분
 │   ↓
 │ Answer
 │
 └─ 부족
      ↓
   Web Search
      ↓
   Crawl
      ↓
   Temporary RAG
      ↓
   Entity Extraction
      ↓
   Graph Expansion
      ↓
   Knowledge Ingestion
      ↓
   Answer
```

---

# 32. 중요한 학습 포인트

이 프로젝트에서 가장 중요한 건:

* Chunking
* Retrieval
* Reranking
* Thresholding
* Context 구성
* Graph Expansion
* Agentic Routing

을 직접 경험하는 것이다.

실무 RAG 품질은 상당 부분:

```text
Retrieval + Rerank + Context Engineering
```

에서 결정된다.
