# 콘텐츠 수집 시스템 MCP 서버 학습 가이드

## 🎯 **학습 목표**

이 가이드를 통해 **ContentCollectionClient**를 사용하여 콘텐츠를 수집하고, **개발 기술 중심의 포트폴리오**를 구축할 수 있습니다.

## 🏗️ **아키텍처 개요**

### **핵심 컴포넌트**

- **ContentCollectionClient**: 콘텐츠 수집 클라이언트
- **ContentCollectionMCPServer**: MCP 서버 구현체
- **ContentItem**: 콘텐츠 아이템 데이터 클래스
- **ContentCollectionError**: 에러 처리 클래스

### **기술 스택**

- **FastMCP**: MCP 서버 프레임워크
- **BaseMCPClient**: MCP 클라이언트 기본 클래스
- **asyncio**: 비동기 처리
- **dataclass**: 데이터 구조화

## 🚀 **시작하기**

### **1. 클라이언트 초기화**

```python
from src.mcp_servers.naver_news.client import ContentCollectionClient

# 클라이언트 생성
client = ContentCollectionClient("my_collector")
```

### **2. 사용 가능한 도구 확인**

```python
# 도구 목록 조회
tools = await client.list_tools()
print(f"사용 가능한 도구: {len(tools)}개")

for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

## 🔧 **주요 기능 사용법**

### **1. 콘텐츠 수집**

```python
# 쿼리 기반 콘텐츠 수집
result = await client.collect_content("AI 기술", max_items=20, category="technology")

if result["success"]:
    print(f"수집된 콘텐츠: {result['total_collected']}개")
    print(f"카테고리: {result['category']}")
    print(f"수집 시간: {result['collection_timestamp']}")

    for item in result["items"]:
        print(f"- {item['title']} (관련도: {item['relevance_score']:.2f})")
else:
    print(f"콘텐츠 수집 실패: {result['error']}")
```

### **2. 콘텐츠 파싱**

```python
# 수집된 콘텐츠 파싱 및 분석
content_items = result["items"]
parsing_result = await client.parse_content(content_items)

if parsing_result["success"]:
    print(f"파싱 완료: {parsing_result['total_parsed']}개")
    print(f"고유 키워드: {parsing_result['unique_keywords']}개")

    for item in parsing_result["parsed_items"]:
        print(f"- {item['title']}")
        print(f"  요약: {item['summary']}")
        print(f"  키워드: {', '.join(item['keywords'])}")
else:
    print(f"파싱 실패: {parsing_result['error']}")
```

### **3. 콘텐츠 저장**

```python
# 파싱된 콘텐츠 저장
storage_result = await client.store_content(parsing_result, storage_type="database")

if storage_result["success"]:
    storage_info = storage_result["storage_info"]
    print(f"저장 완료: {storage_info['storage_id']}")
    print(f"저장 타입: {storage_info['storage_type']}")
    print(f"저장된 항목: {storage_info['total_items']}개")
else:
    print(f"저장 실패: {storage_result['error']}")
```

## 📊 **데이터 구조 이해**

### **ContentItem 구조**

```python
@dataclass
class ContentItem:
    title: str              # 콘텐츠 제목
    content: str            # 콘텐츠 내용
    url: str                # 콘텐츠 URL
    published_at: datetime  # 발행 시간
    source: str             # 콘텐츠 소스
    category: str           # 콘텐츠 카테고리
    relevance_score: float  # 관련도 점수 (0.0 ~ 1.0)
    keywords: List[str]     # 키워드 목록
```

### **응답 구조**

```python
# 콘텐츠 수집 성공 응답
{
    "success": True,
    "query": "AI 기술",
    "total_collected": 10,
    "category": "technology",
    "items": [
        {
            "title": "AI 기술 관련 콘텐츠 1",
            "content": "이것은 AI 기술에 대한 실제 콘텐츠 내용입니다...",
            "url": "https://example.com/content/AI_기술_1",
            "published_at": "2024-01-01T10:00:00",
            "source": "콘텐츠 수집 시스템",
            "category": "technology",
            "relevance_score": 0.9,
            "keywords": ["AI 기술", "기술", "개발", "소프트웨어"]
        }
    ],
    "collection_timestamp": "2024-01-01T10:00:00"
}

# 콘텐츠 파싱 성공 응답
{
    "success": True,
    "total_parsed": 10,
    "unique_keywords": 15,
    "parsed_items": [
        {
            "id": "item_0",
            "title": "AI 기술 관련 콘텐츠 1",
            "summary": "이것은 AI 기술에 대한 실제 콘텐츠 내용입니다...",
            "keywords": ["AI", "기술", "개발"],
            "word_count": 25,
            "parsed_at": "2024-01-01T10:00:00"
        }
    ],
    "parsing_timestamp": "2024-01-01T10:00:00"
}
```

## 🔄 **고급 기능**

### **1. 캐싱 활용**

```python
# 캐시는 자동으로 관리됩니다
# 첫 번째 호출: 실제 콘텐츠 수집
result1 = await client.collect_content("AI 기술", max_items=20)

# 두 번째 호출: 캐시에서 반환 (빠름)
result2 = await client.collect_content("AI 기술", max_items=20)

# 결과는 동일합니다
assert result1 == result2
```

### **2. 재시도 로직**

```python
# 네트워크 오류 시 자동 재시도
# 기본 설정: 최대 3회, 지수 백오프 (1초 → 2초 → 4초)
try:
    result = await client.collect_content("AI 기술", max_items=20)
except Exception as e:
    print(f"최대 재시도 후 실패: {e}")
