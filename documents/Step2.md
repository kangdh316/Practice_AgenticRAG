# Agentic GraphRAG 확장 7단계 상세 구현 가이드

---

# 개요

현재 MVP 구조:

```text id="f3m8t2"
FastAPI
+
LangGraph
+
Gemini
+
FAISS
+
Reranker
```

는:

```text id="r5n1v7"
기본적인 Internal VectorRAG
```

단계다.

이 문서에서는 이를:

```text id="q9k4x6"
Self-Expanding Agentic GraphRAG
```

로 발전시키는 과정을 설명한다.

---

# 전체 최종 목표 구조

```text id="z6m2p8"
User
 ↓
Planner Agent
 ↓
Internal Retrieval
 ↓
Rerank
 ↓
Confidence Check
 ├─ 충분 → Answer
 │
 └─ 부족
      ↓
   Web Search
      ↓
   Crawl
      ↓
   Dynamic Ingestion
      ↓
   Entity Extraction
      ↓
   Graph Expansion
      ↓
   Re-Retrieve
      ↓
   Final Answer
```

---

# 프로젝트 구조 확장

최종 권장 구조:

```text id="n2x7w4"
app/
│
├── llm/
│
├── services/
│   ├── vector/
│   ├── graph/
│   ├── web/
│   ├── entity/
│   └── planner/
│
├── nodes/
│
├── prompts/
│
├── repositories/
│
├── schemas/
│
└── utils/
```

---

# 핵심 설계 철학

중요한 건:

```text id="b5m9r1"
"기능별 분리"
```

다.

즉:

| 영역           | 역할           |
| ------------ | ------------ |
| services     | 실제 처리 로직     |
| nodes        | LangGraph 연결 |
| repositories | 저장 계층        |
| llm          | 모델 관리        |
| prompts      | Prompt 관리    |

---

# 1단계 — Tavily 기반 Web Search 통합

---

# 목표

내부 KB로 부족할 경우:

```text id="t4x1m8"
외부 검색 수행
```

---

# 설치

```bash id="k7n3v2"
pip install tavily-python
```

---

# config.py 수정

```python id="g2m8p4"
TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)

TRUSTED_DOMAINS = [
    "law.go.kr",
    "g2b.go.kr",
    "moe.go.kr",
]
```

---

# services/web/search_service.py

```python id="v8k5n1"
from tavily import TavilyClient
from app.config import (
    TAVILY_API_KEY,
    TRUSTED_DOMAINS
)

client = TavilyClient(
    api_key=TAVILY_API_KEY
)


async def search_web(query: str):

    response = client.search(
        query=query,
        include_domains=TRUSTED_DOMAINS,
        max_results=5
    )

    return response["results"]
```

---

# 반환 형태 예시

```python id="x3r9m7"
[
    {
        "title": "...",
        "url": "...",
        "content": "..."
    }
]
```

---

# LangGraph Node 연결

## nodes/web_search_node.py

```python id="q6m1t5"
from app.services.web.search_service import (
    search_web
)


async def web_search_node(state):

    results = await search_web(
        state["question"]
    )

    return {
        "web_results": results
    }
```

---

# 데이터 흐름

```text id="p7n2x4"
Question
 ↓
Retrieve
 ↓
Threshold Fail
 ↓
Web Search
```

---

# 중요한 운영 포인트

반드시:

```text id="s5m8v3"
Trusted Domain 제한
```

을 둔다.

왜냐하면:

* hallucination 감소
* spam 제거
* entity 품질 안정
* graph 품질 유지

효과가 있다.

---

# 2단계 — Web Crawling + Dynamic Ingestion

---

# 목표

검색 결과를:

```text id="r1k7m6"
실시간 VectorRAG에 편입
```

한다.

---

# 데이터 흐름

```text id="u3x9n5"
Search Result
 ↓
Crawl
 ↓
Chunk
 ↓
Embedding
 ↓
FAISS Add
```

---

# crawl_service.py

```python id="m8t4v1"
import trafilatura


async def crawl_url(url: str):

    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return None

    text = trafilatura.extract(downloaded)

    return text
```

---

# ingest_service.py

## 신규 생성

```python id="n4x7m2"
from app.services.chunk_service import (
    split_text
)

from app.llm.embedding import embeddings

from app.services.vector_store import (
    add_embeddings
)


async def ingest_document(text):

    chunks = split_text(text)

    vectors = embeddings.embed_documents(
        chunks
    )

    add_embeddings(
        vectors,
        chunks
    )

    return chunks
```

---

# crawl_node.py

```python id="j9m2r8"
from app.services.web.crawl_service import (
    crawl_url
)

from app.services.vector.ingest_service import (
    ingest_document
)


async def crawl_node(state):

    docs = []

    for result in state["web_results"]:

        text = await crawl_url(
            result["url"]
        )

        if not text:
            continue

        docs.append(text)

        await ingest_document(text)

    return {
        "crawled_docs": docs
    }
```

