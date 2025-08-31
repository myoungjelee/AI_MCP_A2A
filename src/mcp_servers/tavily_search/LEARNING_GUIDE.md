# 🎯 `tavily_search` MCP 서버 학습 가이드

**복잡한 AI 기능 대신 깔끔한 코드 구조와 효율적인 검색 알고리즘을 보여주는 MCP 서버**

---

## 📋 **1. 전체 구조 이해**

### **파일 구성**

```
tavily_search/
├── __init__.py      # 모듈 초기화 및 export
├── client.py        # 검색 클라이언트 (핵심 로직)
├── server.py        # FastMCP 서버 (도구 등록)
└── LEARNING_GUIDE.md # 이 학습 가이드
```

### **아키텍처 패턴**

```
사용자 요청 → FastMCP 서버 → 검색 클라이언트 → 검색 결과 반환
```

---

## 🏗️ **2. 핵심 클래스 분석**

### **`TavilySearchClient` - 검색 엔진**

```python
class TavilySearchClient(BaseMCPClient):
    """검색 시스템 MCP 클라이언트 (개발 기술 중심)"""
```

**주요 특징**:

- **BaseMCPClient 상속**: MCP 표준 준수
- **비동기 처리**: `async/await` 패턴
- **캐싱 시스템**: 메모리 캐시 + TTL (5분)
- **재시도 로직**: 지수 백오프 (최대 3회)

---

## ⚡ **3. 핵심 기술 구현**

### **3-1. 캐싱 시스템**

```python
def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
    """캐시 키 생성"""
    import hashlib

    key_data = f"{operation}:{str(sorted(params.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def _is_cache_valid(self, cache_key: str) -> bool:
    """캐시 유효성 검사"""
    if cache_key not in self._cache_timestamps:
        return False

    age = datetime.now() - self._cache_timestamps[cache_key]
    return age.total_seconds() < self.cache_ttl
```

**학습 포인트**:

- **해시 기반 키 생성**: 파라미터 순서 무관하게 동일한 키 생성
- **TTL 기반 만료**: 5분(300초) 기반 캐시 무효화
- **메모리 효율성**: 간단한 딕셔너리 구조

---

### **3-2. 재시도 로직**

```python
async def _retry_with_backoff(self, func, *args, **kwargs):
    """지수 백오프를 사용한 재시도 로직"""
    for attempt in range(self.max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == self.max_retries - 1:
                raise

            delay = self.retry_delay * (2**attempt)
            self.logger.warning(
                f"재시도 {attempt + 1}/{self.max_retries}, {delay}초 후 재시도: {e}"
            )
            await asyncio.sleep(delay)
```

**학습 포인트**:

- **지수 백오프**: 1초 → 2초 → 4초로 증가
- **최대 재시도 제한**: 3회로 무한 루프 방지
- **비동기 대기**: `asyncio.sleep()` 사용

---

### **3-3. 데이터 구조**

```python
@dataclass
class SearchResult:
    """검색 결과 구조"""

    title: str
    url: str
    content: str
    score: float
    published_date: datetime
    source: str
```

**학습 포인트**:

- **@dataclass**: 자동으로 `__init__`, `__repr__` 생성
- **타입 힌트**: 명시적 타입 선언으로 가독성 향상
- **불변성**: 데이터 변경 방지

---

## 🚀 **4. FastMCP 서버 구현**

### **4-1. 서버 초기화**

```python
class TavilySearchMCPServer:
    def __init__(self, port: int = 3020, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.mcp = FastMCP("search_system")
        self.mcp.description = (
            "웹 검색, 뉴스 검색, 금융 정보 검색을 위한 MCP 서버 (개발 기술 중심)"
        )
```

**학습 포인트**:

- **FastMCP 인스턴스**: MCP 서버의 핵심
- **설정 주입**: 포트, 호스트를 파라미터로 받음
- **명확한 설명**: 서버의 역할을 명시

---

### **4-2. 도구 등록**

```python
def _register_tools(self):
    """MCP 도구들을 등록합니다."""

    @self.mcp.tool()
    async def search_web(query: str, max_results: int = 10) -> Dict[str, Any]:
        """웹 검색 수행 (캐싱 + 재시도 로직)"""
        try:
            result = await self.search_client.search_web(query, max_results)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "웹 검색에 실패했습니다"
            }
```

**학습 포인트**:

- **@self.mcp.tool()**: FastMCP 도구 등록 데코레이터
- **비동기 함수**: `async def`로 비동기 처리
- **에러 처리**: try-catch로 안전한 응답 반환

---

## 🔍 **5. 실제 검색 기능**

