# AgenticRAG 메타정보 활용 개선 - 변경 요약

## 목표
문서와 검색 정보의 메타정보(제목, 연도, 저자, 출처 등)를 더 풍부하게 활용하여 RAG 시스템의 답변 품질 향상

---

## 1. DocumentMetadata 스키마 확장 (`app/schemas/document.py`)

### 변경 사항
기존의 최소 메타정보에서 확장된 메타정보 구조로 개선

**추가된 필드들:**

| 분류 | 필드명 | 타입 | 설명 |
|------|--------|------|------|
| 기본 출처 | `source` | Optional[str] | 출처명 (예: 교육청 지침) |
| | `source_url` | Optional[str] | 문서 URL |
| | `domain` | Optional[str] | 도메인 정보 |
| 문서 정보 | `title` | Optional[str] | 문서 제목 |
| | `author` | Optional[str] | 저자/작성자 |
| | `year` | Optional[int] | 발행 연도 |
| | `publish_date` | Optional[str] | 발행일 |
| | `description` | Optional[str] | 문서 설명 |
| | `category` | Optional[str] | 카테고리/분류 |
| 관리 정보 | `collected_at` | Optional[datetime] | 수집 시간 |
| | `approved` | Optional[bool] | 승인 여부 |
| | `embedding_model` | Optional[str] | 임베딩 모델 |
| 추가 정보 | `language` | Optional[str] | 언어 |
| | `page_number` | Optional[int] | 페이지 번호 |
| | `section` | Optional[str] | 섹션명 |
| | `tags` | Optional[list[str]] | 태그 목록 |

### 사용 예시
```python
metadata = {
    "title": "학교 태블릿 공동구매 승인 절차",
    "author": "교육청 학생복지과",
    "year": 2024,
    "source": "교육청 지침",
    "category": "교육 정책",
    "section": "학용품 구매",
    "tags": ["태블릿", "공동구매", "승인"]
}
```

---

## 2. answer_node 개선 (`app/nodes/answer_node.py`)

### 변경 사항
메타정보를 포함한 구조화된 context 생성

**주요 기능:**
- `_format_document_with_metadata()` 함수 추가: 문서와 메타정보를 포맷팅
- 메타정보 헤더 섹션 구성 (제목, 저자, 연도, 출처 등)
- 신뢰도 스코어 표시
- 문서 내용과 메타정보의 명확한 구분

### Context 포맷 예시
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
학교 태블릿 공동구매는 교육청 승인이 필요하다.

---

[메타정보]
제목: 나라장터를 이용한 학교 전자기기 공동구매 가이드
저자: 조달청
연도: 2024
출처: 조달청
카테고리: 조달 가이드
신뢰도: 0.892

[내용]
조달청 나라장터를 통해 학교 전자기기 공동구매가 가능하다.
```

### 프롬프트 개선
- 메타정보를 고려하여 신뢰도 높은 정보를 우선으로 답변
- LLM에게 메타정보 활용 지침 제공

---

## 3. web_search_node 개선 (`app/services/web/search_service.py`)

### 변경 사항
Tavily 웹 검색 결과에서 메타정보 추출 및 구조화

**추가된 기능:**
- `_extract_metadata_from_web_result()` 함수: 웹 결과에서 메타정보 추출
- 웹 검색 결과를 `{document, metadata, score}` 구조로 통일

**추출되는 메타정보:**
- `title`: 검색 결과 제목
- `source_url`: 페이지 URL
- `source`: 출처 도메인
- `description`: 검색 결과 설명
- `domain`: 도메인 추출
- `category`: "web_search"로 자동 설정

### 반환 구조 변경
**기존:**
```python
[
    {"title": "...", "url": "...", "content": "..."},
    ...
]
```

**개선 후:**
```python
[
    {
        "document": "...",  # 실제 콘텐츠
        "metadata": {
            "title": "...",
            "source_url": "...",
            "source": "...",
            "description": "...",
            "domain": "...",
            "category": "web_search"
        },
        "score": 0.xxx
    },
    ...
]
```

---

## 4. ingest_service 개선 (`app/services/vector/ingest_service.py`)

### 변경 사항
메타정보 전달 기능 강화

**새로운 파라미터:**
```python
async def ingest_document(text, metadata=None):
    """
    Args:
        text: 문서 내용
        metadata: 딕셔너리 (모든 청크에 동일 적용) 또는 리스트 (청크별 개별 메타정보)
    """