---

# 핵심 의미

이 단계부터:

```text id="c8x5n1"
시스템이 실시간으로 지식을 흡수
```

하기 시작한다.

---

# 중요한 문제

이 시점부터:

```text id="w2m9v4"
Vector Pollution
```

위험 발생.

즉:

* 중복 문서
* 저품질 문서
* 오래된 문서

가 누적될 수 있다.

---

# 따라서 이후 단계 필요

* Metadata
* Deduplication
* User Approval

---

# 3단계 — User Approval 기반 Knowledge Expansion

---

# 목표

외부 자료를:

```text id="k6t1m9"
사용자 승인 후 영구 저장
```

한다.

---

# 현재 문제

현재 구조:

```text id="q4x8n2"
자동 ingestion
```

이다.

위험:

* 잘못된 정보 축적
* KB 오염
* graph quality 저하

---

# 추천 구조

```text id="g1m7v5"
Web Search
 ↓
Candidate Docs
 ↓
User Approval
 ↓
Permanent Ingestion
```

---

# 새로운 저장 구조

```text id="b8n2x6"
data/
├── raw/
├── approved/
└── metadata/
```

---

# metadata schema 예시

## schemas/document.py

```python id="r5m9t3"
from pydantic import BaseModel
from datetime import datetime


class DocumentMetadata(BaseModel):

    source_url: str

    domain: str

    collected_at: datetime

    approved: bool

    embedding_model: str
```

---

# approved 저장 함수

## repositories/document_repository.py

```python id="p2v8m1"
import json
from pathlib import Path


def save_document(
    text,
    metadata
):

    file_id = hash(
        metadata["source_url"]
    )

    Path(
        f"data/approved/{file_id}.txt"
    ).write_text(text)

    Path(
        f"data/metadata/{file_id}.json"
    ).write_text(
        json.dumps(metadata)
    )
```

---

# UX 흐름

```text id="m7x4n8"
현재 KB에 충분한 자료가 없습니다.

다음 자료를 저장하시겠습니까?

[1] 국가법령정보센터
[2] 조달청
[3] 교육부 지침
```

---

# 중요한 점

이 단계부터 시스템은:

```text id="x1k5v2"
Self-Expanding Knowledge Base
```

가 된다.

---

# 4단계 — Entity Canonicalization

---

# 목표

서로 다른 표현을:

```text id="n3m8t4"
동일 Entity로 통합
```

한다.

---

# 문제 사례

```text id="h7x2v9"
조달청
나라장터
G2B
```

실제로는 강하게 연결됨.

하지만 embedding만 사용하면:

```text id="z5m1n6"
서로 다른 node
```

가 된다.

---

# graph fragmentation 예시

```text id="t2v8m3"
조달청 ─ 학교
나라장터 ─ 계약
G2B ─ 구매
```

실제로는 하나여야 함.

---

# canonical_service.py

```python id="f9m4x2"
ENTITY_ALIAS = {

    "나라장터": "조달청",

    "G2B": "조달청",
}


def canonicalize(entity):

    return ENTITY_ALIAS.get(
        entity,
        entity
    )
```

---

# entity extraction 수정

## entity_service.py

```python id="c6n1x7"
from app.services.entity.canonical_service import (
    canonicalize
)


async def extract_entities(text):

    ...

    entities = parsed_result

    canonical_entities = [
        canonicalize(e)
        for e in entities
    ]

    return canonical_entities
```

---

# 이후 확장

초기:

```text id="v8m3t5"
Dictionary 기반
```

후기:

```text id="k4x7n1"
Embedding clustering
```

가능.

---

# 중요성

GraphRAG 품질은 상당 부분:

```text id="b2m9v6"
Entity Quality
```

에서 결정된다.

---

# 5단계 — Typed Relation Extraction

---

# 목표

Entity 관계 유형까지 추출.

---

# 현재 상태

```text id="w6n2x4"
학교 ─ 조달청
```

수준.

---

# 목표 상태

```text id="q1m8t7"
학교 --구매--> 조달청
학교 --승인--> 교육청
교육청 --관리--> 지침
```

---

# relation_service.py

```python id="j5x9m2"
from app.llm.gemini import llm


async def extract_relations(text):

    prompt = f"""
    다음 텍스트에서
    Entity 간 관계를 추출해라.

    형식:
    [
      {{
        "source": "...",
        "relation": "...",
        "target": "..."
      }}
    ]

    텍스트:
    {text}
    """

    result = await llm.ainvoke(
        prompt
    )

    return result.content
```

---

# graph_service.py 수정

