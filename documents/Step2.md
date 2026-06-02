# Agentic RAG 확장 7단계 실전 가이드

---

# 개요

현재 MVP 구조:

```text id="j8t4k2"
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

```text id="w4p9f7"
"기본적인 내부 RAG"
```

수준이다.

여기서 실제 Agentic GraphRAG 수준으로 가기 위해 필요한 확장 단계를 설명한다.

---

# 전체 진화 흐름

```text id="c7d2x8"
1. Internal VectorRAG
        ↓
2. Web Search Integration
        ↓
3. Dynamic Knowledge Expansion
        ↓
4. Entity Canonicalization
        ↓
5. Typed Relation Graph
        ↓
6. Persistent Graph DB
        ↓
7. Agentic Planner System
```

---

# 1단계 — Tavily 기반 Web Search 통합

---

# 목표

내부 VectorRAG만으로 부족한 경우:

```text id="y3n8w1"
외부 신뢰 사이트 검색
```

을 수행한다.

---

# 현재 문제

현재 시스템:

```text id="g6f1q4"
FAISS 내부 문서만 검색 가능
```

하다.

즉:

* KB에 없는 질문 대응 불가
* 최신 정보 부족
* cold start 문제 존재

---

# 목표 구조

```text id="n9s5m2"
Question
 ↓
Internal Retrieval
 ↓
Confidence Check
 ├─ 충분 → Answer
 └─ 부족 → Web Search
```

---

# 추천 API

| API     | 추천도   |
| ------- | ----- |
| Tavily  | 매우 추천 |
| SerpAPI | 추천    |
| Exa     | 고급용   |

---

# Tavily 추천 이유

* RAG 최적화
* snippet 품질 우수
* Python 친화적
* hallucination 감소
* 비교적 저렴

---

# 설치

```bash id="r8v2j3"
pip install tavily-python
```

---

# 환경 변수

```env id="q4t6h9"
TAVILY_API_KEY=YOUR_KEY
```

---

# 서비스 구현

## app/services/search_service.py

```python id="m7d5w4"
from tavily import TavilyClient
from app.config import TAVILY_API_KEY

client = TavilyClient(
    api_key=TAVILY_API_KEY
)

TRUSTED_DOMAINS = [
    "law.go.kr",
    "g2b.go.kr",
    "moe.go.kr"
]


async def search_web(query):

    response = client.search(
        query=query,
        max_results=5,
        include_domains=TRUSTED_DOMAINS
    )

    return response["results"]
```

---

# 핵심 포인트

중요한 건:

```text id="k1b4n7"
"인터넷 전체"
```

가 아니라:

```text id="z6x3c5"
신뢰 가능한 제한된 지식 공간
```

이다.

---

# 2단계 — Web Crawling + Dynamic Ingestion

---

# 목표

검색 결과를:

```text id="s2m8r1"
실시간으로 수집하고
임시 VectorRAG에 편입
```

한다.

---

# 구조

```text id="a9n7v4"
Web Search
 ↓
Crawling
 ↓
Chunking
 ↓
Embedding
 ↓
Temporary Vector Store
```

---

# 핵심 개념

이 단계부터:

```text id="e3k5q8"
Static RAG
```

에서:

```text id="v6d1x2"
Dynamic RAG
```

로 진화한다.

---

# Crawl → Chunk → Embed

## ingest_service.py

```python id="b4m9r3"
from app.services.chunk_service import split_text
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
```

---

# 매우 중요한 점

이 단계부터:

```text id="t7f3m1"
지식이 동적으로 증가
```

한다.

---

# 3단계 — User Approval 기반 Knowledge Expansion

---

# 목표

외부 자료를:

```text id="u1n5p6"
사용자 승인 후 영구 저장
```

한다.

---

# 왜 중요한가?

무조건 ingestion하면:

```text id="h8c2v7"
Knowledge Pollution
```

이 발생한다.

---

# 추천 구조

```text id="r4w7k9"
Search Result
 ↓
User Approval
 ↓
Permanent Ingestion
```

---

# 예시 UX

```text id="f2x6n4"
현재 KB에 충분한 정보가 없습니다.

아래 자료를 저장하시겠습니까?