```

**사용 예시:**

1. 동일 메타정보를 모든 청크에 적용:
```python
await ingest_document(
    text=document_content,
    metadata={
        "title": "교육청 지침",
        "author": "교육청",
        "year": 2024,
        "source": "교육청"
    }
)
```

2. 청크별 개별 메타정보:
```python
metadata_list = [
    {"title": "교육청 지침", "section": "장비 구매", ...},
    {"title": "교육청 지침", "section": "네트워크 관리", ...},
    ...
]
await ingest_document(text=content, metadata=metadata_list)
```

---

## 5. 테스트 파일 개선

### test_ingest.py
**개선 사항:**
- 확장된 메타정보 구조를 포함한 예시 제공
- 모든 필드(title, author, year, source, category, section, tags)를 활용한 예시
- 성공 메시지 개선

**메타정보 예시:**
```python
metadata = [
    {
        "source": "교육청 지침",
        "title": "학교 태블릿 공동구매 승인 절차",
        "author": "교육청 학생복지과",
        "year": 2024,
        "category": "교육 정책",
        "section": "학용품 구매",
        "tags": ["태블릿", "공동구매", "승인"]
    },
    # ... 추가 항목들
]
```

### test_retrieval.py
**개선 사항:**
- 메타정보를 구조화된 형식으로 표시
- 각 필드별로 라벨을 붙여 명확한 출력
- 점수를 소수점 4자리로 표시하여 정밀성 향상

**출력 예시:**
```
=== METADATA ===
제목: 학교 태블릿 공동구매 승인 절차
저자: 교육청 학생복지과
연도: 2024
출처: 교육청 지침
카테고리: 교육 정책
섹션: 학용품 구매
태그: 태블릿, 공동구매, 승인
```

---

## 사용 흐름

### 1. 문서 수집 및 저장
```python
# 메타정보와 함께 문서 수집
await ingest_document(
    text=document_text,
    metadata={
        "title": "...",
        "author": "...",
        "year": 2024,
        "source": "...",
        "category": "...",
        ...
    }
)
```

### 2. 검색 수행
```
# RAG 모드 (기존 문서에서 검색)
- retrieve_node: 유사도로 상위 k개 검색
- rerank_node: 재순위 매김 (메타정보 포함)

# WEB 모드 (웹 검색)
- web_search_node: Tavily에서 검색 (메타정보 자동 추출)
- web_rerank_node: 재순위 매김 (메타정보 포함)
```

### 3. 답변 생성
```
answer_node에서:
- 검색 결과의 메타정보를 포함한 context 구성
- LLM에 메타정보 고려 지침 제공
- 신뢰도 높은 정보 우선 활용
```

---

## 이점

1. **신뢰도 향상**: 메타정보(출처, 저자, 연도)로 정보 신뢰성 판단 용이
2. **맥락 이해**: 제목, 카테고리, 섹션으로 문서 맥락 파악
3. **추적성 개선**: 저자, 출처, 링크로 정보 추적 가능
4. **유연성**: 다양한 메타정보 필드 지원
5. **확장성**: 새로운 메타정보 필드 추가 용이

---

## 호환성

- 기존 코드와 완벽한 하위 호환성 유지
- `metadata`가 없는 경우 자동으로 빈 딕셔너리 처리
- 선택적 필드로 점진적 마이그레이션 가능

---

## 다음 단계 (제안)

1. **메타정보 검증**: 수집된 메타정보의 정확성 검증
2. **메타정보 인덱싱**: 메타정보로 추가 검색 지원
3. **메타정보 수집 자동화**: 문서 URL에서 자동으로 메타정보 추출
4. **메타정보 필터링**: 사용자 설정에 따른 필터링
5. **메타정보 시각화**: 웹 UI에서 메타정보 표시
