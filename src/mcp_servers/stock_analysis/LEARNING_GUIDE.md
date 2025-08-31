# 🎯 `stock_analysis` MCP 서버 학습 가이드

**복잡한 주식 분석 대신 깔끔한 코드 구조와 효율적인 데이터 분석 알고리즘을 보여주는 MCP 서버**

---

## 📋 **1. 전체 구조 이해**

### **파일 구성**

```
stock_analysis/
├── __init__.py      # 모듈 초기화 및 export
├── client.py        # 데이터 분석 클라이언트 (핵심 로직)
├── server.py        # FastMCP 서버 (도구 등록)
└── LEARNING_GUIDE.md # 이 학습 가이드
```

### **아키텍처 패턴**

```
사용자 요청 → FastMCP 서버 → 데이터 분석 클라이언트 → 분석 결과 반환
```

---

## 🏗️ **2. 핵심 클래스 분석**

### **`DataAnalysisClient` - 분석 엔진**

```python
class DataAnalysisClient(BaseMCPClient):
    """데이터 분석 시스템 MCP 클라이언트 (개발 기술 중심)"""
```

**주요 특징**:

- **BaseMCPClient 상속**: MCP 표준 준수
- **비동기 처리**: `async/await` 패턴
- **캐싱 시스템**: 메모리 캐시 + TTL (5분)
- **재시도 로직**: 지수 백오프 (최대 3회)
- **실제 데이터 연동**: FinanceDataReader 사용

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

### **3-3. 데이터 분석 알고리즘**

```python
def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
    """RSI 계산"""
    if len(prices) < period + 1:
        return 50.0

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi)
```

**학습 포인트**:

- **NumPy 활용**: 효율적인 배열 연산
- **수학적 알고리즘**: RSI 공식 구현
- **에러 처리**: 데이터 부족 시 기본값 반환

---

### **3-4. 데이터 구조**

```python
@dataclass
class AnalysisResult:
    """분석 결과 구조"""
    symbol: str
    signal: str
    score: float
    confidence: float
    indicators: Dict[str, Any]
    timestamp: datetime
```

**학습 포인트**:

- **@dataclass**: 자동으로 `__init__`, `__repr__` 생성
- **타입 힌트**: 명시적 타입 선언으로 가독성 향상
- **불변성**: 데이터 변경 방지

---

## 🔍 **4. 실제 분석 기능**

### **4-1. 데이터 트렌드 분석**

```python
async def analyze_data_trends(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
    """데이터 트렌드 분석 수행 (캐싱 + 재시도 로직)"""
    # 캐시 확인 → 실제 분석 → 결과 반환
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "period": period,
            "current_price": float(current_price),
            "ma20": float(ma20),
            "ma60": float(ma60),
            "rsi": float(rsi),
            "signal": signal,  # "상승", "하락", "중립"
            "score": score,    # 0.0 ~ 1.0
            "confidence": 0.7,
            "data_points": len(close_prices)
        },
        "source": "fresh",  # 또는 "cache"
        "message": f"'{symbol}' 트렌드 분석 완료"
    }
```

### **4-2. 통계적 지표 계산**

```python
async def calculate_statistical_indicators(self, symbol: str) -> Dict[str, Any]:
    """통계적 지표 계산 수행 (캐싱 + 재시도 로직)"""
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "price_statistics": {
                "mean": float(price_mean),
                "std": float(price_std),
                "min": float(price_min),
                "max": float(price_max),
                "volatility": float(volatility)  # 연간 변동성
            },
            "volume_statistics": volume_stats,
            "data_points": len(close_prices),
            "analysis_period": "90일"
        },
        "source": "fresh",
        "message": f"'{symbol}' 통계 지표 계산 완료"
    }
```

### **4-3. 패턴 인식**

```python
async def perform_pattern_recognition(self, symbol: str) -> Dict[str, Any]:
    """패턴 인식 수행 (캐싱 + 재시도 로직)"""
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "patterns": patterns,  # 패턴 리스트
            "total_patterns": len(patterns),
            "analysis_period": "120일",
            "data_points": len(close_prices)
        },
        "source": "fresh",
        "message": f"'{symbol}' 패턴 인식 완료"
    }
```

---

## 🚀 **5. FastMCP 서버 구현**

### **5-1. 서버 초기화**

```python
class DataAnalysisMCPServer:
    def __init__(self, port: int = 3021, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.mcp = FastMCP("data_analysis_system")
        self.mcp.description = (
            "데이터 트렌드 분석, 통계적 지표 계산, 패턴 인식을 위한 MCP 서버 (개발 기술 중심)"
        )
```

