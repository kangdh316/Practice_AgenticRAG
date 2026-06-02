# RAW/APPROVED 저장소 관리 기능 구현 가이드

## 개요

FastAPI 애플리케이션에 **Raw/Approved 저장소 분리 기능**을 추가했습니다. 이를 통해 웹 검색으로 수집된 문서와 승인된 문서를 분리하여 관리할 수 있습니다.

## 주요 기능

### 1. 저장소 분리 (Raw/Approved)

**Approved 저장소**
- 신뢰도 높은 문서들을 저장
- 기본 검색(RAG) 시 이곳에서 검색 수행
- 초기에 기존 벡터스토어의 모든 데이터가 여기에 저장됨

**Raw 저장소**
- 웹 검색으로 수집된 문서 저장
- Threshold 이상의 유사도를 가진 웹 검색 결과 자동 저장
- 검토 후 승인된 문서는 Approved로 이동 가능

### 2. 사전 조건

✅ **사전 조건 1: 웹 검색 결과를 Raw 저장소에 저장**
- `web_rerank_node.py`에서 자동 구현
- `SIMILARITY_THRESHOLD` (기본값: 0.72) 이상의 재순위 점수를 가진 결과만 Raw에 저장
- 메타데이터 포함: `score`, `source_type: "web_search"`

✅ **사전 조건 2: 현재 데이터를 Approved로 초기화**
- `app/startup.py`의 `initialize_vector_store()` 실행 시 기존 데이터가 Approved에 저장됨

### 3. 추가 구현 기능

#### 기능 1: Raw 저장소 검색 API

**엔드포인트:** `POST /api/raw/search`

```bash
curl -X POST http://localhost:8000/api/raw/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "기계 학습",
    "top_k": 10
  }'
```

**요청 본문:**
```json
{
  "query": "검색 쿼리",
  "top_k": 10  // 선택사항, 기본값: 10
}
```

**응답:**
```json
{
  "query": "기계 학습",
  "results": [
    {
      "index": 0,
      "document": "문서 내용...",
      "score": 0.8234,
      "metadata": {
        "title": "웹 검색 결과 제목",
        "source_type": "web_search",
        "score": 0.85
      }
    }
  ],
  "total": 1
}
```

#### 기능 2: Raw → Approved 이동 API

**엔드포인트:** `POST /api/raw/approve`

```bash
curl -X POST http://localhost:8000/api/raw/approve \
  -H "Content-Type: application/json" \
  -d '{
    "indices": [0, 2, 5]
  }'
```

**요청 본문:**
```json
{
  "indices": [0, 2, 5]  // 이동할 문서의 인덱스 배열
}
```

**응답:**
```json
{
  "status": "success",
  "moved_count": 3,
  "indices": [0, 2, 5]
}
```

#### 기능 3: 저장소 상태 조회 API

**엔드포인트:** `GET /api/status`

```bash
curl http://localhost:8000/api/status
```

**응답:**
```json
{
  "approved": {
    "count": 45,
    "index_size": 45
  },
  "raw": {
    "count": 12,
    "index_size": 12
  }
}
```

## 코드 변경 사항

### 1. `vector_store.py` 리팩토링

**변경점:**
- 글로벌 변수 분리: `documents_approved`, `metadatas_approved`, `index_approved` / `documents_raw`, `metadatas_raw`, `index_raw`
- `add_embeddings()` - `to_approved` 파라미터 추가
- `similarity_search()` - `from_approved` 파라미터 추가
- `get_stats()` - 양쪽 저장소 상태 조회
- `save_documents()`, `load_documents()` - `approved` 파라미터 추가

### 2. `ingest_service.py` 수정

```python
async def ingest_document(text, metadata=None, to_approved=True):
    # to_approved=True: approved에 저장 (기본값)
    # to_approved=False: raw에 저장
```

### 3. `retrieval_service.py` 수정

```python
async def retrieve_documents(question: str, top_k=5, from_approved=True):
    # from_approved=True: approved에서 검색 (기본값)
    # from_approved=False: raw에서 검색
```

### 4. `web_rerank_node.py` 개선

**기능:**
- Threshold 이상의 재순위 점수를 가진 웹 검색 결과를 자동으로 Raw 저장소에 저장
- 각 문서에 메타데이터 추가: `source_type: "web_search"`, `score: <rerank_score>`

**코드:**
```python
# threshold 이상의 결과를 raw에 저장
for result in reranked:
    if result["score"] >= SIMILARITY_THRESHOLD:
        # 문서를 임베딩하고 raw에 추가
        add_embeddings(
            doc_embedding,
            [result["document"]],
            [metadata],
            to_approved=False  # raw에 저장
        )
```