### **5-1. 웹 검색**

```python
async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
    """웹 검색 수행 (캐싱 + 재시도 로직)"""
    # 캐시 확인 → 실제 검색 → 결과 반환
    return {
        "success": True,
        "data": results,
        "source": "fresh",  # 또는 "cache"
        "message": f"'{query}' 웹 검색 완료"
    }
```

### **5-2. 뉴스 검색**

```python
async def search_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
    """뉴스 검색 수행 (캐싱 + 재시도 로직)"""
    # 뉴스 전용 검색 로직
    # 시간 기반 정렬 (최신 뉴스 우선)
```

### **5-3. 금융 정보 검색**

```python
async def search_finance(self, query: str, max_results: int = 10) -> Dict[str, Any]:
    """금융 정보 검색 수행 (캐싱 + 재시도 로직)"""
    # 금융 전용 검색 로직
    # 시장 정보, 분석 리포트 등
```

---

## 📚 **6. 학습 순서 가이드**

### **1단계: 기본 구조 이해**

1. `__init__.py` - 모듈 구조 파악
2. `server.py` - FastMCP 서버 구조
3. `client.py` - 클라이언트 클래스 구조

### **2단계: 핵심 기술 학습**

1. **캐싱 시스템**: `_get_cache_key`, `_is_cache_valid`
2. **재시도 로직**: `_retry_with_backoff`
3. **데이터 구조**: `SearchResult`, `SearchError`

### **3단계: 실제 구현 패턴**

1. **비동기 처리**: `async/await` 패턴
2. **에러 처리**: 커스텀 예외와 로깅
3. **FastMCP 통합**: 도구 등록과 서버 실행

---

## 🔧 **7. 실습 예제**

### **7-1. 새로운 검색 타입 추가**

```python
async def search_images(self, query: str, max_results: int = 10) -> Dict[str, Any]:
    """이미지 검색 추가 예제"""
    # 1. 캐시 키 생성
    cache_key = self._get_cache_key("search_images", {"query": query, "max_results": max_results})

    # 2. 캐시 확인
    if self._is_cache_valid(cache_key):
        return {"success": True, "data": self._cache[cache_key], "source": "cache"}

    # 3. 실제 검색 로직 구현
    # 4. 캐시 업데이트
    # 5. 결과 반환
```

### **7-2. 서버에 도구 추가**

```python
@self.mcp.tool()
async def search_images(query: str, max_results: int = 10) -> Dict[str, Any]:
    """이미지 검색 수행"""
    try:
        result = await self.search_client.search_images(query, max_results)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## 🎯 **8. 핵심 학습 포인트**

### **개발 기술 어필**

1. **캐싱**: 성능 최적화 (5분 TTL)
2. **재시도**: 안정성 향상 (3회 최대)
3. **비동기**: 동시성 처리
4. **에러 처리**: 견고한 시스템

### **코드 품질**

1. **타입 힌트**: 명시적 타입 선언
2. **한글 주석**: 이해하기 쉬운 설명
3. **단일 책임**: 함수별 명확한 역할
4. **일관성**: 통일된 코딩 스타일

---

## 🚀 **9. 다음 단계 학습**

**이 코드를 완벽히 이해한 후**:

1. **다른 MCP 서버 분석**: `stock_analysis`, `naver_news` 등
2. **A2A 에이전트 구현**: 에이전트 간 통신
3. **LangGraph 워크플로우**: 복잡한 작업 흐름
4. **Docker 컨테이너화**: 배포 및 운영

---

## 💡 **10. 디버깅 팁**

### **캐시 디버깅**

```python
# 캐시 상태 확인
print(f"캐시 키: {cache_key}")
print(f"캐시 존재: {cache_key in self._cache}")
print(f"캐시 유효: {self._is_cache_valid(cache_key)}")
```

### **재시도 로직 디버깅**

```python
# 재시도 횟수 확인
print(f"현재 재시도: {attempt + 1}/{self.max_retries}")
print(f"대기 시간: {delay}초")
```

---

## 📖 **11. 참고 자료**

- **FastMCP 문서**: [FastMCP 공식 문서](https://github.com/fastmcp/fastmcp)
- **Python asyncio**: [Python 공식 문서](https://docs.python.org/3/library/asyncio.html)
- **MCP 프로토콜**: [MCP 공식 문서](https://modelcontextprotocol.io/)

---

**이제 이 학습 가이드를 참고해서 코드를 차근차근 학습해보세요!** 🎯✨

**궁금한 점이나 추가 설명이 필요한 부분이 있으면 언제든 말씀해주세요!** 📚💬