1. 국가법령정보센터
2. 교육부 지침
3. 조달청 계약 가이드
```

---

# 저장 시 필수 Metadata

```python id="n5k8d3"
{
  "source_url": "...",
  "domain": "...",
  "collected_at": "...",
  "approved": True,
  "embedding_model": "...",
}
```

---

# 중요 개념

이 단계부터 시스템은:

```text id="m3v9r2"
Self-Expanding Knowledge System
```

으로 진화한다.

---

# 4단계 — Entity Canonicalization

---

# 목표

서로 다른 표현을:

```text id="j7t2w6"
동일 Entity로 정규화
```

한다.

---

# 왜 필요한가?

예:

```text id="p4f1c8"
조달청
G2B
나라장터
```

실제로는 관련성이 매우 높다.

---

# 문제

정규화가 없으면:

```text id="w9k5r3"
graph fragmentation
```

발생.

---

# 추천 구조

```python id="q2n7v1"
ENTITY_ALIAS = {
    "나라장터": "조달청",
    "G2B": "조달청",
}
```

---

# 추천 방식

초기:

```text id="y6m3f4"
Dictionary 기반
```

후기:

```text id="s1v8p2"
Embedding 기반 clustering
```

---

# 매우 중요

GraphRAG 품질은 상당 부분:

```text id="b5k2t7"
Entity Quality
```

에서 결정된다.

---

# 5단계 — Typed Relation Extraction

---

# 목표

단순 Entity 연결이 아니라:

```text id="z8p1m5"
관계 유형까지 추출
```

한다.

---

# 현재 상태

```text id="k6v4n2"
A — B
```

정도만 존재.

---

# 목표 상태

```text id="g3x9t6"
학교 --승인--> 교육청
학교 --구매--> 조달청
조달청 --관리--> 나라장터
```

---

# Relation Extraction Prompt 예시

```python id="x4m7r1"
prompt = f"""
다음 텍스트에서
Entity 간 관계를 추출해라.

형식:
(Entity1, Relation, Entity2)

텍스트:
{text}
"""
```

---

# 추천 Relation 종류

| Relation | 의미         |
| -------- | ---------- |
| 승인       | approval   |
| 참조       | reference  |
| 소속       | belongs_to |
| 관리       | manages    |
| 구매       | purchase   |
| 근거       | based_on   |

---

# 중요성

이 단계부터:

```text id="v2c8n5"
단순 RAG
```

가 아니라:

```text id="t9m1x4"
Graph Reasoning
```

가능해진다.

---

# 6단계 — Neo4j 기반 Persistent Graph

---

# 목표

동적 메모리 graph를:

```text id="d4f7w3"
영구 Graph DB
```

로 확장한다.

---

# 현재 문제

NetworkX는:

* 메모리 기반
* 영속성 부족
* 복잡 traversal 제한

---

# Neo4j 도입 시점

아래 상황이면 추천:

* multi-hop reasoning
* graph persistence
* graph analytics
* 대규모 entity
* Cypher query 필요

---

# 설치

```bash id="h9r2v5"
pip install neo4j
```

---

# 예시 구조

```text id="p6k4n8"
(:School)-[:APPROVES]->(:EducationOffice)

(:School)-[:PURCHASES]->(:G2B)
```

---

# Cypher 예시

```cypher id="c1m8w2"
MATCH (s:School)-[:PURCHASES]->(g:G2B)
RETURN s, g
```

---

# 매우 중요한 개념

Neo4j는:

```text id="x7v5p1"
검색 엔진
```

이 아니라:

```text id="r3n9f6"
관계 reasoning 엔진
```

이다.

---

# 7단계 — Agentic Planner System

---

# 목표

LLM이:

```text id="j2m7t9"
무엇을 해야 할지
스스로 결정
```

하게 만든다.

---

# 현재 구조 문제

현재 workflow:

```text id="w5x1p4"
고정 흐름
```

이다.

즉:

```text id="n8v6c2"
retrieve → rerank → answer
```

만 수행.

---

# 목표 구조

```text id="u3k9m5"
Planner Agent
 ├─ Search 필요?
 ├─ Graph 확장 필요?
 ├─ Web 검색 필요?
 ├─ 재검색 필요?
 ├─ 추가 reasoning 필요?
 └─ 답변 가능?
```

---

# 핵심 개념

이 단계부터:

```text id="a6v2t7"
Workflow
```

가 아니라:

```text id="f9m4x1"
Decision Making System
```

이 된다.

---

# 예시 Prompt

```python id="k5w8r3"
prompt = f"""
사용자 질문을 분석하고
다음 행동 중 하나를 선택해라.

- retrieve
- web_search
- graph_expand
- answer

Question:
{question}
"""
```

---

# Planner 결과 예시

```json id="d7p1n4"
{
  "action": "web_search"
}
```

---

# LangGraph Conditional Branch

```python id="x2m5v9"
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

# 이 단계의 진짜 의미

여기서부터 시스템은:

```text id="q8t4m2"
Agentic RAG
```

가 된다.

즉:

* 상황 판단
* 행동 선택
* iterative reasoning
* self-correction

가능.

---

# 최종 구조

```text id="z4n7v1"
User
 ↓
Planner Agent
 ↓
Retrieve
 ↓
Rerank
 ↓
Confidence Check
 ├─ 충분
 │    ↓
 │  Answer
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
   Answer
```

---

# 최종적으로 얻게 되는 것

이 7단계를 거치면 시스템은:

```text id="p1m5x8"
단순 챗봇
```

이 아니라:

```text id="s7v2n6"
Knowledge-Aware Agentic GraphRAG
```

수준으로 발전한다.

---

# 가장 중요한 핵심

실무 RAG 품질은 단순히:

```text id="m4k8t1"
좋은 LLM
```

에서 나오지 않는다.

실제로는:

```text id="b9n3x5"
Retrieval
+
Rerank
+
Knowledge Governance
+
Graph Reasoning
+
Agentic Routing
```

에서 결정된다.