```

### **3. 키워드 추출**

```python
# 내부적으로 키워드 추출 기능 제공
# 3글자 이상의 단어를 키워드로 자동 추출
# 중복 제거 및 최대 키워드 수 제한 (기본: 5개)
```

## 🧪 **테스트 작성**

### **단위 테스트 예시**

```python
import pytest
from src.mcp_servers.naver_news.client import ContentCollectionClient

@pytest.mark.asyncio
async def test_content_collection_success():
    """[콘텐츠 수집] 유효한 쿼리로 콘텐츠 수집이 성공한다"""
    # Given: 유효한 쿼리
    client = ContentCollectionClient("test_collector")
    query = "AI 기술"

    # When: 콘텐츠 수집 실행
    result = await client.collect_content(query, max_items=10)

    # Then: 수집 성공
    assert result["success"] is True
    assert "items" in result
    assert result["query"] == query
    assert result["total_collected"] > 0

@pytest.mark.asyncio
async def test_content_parsing_success():
    """[콘텐츠 파싱] 유효한 콘텐츠로 파싱이 성공한다"""
    # Given: 수집된 콘텐츠와 클라이언트
    client = ContentCollectionClient("test_collector")
    content_items = [
        {
            "title": "테스트 제목",
            "content": "테스트 콘텐츠 내용입니다.",
            "url": "https://test.com",
            "published_at": "2024-01-01T10:00:00",
            "source": "테스트",
            "category": "test",
            "relevance_score": 0.9,
            "keywords": ["테스트", "콘텐츠"]
        }
    ]

    # When: 콘텐츠 파싱 실행
    result = await client.parse_content(content_items)

    # Then: 파싱 성공
    assert result["success"] is True
    assert result["total_parsed"] == 1
    assert "parsed_items" in result
```

## 🚨 **에러 처리**

### **일반적인 에러 상황**

```python
try:
    result = await client.collect_content("", max_items=0)
except ContentCollectionError as e:
    print(f"콘텐츠 수집 에러: {e}")
    print(f"에러 코드: {e.error_code}")
    if e.details:
        print(f"상세 정보: {e.details}")
```

### **에러 타입**

- **ContentCollectionError**: 일반적인 콘텐츠 수집 에러
- **ValueError**: 잘못된 파라미터
- **NetworkError**: 네트워크 연결 에러

## 📈 **성능 최적화 팁**

### **1. 배치 처리**

```python
# 여러 쿼리를 동시에 처리
queries = ["AI 기술", "머신러닝", "딥러닝"]
tasks = [client.collect_content(query, max_items=20) for query in queries]
results = await asyncio.gather(*tasks)

for query, result in zip(queries, results):
    if result["success"]:
        print(f"{query}: {result['total_collected']}개 수집")
```

### **2. 캐시 TTL 조정**

```python
# 캐시 유효 시간 조정 (기본: 5분)
client._cache_ttl = 600  # 10분으로 증가
```

### **3. 키워드 최적화**

```python
# 기본 키워드 설정으로 관련성 향상
client.default_keywords = ["AI", "머신러닝", "데이터", "개발", "기술"]
```

## 🔍 **디버깅 및 로깅**

### **로깅 설정**

```python
import logging

# 상세한 로깅 활성화
logging.basicConfig(level=logging.DEBUG)

# 클라이언트별 로깅
logger = logging.getLogger("content_collector.my_collector")
logger.setLevel(logging.DEBUG)
```

### **디버깅 정보**

```python
# 캐시 상태 확인
print(f"캐시된 항목: {len(client._cache)}")
print(f"캐시 키들: {list(client._cache.keys())}")

# 기본 설정 확인
print(f"최대 아이템 수: {client.max_items_per_request}")
print(f"기본 타임아웃: {client.default_timeout}초")
print(f"기본 키워드: {client.default_keywords}")
```

## 🚀 **FastMCP 서버 구현**

### **서버 초기화**

```python
class ContentCollectionMCPServer:
    def __init__(self, port: int = 8050, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.mcp = FastMCP("content_collector")
        self.mcp.description = "콘텐츠 수집 시스템 - 개발 기술 중심의 MCP 서버"
```

### **도구 등록**

```python
@self.mcp.tool()
async def collect_content(query: str, max_items: int = 20, category: str = "general") -> dict[str, Any]:
    """콘텐츠 수집"""
    try:
        result = await self.client.collect_content(query=query, max_items=max_items, category=category)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "query": query}
```

## 📚 **추가 학습 자료**

### **관련 기술**

- **Model Context Protocol (MCP)**: AI 모델과 도구 간 통신 표준
- **FastMCP**: Python MCP 서버 구현 프레임워크
- **BaseMCPClient**: MCP 클라이언트 기본 클래스
- **비동기 프로그래밍**: asyncio, async/await 패턴

### **다음 단계**

- **LangGraph 에이전트**: 복잡한 워크플로우 구현
- **A2A 통신**: 에이전트 간 협업 시스템
- **Docker 컨테이너화**: 서비스 배포 및 확장

## 🎉 **성취 체크리스트**

- [ ] **ContentCollectionClient** 초기화 및 기본 사용법 숙지
- [ ] **콘텐츠 수집** 기능 활용
- [ ] **콘텐츠 파싱** 기능 활용
- [ ] **콘텐츠 저장** 기능 활용
- [ ] **캐싱 및 재시도** 로직 이해
- [ ] **에러 처리** 및 로깅 구현
- [ ] **단위 테스트** 작성 및 실행
- [ ] **성능 최적화** 기법 적용

이제 **콘텐츠 수집 시스템 MCP 서버**를 마스터하여 **개발 기술 중심의 포트폴리오**를 완성할 수 있습니다! 🚀
