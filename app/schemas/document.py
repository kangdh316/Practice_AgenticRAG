from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentMetadata(BaseModel):
    # 기본 출처 정보
    source_url: Optional[str] = None
    source: Optional[str] = None
    domain: Optional[str] = None
    
    # 문서 상세 정보
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    publish_date: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    
    # 메타데이터 관리 정보
    collected_at: Optional[datetime] = None
    approved: Optional[bool] = None
    embedding_model: Optional[str] = None
    
    # 추가 정보
    language: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    tags: Optional[list[str]] = None