```python id="p8n4v1"
import networkx as nx

graph = nx.MultiDiGraph()


def add_relation(
    source,
    relation,
    target
):

    graph.add_edge(
        source,
        target,
        relation=relation
    )
```

---

# graph query 예시

```python id="x7m2t8"
def get_purchase_relations():

    results = []

    for u, v, data in graph.edges(data=True):

        if data["relation"] == "구매":

            results.append(
                (u, v)
            )

    return results
```

---

# 핵심 의미

이 단계부터:

```text id="n1v6m4"
검색
```

이 아니라:

```text id="g5x8t2"
관계 기반 reasoning
```

가능.

---

# 6단계 — Neo4j Persistent Graph

---

# 목표

현재 메모리 graph를:

```text id="m9t3v7"
영구 graph DB
```

로 확장.

---

# 설치

```bash id="k2x8n5"
pip install neo4j
```

---

# docker-compose.yml

```yaml id="q4m1v8"
version: '3'

services:

  neo4j:

    image: neo4j:5

    ports:
      - "7474:7474"
      - "7687:7687"

    environment:
      NEO4J_AUTH: neo4j/password
```

---

# 실행

```bash id="v7n2m4"
docker compose up -d
```

---

# graph_repository.py

```python id="t8m5x1"
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)


def save_relation(
    source,
    relation,
    target
):

    query = f"""
    MERGE (a:Entity {{name:$source}})
    MERGE (b:Entity {{name:$target}})

    MERGE (a)-[:{relation}]->(b)
    """

    with driver.session() as session:

        session.run(
            query,
            source=source,
            target=target
        )
```

---

# 매우 중요한 개념

Neo4j는:

```text id="y3m7n2"
검색 엔진
```

이 아니라:

```text id="d6x1v9"
관계 추론 엔진
```

이다.

---

# 활용 예시

```cypher id="c5t8m3"
MATCH (a)-[:승인]->(b)
RETURN a,b
```

---

# 7단계 — Agentic Planner

---

# 목표

LLM이:

```text id="w8m2x5"
무엇을 해야 하는지
판단
```

하게 만든다.

---

# 현재 문제

현재 구조:

```text id="k3v7n1"
고정 workflow
```

이다.

---

# 목표 구조

```text id="f9m4t8"
Planner
 ├─ Retrieve
 ├─ Web Search
 ├─ Graph Expand
 ├─ Retry
 └─ Answer
```

---

# planner_service.py

```python id="n6x2m9"
from app.llm.gemini import llm


async def plan(question):

    prompt = f"""
    사용자 질문을 분석해라.

    가능한 action:

    - retrieve
    - web_search
    - graph_expand
    - answer

    JSON만 반환.

    Question:
    {question}
    """

    result = await llm.ainvoke(
        prompt
    )

    return result.content
```

---

# planner_node.py

```python id="r4m8v2"
from app.services.planner.planner_service import (
    plan
)

import json


async def planner_node(state):

    result = await plan(
        state["question"]
    )

    parsed = json.loads(result)

    return {
        "next_action": parsed["action"]
    }
```

---

# state.py 수정

```python id="b7x3m5"
class AgentState(TypedDict):

    ...

    next_action: str
```

---

# planner_router.py

```python id="p1m9v4"
def planner_router(state):

    return state["next_action"]
```

---

# graph.py 수정

```python id="x5n2m8"
builder.add_node(
    "planner",
    planner_node
)

builder.set_entry_point(
    "planner"
)

builder.add_conditional_edges(
    "planner",
    planner_router,
    {
        "retrieve": "retrieve",
        "web_search": "web_search",
        "graph_expand": "graph_expand",
        "answer": "answer"
    }
)
```

---

# 중요 개념

이 단계부터:

```text id="h2m7v1"
workflow
```

가 아니라:

```text id="q8x4n6"
decision system
```

이 된다.

---

# 최종 구조

```text id="v1m5t9"
User
 ↓
Planner
 ↓
Retrieve
 ↓
Rerank
 ↓
Threshold
 ├─ 충분 → Answer
 │
 └─ 부족
      ↓
   Web Search
      ↓
   Crawl
      ↓
   Ingest
      ↓
   Entity
      ↓
   Relation
      ↓
   Graph Expand
      ↓
   Re-Retrieve
      ↓
   Answer
```

---

# 최종적으로 얻게 되는 시스템

이 구조는 단순 챗봇이 아니라:

```text id="y7m2x8"
Knowledge-Aware
Self-Expanding
Agentic GraphRAG
```

시스템이다.

---

# 실무적으로 가장 중요한 것

실제 RAG 품질은:

```text id="n4v8m3"
LLM 자체
```

보다:

```text id="k9m1x5"
Retrieval
+
Rerank
+
Entity Quality
+
Knowledge Governance
+
Planner Logic
```

에서 훨씬 크게 결정된다.