**학습 포인트**:

- **FastMCP 인스턴스**: MCP 서버의 핵심
- **설정 주입**: 포트, 호스트를 파라미터로 받음
- **명확한 설명**: 서버의 역할을 명시

---

### **5-2. 도구 등록**

```python
def _register_tools(self):
    """MCP 도구들을 등록합니다."""

    @self.mcp.tool()
    async def analyze_data_trends(symbol: str, period: str = "1y") -> Dict[str, Any]:
        """데이터 트렌드 분석 수행 (캐싱 + 재시도 로직)"""
        try:
            result = await self.analysis_client.analyze_data_trends(symbol, period)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "데이터 트렌드 분석에 실패했습니다"
            }
```

**학습 포인트**:

- **@self.mcp.tool()**: FastMCP 도구 등록 데코레이터
- **비동기 함수**: `async def`로 비동기 처리
- **에러 처리**: try-catch로 안전한 응답 반환

---

## 📚 **6. 학습 순서 가이드**

### **1단계: 기본 구조 이해**

1. `__init__.py` - 모듈 구조 파악
2. `server.py` - FastMCP 서버 구조
3. `client.py` - 클라이언트 클래스 구조

### **2단계: 핵심 기술 학습**

1. **캐싱 시스템**: `_get_cache_key`, `_is_cache_valid`
2. **재시도 로직**: `_retry_with_backoff`
3. **데이터 분석**: RSI, 이동평균, 패턴 인식
4. **데이터 구조**: `AnalysisResult`, `DataAnalysisError`

### **3단계: 실제 구현 패턴**

1. **비동기 처리**: `async/await` 패턴
2. **에러 처리**: 커스텀 예외와 로깅
3. **FastMCP 통합**: 도구 등록과 서버 실행
4. **실제 데이터 연동**: FinanceDataReader 활용

---

## 🔧 **7. 실습 예제**

### **7-1. 새로운 분석 지표 추가**

```python
async def calculate_momentum_indicators(self, symbol: str) -> Dict[str, Any]:
    """모멘텀 지표 계산 추가 예제"""
    # 1. 캐시 키 생성
    cache_key = self._get_cache_key("calculate_momentum", {"symbol": symbol})

    # 2. 캐시 확인
    if self._is_cache_valid(cache_key):
        return {"success": True, "data": self._cache[cache_key], "source": "cache"}

    # 3. 실제 모멘텀 계산 로직 구현
    # 4. 캐시 업데이트
    # 5. 결과 반환
```

### **7-2. 서버에 도구 추가**

```python
@self.mcp.tool()
async def calculate_momentum_indicators(symbol: str) -> Dict[str, Any]:
    """모멘텀 지표 계산 수행"""
    try:
        result = await self.analysis_client.calculate_momentum_indicators(symbol)
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
5. **알고리즘 구현**: RSI, 이동평균 등

### **코드 품질**

1. **타입 힌트**: 명시적 타입 선언
2. **한글 주석**: 이해하기 쉬운 설명
3. **단일 책임**: 함수별 명확한 역할
4. **일관성**: 통일된 코딩 스타일
5. **실제 데이터**: FinanceDataReader 연동

---

## 🚀 **9. 다음 단계 학습**

**이 코드를 완벽히 이해한 후**:

1. **다른 MCP 서버 분석**: `naver_news`, `kiwoom` 등
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

### **데이터 분석 디버깅**

```python
# 데이터 상태 확인
print(f"데이터 포인트 수: {len(close_prices)}")
print(f"RSI 값: {rsi}")
print(f"이동평균: MA20={ma20}, MA60={ma60}")
```

---

## 📖 **11. 참고 자료**

- **FastMCP 문서**: [FastMCP 공식 문서](https://github.com/fastmcp/fastmcp)
- **Python asyncio**: [Python 공식 문서](https://docs.python.org/3/library/asyncio.html)
- **NumPy**: [NumPy 공식 문서](https://numpy.org/doc/)
- **FinanceDataReader**: [FinanceDataReader 문서](https://github.com/financedata-org/FinanceDataReader)
- **MCP 프로토콜**: [MCP 공식 문서](https://modelcontextprotocol.io/)

---

**이제 이 학습 가이드를 참고해서 코드를 차근차근 학습해보세요!** 🎯✨

**궁금한 점이나 추가 설명이 필요한 부분이 있으면 언제든 말씀해주세요!** 📚💬
