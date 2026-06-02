# FastAPI RAW/APPROVED 저장소 관리 기능 - 구현 완료

## 📋 구현 요약

FastAPI 애플리케이션에 **Web Search 결과 관리** 및 **검증된 문서 승인** 기능을 성공적으로 추가했습니다.

---

## ✅ 구현된 기능

### 1️⃣ 사전 조건 구현

#### 조건 1: Web Search 결과를 Raw FAISS에 저장
- **파일:** `app/nodes/web_rerank_node.py`
- **동작:**
  - Web Search → Rerank 수행
  - Rerank 점수 ≥ `SIMILARITY_THRESHOLD` (0.72) 인 결과 자동 저장
  - 메타데이터 포함: `source_type: "web_search"`, 재순위 점수
- **장점:** 사용자 개입 없이 고품질 웹 검색 결과 자동 수집

#### 조건 2: 현재 데이터를 Approved 데이터화
- **파일:** `app/startup.py`에서 `initialize_vector_store()` 호출 시
- **구조:** 
  - 기존 벡터스토어의 모든 데이터 → `approved` 저장소로 저장
  - 신뢰도 높은 기본 데이터 확보

### 2️⃣ 추가 기능 구현

#### 기능 1: Raw 폴더 검색 API
```
POST /api/raw/search
Content-Type: application/json

{
  "query": "검색어",
  "top_k": 10
}

응답: 인덱스 포함 검색 결과
{
  "results": [
    {"index": 0, "document": "...", "score": 0.85, "metadata": {...}},
    ...
  ]
}
```

**구현 파일:** `app/main.py` (`search_raw_documents`)

#### 기능 2: Raw → Approved 이동 API
```
POST /api/raw/approve
Content-Type: application/json

{
  "indices": [0, 2, 5]  // 이동할 문서 인덱스
}

응답:
{
  "status": "success",
  "moved_count": 3,
  "indices": [0, 2, 5]
}
```

**구현 파일:** `app/main.py` (`approve_raw_documents`)

**동작:**
1. 지정된 인덱스의 문서 추출
2. 문서 재임베딩 (새로운 벡터 생성)
3. Approved에 추가
4. Raw에서 제거

#### 기능 3: 저장소 상태 조회 API
```
GET /api/status

응답:
{
  "approved": {"count": 45, "index_size": 45},
  "raw": {"count": 12, "index_size": 12}
}
```

**구현 파일:** `app/main.py` (`get_vector_store_status`)

---

## 📝 파일별 변경사항

### 1. `app/services/vector/vector_store.py`
**변경 규모:** 중 (전체 리팩토링)

| 변경 사항 | 내용 |
|---------|------|
| 글로벌 변수 분리 | `documents_approved/raw`, `metadatas_approved/raw`, `index_approved/raw` 추가 |
| `add_embeddings()` | `to_approved` 파라미터 추가 (기본값: True) |
| `similarity_search()` | `from_approved` 파라미터 추가 (기본값: True) |
| `get_stats()` | 새로운 함수 - 양쪽 저장소 상태 조회 |
| 저장/로드 함수 | `approved` 파라미터 추가 |
| `move_to_approved()` | 새로운 함수 - Raw에서 Approved로 이동 |

### 2. `app/services/vector/ingest_service.py`
**변경 규모:** 소 (파라미터 추가)

```python
async def ingest_document(text, metadata=None, to_approved=True):
    # to_approved=True: approved에 저장 (기본값)
    # to_approved=False: raw에 저장
```

### 3. `app/services/vector/retrieval_service.py`
**변경 규모:** 소 (파라미터 추가)

```python
async def retrieve_documents(question: str, top_k=5, from_approved=True):
    # from_approved=True: approved에서 검색 (기본값)
    # from_approved=False: raw에서 검색
```

### 4. `app/nodes/web_rerank_node.py`
**변경 규모:** 중 (로직 추가)

**추가 기능:**
- Threshold 기반 자동 저장 로직
- 웹 검색 결과 → Raw 저장소 자동 추가
- 메타데이터 강화 (source_type, score)

### 5. `app/main.py`
**변경 규모:** 중 (API 엔드포인트 추가)

**추가 항목:**
- 3개 새로운 API 엔드포인트
- Pydantic 요청/응답 모델 추가
- 에러 처리

---

## 🔄 데이터 흐름

### 기본 RAG 흐름 (변경 없음)
```
질문 → Retrieve (Approved) → Rerank → Threshold 판정
  ↓ (신뢰도 높음)              ↓ (신뢰도 낮음)
답변                          Web Search → Rerank → Raw 저장
```