### 5. `main.py` API 엔드포인트 추가

- `GET /api/status` - 저장소 상태 조회
- `POST /api/raw/search` - Raw 저장소 검색
- `POST /api/raw/approve` - Raw에서 Approved로 이동

## 사용 시나리오

### 시나리오 1: 기본 RAG 검색 (Approved 사용)

```python
# 사용자의 질문에 대해 기본 RAG로 검색
results = await retrieve_documents(
    question="이 내용은?",
    top_k=5,
    from_approved=True  # 신뢰할 수 있는 approved 데이터에서만 검색
)
```

### 시나리오 2: 웹 검색 결과 자동 저장

```
사용자 질문 → Retrieve 시도 → 신뢰도 낮음 (Threshold 미만)
→ Web Search 실행 → Rerank 수행
→ Threshold 이상의 결과는 자동으로 Raw에 저장
→ 사용자에게 답변 제공
```

### 시나리오 3: 수동 승인 워크플로우

```
1. Raw 저장소 검색
   GET /api/raw/search?query=검색어&top_k=10

2. 결과 검토 및 선택

3. 선택된 문서 승인
   POST /api/raw/approve
   Body: {"indices": [0, 2, 5]}

4. 상태 확인
   GET /api/status
```

## 기술 상세

### 벡터 스토어 구조

```
Vector Store (메모리 기반)
├── Approved (신뢰도 높은 문서)
│   ├── documents_approved: 문서 내용 리스트
│   ├── metadatas_approved: 메타데이터 리스트
│   └── index_approved: FAISS IndexFlatIP
│
└── Raw (웹 검색 결과)
    ├── documents_raw: 문서 내용 리스트
    ├── metadatas_raw: 메타데이터 리스트
    └── index_raw: FAISS IndexFlatIP
```

### 임베딩 방식

- **Cosine Similarity:** `IndexFlatIP` 사용 (내적 기반)
- **정규화:** L2 정규화 적용 (norm = 1)
- **차원:** 1536 (Google Generative AI Embeddings 기본값)

### Raw → Approved 이동 과정

1. 사용자가 이동할 문서의 인덱스 배열 제공
2. Raw에서 해당 문서 추출
3. 문서를 재임베딩 (새로운 벡터 생성)
4. Approved에 추가
5. Raw에서 제거
6. 상태 반환

**주의:** Raw 저장소의 FAISS 인덱스는 현재 완전히 동기화되지 않습니다. 대신 문서 메타데이터 리스트는 정확하게 유지됩니다.

## 설정

### `app/config.py`

```python
SIMILARITY_THRESHOLD = 0.72  # 웹 검색 결과 저장 기준 점수
```

이 값 이상의 재순위 점수를 가진 웹 검색 결과만 Raw 저장소에 저장됩니다.

## 테스트

### 로컬 테스트 실행

```bash
python test_raw_approved.py
```

### API 테스트

```bash
# 1. 서버 시작
uvicorn app.main:app --reload

# 2. 상태 조회
curl http://localhost:8000/api/status

# 3. Raw 검색
curl -X POST http://localhost:8000/api/raw/search \
  -H "Content-Type: application/json" \
  -d '{"query": "검색어", "top_k": 5}'

# 4. 승인 이동
curl -X POST http://localhost:8000/api/raw/approve \
  -H "Content-Type: application/json" \
  -d '{"indices": [0, 1]}'
```

## 제한사항 및 향후 개선사항

### 현재 제한사항

1. **메모리 기반 저장:** 서버 재시작 시 데이터 손실
   - 개선: 디스크 저장소 연동 (SQLite, MongoDB 등)

2. **FAISS 인덱스 동기화:** Raw 저장소에서 문서 제거 시 FAISS 인덱스와 메타데이터 리스트 불일치 가능
   - 개선: IDMap 기반 FAISS 또는 벡터 데이터베이스 (Pinecone, Weaviate 등) 사용

3. **배치 작업 미지원:** 한 번에 하나의 문서만 처리
   - 개선: 배치 API 추가

### 향후 개선 방향

- [ ] 데이터 영속성 (디스크 저장)
- [ ] 부분 벡터 삭제 지원
- [ ] 배치 승인 최적화
- [ ] 타임스탬프 기반 필터링
- [ ] 사용자별 승인 권한 관리
- [ ] 승인 히스토리 추적
- [ ] Web UI 대시보드

## 호환성

- 기존 코드와 **완벽한 하위 호환성** 유지
- 기본값으로 Approved 저장소 사용
- Raw 저장소 기능은 선택적 사용
