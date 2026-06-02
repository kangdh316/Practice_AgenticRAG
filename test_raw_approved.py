"""
Raw/Approved 저장소 기능 테스트
"""

import asyncio
import json
from app.services.vector.ingest_service import ingest_document
from app.services.vector.retrieval_service import retrieve_documents
from app.services.vector.vector_store import get_stats


async def test_approved_storage():
    """Approved 저장소에 문서 추가 테스트"""
    print("\n=== TEST 1: Approved 저장소 테스트 ===")
    
    # approved에 문서 추가
    metadata1 = {
        "title": "Test Document 1",
        "source": "test",
        "approved": True
    }
    
    await ingest_document(
        text="이것은 테스트 문서 1입니다. 기계 학습 및 인공지능에 대한 내용입니다.",
        metadata=metadata1,
        to_approved=True
    )
    
    metadata2 = {
        "title": "Test Document 2", 
        "source": "test",
        "approved": True
    }
    
    await ingest_document(
        text="이것은 테스트 문서 2입니다. 자연어 처리에 대한 내용입니다.",
        metadata=metadata2,
        to_approved=True
    )
    
    # 상태 조회
    stats = get_stats()
    print(f"After adding to approved: {json.dumps(stats, indent=2)}")
    
    # 검색
    results = await retrieve_documents(
        question="기계 학습",
        top_k=5,
        from_approved=True
    )
    
    print(f"\nApproved 저장소 검색 결과 (query: '기계 학습'):")
    for i, result in enumerate(results):
        print(f"  [{i}] Score: {result['score']:.4f}")
        print(f"      Doc: {result['document'][:50]}...")
        print(f"      Index: {result.get('index')}")


async def test_raw_storage():
    """Raw 저장소에 문서 추가 테스트"""
    print("\n\n=== TEST 2: Raw 저장소 테스트 ===")
    
    # raw에 문서 추가
    metadata3 = {
        "title": "Raw Document 1",
        "source": "web",
        "source_type": "web_search"
    }
    
    await ingest_document(
        text="이것은 웹에서 검색된 문서입니다. 딥러닝 기술에 대해 설명합니다.",
        metadata=metadata3,
        to_approved=False
    )
    
    metadata4 = {
        "title": "Raw Document 2",
        "source": "web"
    }
    
    await ingest_document(
        text="또 다른 웹 검색 결과입니다. 신경망에 대한 내용입니다.",
        metadata=metadata4,
        to_approved=False
    )
    
    # 상태 조회
    stats = get_stats()
    print(f"After adding to raw: {json.dumps(stats, indent=2)}")
    
    # raw에서 검색
    results = await retrieve_documents(
        question="딥러닝",
        top_k=5,
        from_approved=False
    )
    
    print(f"\nRaw 저장소 검색 결과 (query: '딥러닝'):")
    for i, result in enumerate(results):
        print(f"  [{i}] Index: {result.get('index')}")
        print(f"      Score: {result['score']:.4f}")
        print(f"      Doc: {result['document'][:50]}...")
        print(f"      Meta: {result['metadata']}")


async def main():
    print("=" * 60)
    print("Raw/Approved 저장소 기능 테스트")
    print("=" * 60)
    
    try:
        await test_approved_storage()
        await test_raw_storage()
        
        # 최종 상태
        stats = get_stats()
        print(f"\n\n=== 최종 상태 ===")
        print(f"Approved: {stats['approved']['count']} 문서, {stats['approved']['index_size']} 인덱스")
        print(f"Raw: {stats['raw']['count']} 문서, {stats['raw']['index_size']} 인덱스")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