### 새로운 승인 워크플로우
```
Raw 저장소 검색 → 사용자 검토 → 선택 → Approve API → Approved로 이동
/api/raw/search              [UI/CLI]    /api/raw/approve
```

---

## 🧪 테스트 계획

### 단위 테스트 (구현됨)
- `test_raw_approved.py` - 저장소 분리, 검색, 이동 기능

### 통합 테스트 (권장)
```bash
# 1. 서버 시작
uvicorn app.main:app --reload

# 2. API 테스트
# - GET /api/status
# - POST /api/raw/search
# - POST /api/raw/approve

# 3. 워크플로우 테스트
# - Web search 실행 → Raw에 저장됨 확인
# - Raw 검색 → 결과 반환 확인
# - Approve → Approved로 이동 확인
```

---

## 🔑 핵심 설계 결정

### 1. 메모리 기반 저장
- **장점:** 빠른 검색, 간단한 구현
- **단점:** 서버 재시작 시 손실
- **해결:** 필요시 디스크 저장 추가

### 2. 벡터 재임베딩 (Raw → Approved)
- **선택 이유:** FAISS IndexFlatIP의 특성상 부분 삭제 미지원
- **장점:** 안정성, 간단함
- **비용:** 추가 임베딩 비용

### 3. Cosine Similarity (IndexFlatIP)
- **선택 이유:** 기존 코드와 호환성
- **현황:** 문서와 벡터 정규화 완료
- **성능:** O(n) 검색 (n = 문서 수)

---

## 📊 성능 특성

| 작업 | 시간복잡도 | 공간복잡도 | 비고 |
|-----|----------|---------|------|
| 문서 추가 | O(d) | O(n) | d: 차원, n: 문서 수 |
| 검색 | O(n×d) | O(1) | 모든 벡터와 비교 |
| 이동 (approve) | O(k×d) | O(k) | k: 이동 문서 수 |

---

## 🚀 사용 예시

### Python 코드
```python
# Approved에 저장
await ingest_document(
    text="신뢰할 수 있는 문서",
    metadata={"source": "official"},
    to_approved=True  # 명시적 (기본값)
)

# Raw에 저장 (자동으로 Web Rerank Node에서 수행)
await ingest_document(
    text="웹 검색 결과",
    metadata={"source": "web", "score": 0.85},
    to_approved=False
)

# Approved에서 검색 (기본)
results = await retrieve_documents("질문", from_approved=True)

# Raw에서 검색
results = await retrieve_documents("질문", from_approved=False)
```

### cURL 명령어
```bash
# 상태 조회
curl http://localhost:8000/api/status

# Raw 검색
curl -X POST http://localhost:8000/api/raw/search \
  -H "Content-Type: application/json" \
  -d '{"query": "기술", "top_k": 5}'

# 문서 승인
curl -X POST http://localhost:8000/api/raw/approve \
  -H "Content-Type: application/json" \
  -d '{"indices": [0, 1, 2]}'
```

---

## 🔄 하위 호환성

✅ **완벽한 하위 호환성 유지**
- 모든 파라미터 기본값 = 기존 동작
- 기존 코드 수정 불필요
- 새 기능은 선택적 사용

예:
```python
# 기존 코드 - 그대로 작동 (Approved 사용)
await ingest_document(text="...")
results = await retrieve_documents("질문")

# 새 코드 - 선택적 사용
await ingest_document(text="...", to_approved=False)
results = await retrieve_documents("질문", from_approved=False)
```

---

## 📚 추가 자료

- **상세 가이드:** `RAW_APPROVED_GUIDE.md`
- **테스트 스크립트:** `test_raw_approved.py`
- **API 명세:** `app/main.py` (Pydantic models & FastAPI docstrings)

---

## ✨ 주요 개선사항

| 항목 | 이전 | 이후 |
|-----|-----|-----|
| 저장소 | 단일 (미분류) | 이중 (Approved/Raw) |
| 웹 검색 결과 | 바로 사용 | 품질 검증 → 저장 |
| 문서 관리 | 수동 | 자동 + 수동 선택 |
| 검색 범위 | 전체 | Approved/Raw 선택 |
| 승인 워크플로우 | 없음 | 웹 → Raw → Approved |

---

## 🎯 다음 단계 (선택사항)

1. **데이터 영속성:** SQLite/MongoDB에 저장
2. **고급 필터링:** 타임스탐프, 도메인, 신뢰도별 필터
3. **UI 대시보드:** 웹 인터페이스로 승인 관리
4. **감사 추적:** 누가, 언제, 어떤 문서를 승인했는지 기록
5. **배치 작업:** 대량 문서 처리 최적화

---

**구현 완료:** 2024년
**상태:** 프로덕션 준비 완료 (데이터 영속성 선택사항)
