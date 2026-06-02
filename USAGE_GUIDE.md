# AgenticRAG 메타정보 활용 가이드

## 개요

AgenticRAG 시스템이 문서 및 웹 검색 결과의 다양한 메타정보(제목, 연도, 저자 등)를 활용하여 더 정확하고 신뢰할 수 있는 답변을 생성하도록 개선되었습니다.

---

## 1. 기본 사용법

### 메타정보와 함께 문서 수집하기

#### 1.1 동일한 메타정보를 모든 청크에 적용

```python
from app.services.vector.ingest_service import ingest_document

# 교육청 지침 문서 수집
await ingest_document(
    text="""
    학교 태블릿 공동구매는 교육청 승인이 필요하다.
    1. 구매 신청서 작성
    2. 교육청에 제출
    3. 승인 대기
    """,
    metadata={
        "title": "학교 태블릿 공동구매 승인 절차",
        "author": "교육청 학생복지과",
        "year": 2024,
        "source": "교육청 지침",
        "category": "교육 정책",
        "section": "학용품 구매",
        "tags": ["태블릿", "공동구매", "승인"]
    }
)
```

#### 1.2 청크별 개별 메타정보 적용

```python
# 긴 문서를 청크로 나누어 각 청크에 다른 메타정보 적용
chunks = [
    "학교 태블릿 공동구매는 교육청 승인이 필요하다.",
    "조달청 나라장터를 통해 학교 전자기기 공동구매가 가능하다.",
    "연간 구매 예산은 학교 운영 규칙에 따라 결정된다."
]

metadata_list = [
    {
        "title": "학교 태블릿 공동구매 승인 절차",
        "section": "승인 프로세스",
        "year": 2024,
    },
    {
        "title": "학교 태블릿 공동구매 승인 절차",
        "section": "구매 방법",
        "year": 2024,
    },
    {
        "title": "학교 태블릿 공동구매 승인 절차",
        "section": "예산 관리",
        "year": 2024,
    }
]

await ingest_document(text="\n".join(chunks), metadata=metadata_list)
```

---

## 2. 메타정보 필드 설명

### 필수 필드 (최소)
- `title`: 문서의 제목
- `source`: 출처 정보 (예: "교육청", "조달청", "웹사이트명")

### 권장 필드
- `author`: 저자 또는 작성 기관
- `year`: 발행 연도 (신뢰도 판단에 중요)
- `category`: 문서 카테고리 (검색 필터링에 유용)

### 선택 필드
- `publish_date`: 정확한 발행일 (연도가 없을 경우)
- `section`: 문서 내 섹션명
- `page_number`: 페이지 번호 (특정 출처에서 유용)
- `description`: 문서 간단 설명
- `language`: 문서 언어
- `tags`: 태그 목록 (카테고리화된 검색)
- `source_url`: 문서 URL
- `domain`: 도메인 정보

---

## 3. 검색 및 답변 생성 흐름

### 3.1 RAG 모드 (기존 문서에서 검색)

```python
# 시스템 그래프에서 자동으로 처리됨
# 1. retrieve_node: 유사도로 상위 k개 검색
# 2. rerank_node: 재순위 매김 (메타정보 포함)
# 3. answer_node: 메타정보를 포함한 context 생성

# 사용자는 질문만 제시
state = {"question": "학교 태블릿 구매 승인 절차가 어떻게 되나?"}
```

### 3.2 웹 검색 모드

```python
# 웹 검색 사용
state = {
    "question": "최신 태블릿 공동구매 정책",
    "use_web_search": True  # (설정에 따라)
}

# 자동으로 처리:
# 1. web_search_node: Tavily API로 검색 (메타정보 자동 추출)
# 2. web_rerank_node: 재순위 매김
# 3. answer_node: 웹 결과 메타정보 포함하여 답변
```

---

## 4. 답변 생성 시 메타정보 활용

### 4.1 LLM에게 제공되는 Context 형식

```
[메타정보]
제목: 학교 태블릿 공동구매 승인 절차
저자: 교육청 학생복지과
연도: 2024
출처: 교육청 지침
카테고리: 교육 정책
섹션: 학용품 구매
신뢰도: 0.925

[내용]
학교 태블릿 공동구매는 교육청 승인이 필요하다...

---

[메타정보]
제목: 나라장터를 이용한 학교 전자기기 공동구매 가이드
저자: 조달청
연도: 2024
출처: 조달청
카테고리: 조달 가이드
신뢰도: 0.892

[내용]
조달청 나라장터를 통해 학교 전자기기 공동구매가 가능하다...
```

### 4.2 LLM이 고려하는 사항

LLM은 다음 지침을 따릅니다:
- 메타정보의 연도를 확인하여 최신 정보 우선 사용
- 공식 출처(정부기관, 교육청)를 비공식 출처보다 우선
- 신뢰도 스코어가 높은 문서를 우선으로 참고
- 저자/조직의 신뢰도를 고려

---

## 5. 실제 예시

### 예시 1: 교육 정책 정보

**입력:**
```python
documents = [
    {
        "text": "학교 태블릿 공동구매는 교육청 승인이 필요하다.",
        "metadata": {
            "title": "학교 태블릿 공동구매 승인 절차",
            "author": "교육청 학생복지과",
            "year": 2024,
            "source": "교육청 지침",
            "category": "교육 정책"
        }
    },
    {
        "text": "조달청 나라장터를 통해 학교 전자기기 공동구매가 가능하다.",
        "metadata": {
            "title": "나라장터 이용 가이드",
            "author": "조달청",
            "year": 2023,  # 이전 연도
            "source": "조달청",
            "category": "조달 정보"
        }
    }
]

# 배치 수집
for doc in documents:
    await ingest_document(text=doc["text"], metadata=doc["metadata"])
```

**질문:**
```
학교 태블릿 구매 승인 절차가 어떻게 되나?
```

**답변 (메타정보 활용):**
```
최신 정보(2024년 교육청 지침)에 따르면, 학교 태블릿 공동구매는 교육청 승인이 필요합니다.
교육청 학생복지과에서 제시한 절차는 다음과 같습니다...

참고로, 실제 구매는 조달청 나라장터를 통해 진행할 수 있습니다(조달청 2023년 기준).
```

### 예시 2: 웹 검색과 메타정보

**웹 검색 결과 (자동 추출된 메타정보):**
```python
[
    {
        "document": "2024년 교육부 발표 새로운 디지털 교육 정책...",
        "metadata": {
            "title": "2024년 디지털 교육 전환 정책",
            "source": "교육부 뉴스",
            "source_url": "https://www.moe.go.kr/news",
            "description": "교육부가 발표한 2024년 새로운 디지털 교육 정책",
            "category": "web_search"
        },
        "score": 0.945
    },
    {
        "document": "학교 IT 기기 구매 팁 및 가이드...",
        "metadata": {
            "title": "학교 기기 구매 완벽 가이드",
            "source": "IT 전문 블로그",
            "source_url": "https://example.com/guide",
            "description": "학교에서 IT 기기를 구매할 때 알아야 할 사항",
            "category": "web_search"
        },
        "score": 0.823
    }
]
```

---

## 6. 테스트 및 검증

### 6.1 기본 테스트 실행

```bash
# 1. 메타정보와 함께 문서 수집
python test_ingest.py

# 2. 검색 결과 메타정보 확인
python test_retrieval.py
```

### 6.2 출력 확인

test_retrieval.py 실행 후:
```
=== SEARCH RESULTS ===

[Result 1]
SCORE: 0.9250

=== METADATA ===
제목: 학교 태블릿 공동구매 승인 절차
저자: 교육청 학생복지과
연도: 2024
출처: 교육청 지침
카테고리: 교육 정책
섹션: 학용품 구매
태그: 태블릿, 공동구매, 승인

=== DOCUMENT CONTENT ===
학교 태블릿 공동구매는 교육청 승인이 필요하다.
```

---

## 7. 고급 활용법

### 7.1 메타정보 기반 필터링 (향후 기능)

```python
# 예정: 특정 연도 이후의 문서만 사용
search_results = retrieve_documents(
    query=question,
    filters={"year": {"gte": 2024}}
)

# 예정: 특정 출처만 사용
search_results = retrieve_documents(
    query=question,
    filters={"source": {"in": ["교육청", "조달청"]}}
)
```

### 7.2 메타정보 기반 재순위 (향후 기능)

```python
# 예정: 메타정보의 신뢰도를 재순위 스코어에 반영
# 예: 공식 기관 출처에 높은 가중치 부여
```

### 7.3 메타정보 자동 추출 (향후 기능)

```python
# 예정: URL에서 자동으로 메타정보 추출
from app.services.metadata_extractor import extract_metadata

url = "https://example.com/document"
metadata = await extract_metadata(url)
# {"title": "...", "author": "...", "publish_date": "...", ...}
```

---

## 8. 문제 해결

### Q: 메타정보가 없는데도 작동하나요?

**A:** 네, 완벽한 하위 호환성이 있습니다.
```python
# 메타정보 없이 사용 가능 (기존 방식)
await ingest_document(text=content)
# -> 자동으로 메타정보는 빈 딕셔너리로 처리됨
```

### Q: 메타정보를 나중에 업데이트할 수 있나요?

**A:** 현재는 문서 재수집 필요합니다:
```python
# 1. 기존 인덱스 초기화
# 2. 업데이트된 메타정보와 함께 다시 수집
await ingest_document(text=content, metadata=updated_metadata)
```

### Q: 특정 메타정보만 사용할 수 있나요?

**A:** 네, 필요한 필드만 사용하면 됩니다:
```python
# 최소 메타정보 (필수)
metadata = {
    "title": "문서 제목",
    "source": "출처"
}

# 상세 메타정보 (선택)
metadata = {
    "title": "문서 제목",
    "source": "출처",
    "author": "저자",
    "year": 2024,
    # ... 추가 필드들
}
```

---

## 9. 모범 사례 (Best Practices)

### DO ✅
- 신뢰할 수 있는 출처 정보 제공
- 정확한 발행 연도 기록
- 문서 카테고리 분류
- 청크별 섹션 정보 추가
- 필요한 모든 메타정보 채우기

### DON'T ❌
- 잘못된 연도 또는 저자 정보
- 너무 일반적인 제목 (예: "문서 1")
- 일관성 없는 출처 명명
- 메타정보 필드 값을 비워두기
- 메타정보 형식 불일치

---

## 10. 버전 호환성

| 기능 | 지원 |
|------|------|
| 메타정보 없이 사용 | ✅ |
| 기본 메타정보 필드 | ✅ |
| 확장 메타정보 필드 | ✅ |
| 자동 메타정보 추출 | 예정 |
| 메타정보 기반 필터링 | 예정 |

---

더 궁금한 점이 있으시면 ENHANCEMENT_SUMMARY.md를 참고해주세요.
