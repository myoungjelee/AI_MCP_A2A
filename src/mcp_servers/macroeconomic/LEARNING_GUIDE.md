# 데이터 처리 시스템 MCP 서버 학습 가이드

## 📚 **전체 구조**

이 MCP 서버는 **데이터 처리 시스템**으로 구현되어 있으며, 개발 기술 중심으로 설계되었습니다.

```
macroeconomic/
├── client.py          # 데이터 처리 클라이언트
├── server.py          # FastMCP 기반 서버
├── __init__.py        # 모듈 초기화 및 export
└── LEARNING_GUIDE.md  # 이 학습 가이드
```

## 🏗️ **핵심 클래스**

### **DataProcessingClient**

**역할**: 데이터 수집, 배치 처리, 트렌드 분석을 담당하는 클라이언트

**주요 특징**:

- `BaseMCPClient` 상속으로 MCP 표준 준수
- 비동기 처리 (`async/await`)
- 캐싱 시스템 (TTL 기반, 5분)
- 재시도 로직 (지수 백오프, 최대 3회)
- 선형 회귀 알고리즘 구현

**핵심 메서드**:

```python
async def collect_data(category: str, max_records: int, source: str)
async def process_data_batch(data_records: List[Dict], operation: str)
async def analyze_data_trends(data_records: List[Dict])
```

## 🔧 **주요 기술 구현**

### **1. 캐싱 시스템**

```python
def _get_cache_key(self, func_name: str, **kwargs) -> str:
    """캐시 키 생성"""
    params_str = "&".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return f"{func_name}:{params_str}"

def _is_cache_valid(self, cache_key: str) -> bool:
    """캐시 유효성 검사"""
    if cache_key not in self._cache_timestamps:
        return False

    elapsed = time.time() - self._cache_timestamps[cache_key]
    return elapsed < self._cache_ttl  # 5분(300초)
```

**학습 포인트**:

- 캐시 키 생성 전략
- TTL 기반 캐시 만료 (5분)
- 메모리 효율적인 캐시 관리

### **2. 재시도 로직**

```python
async def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs):
    """지수 백오프를 사용한 재시도 로직"""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt  # 1초 → 2초 → 4초
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

**학습 포인트**:

- 지수 백오프 알고리즘 (1초 → 2초 → 4초)
- 비동기 함수의 재시도 처리 (최대 3회)
- 로깅을 통한 디버깅 지원

### **3. 배치 처리 시스템**

```python
async def process_data_batch(self, data_records: List[Dict], operation: str):
    """배치 데이터 처리"""
    # 배치 크기 최적화 (최대 100개)
    batch_size = min(100, len(data_records))

    for i in range(0, len(data_records), batch_size):
        batch = data_records[i:i + batch_size]
        # 배치별 처리 로직
```

**학습 포인트**:

- 배치 크기 최적화 (최대 100개)
- 메모리 효율적인 처리
- 에러 격리 및 복구

### **4. 선형 회귀 알고리즘**

```python
def _calculate_linear_regression(self, values: List[float], timestamps: List[datetime]):
    """선형 회귀 계산"""
    n = len(values)
    x = list(range(n))
    y = values

    # 평균 계산
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    # 기울기와 절편 계산
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator != 0:
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
```

**학습 포인트**:

- 수학적 알고리즘 구현
- 통계 계산 (평균, 분산, 표준편차)
- R-squared 계산
- 예측 모델 구현

### **5. 데이터 구조화**

```python
@dataclass
class DataRecord:
    """데이터 레코드 구조"""
    id: str
    timestamp: datetime
    value: float
    category: str
    source: str
    metadata: Dict[str, Any]
```

**학습 포인트**:

- `@dataclass` 데코레이터 활용
- 타입 힌트를 통한 명확한 데이터 구조
- 직렬화 가능한 데이터 모델

## 🔍 **실제 데이터 처리 기능**

### **1. 데이터 수집**

```python
async def collect_data(self, category: str, max_records: int = 100, source: str = "default"):
    """데이터 수집 - 실제 데이터 사용"""
    return {
        "success": True,
        "category": category,
        "source": source,
        "total_collected": len(records),
        "records": [
            {
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "value": record.value,
                "category": record.category,
                "source": record.source,
                "metadata": record.metadata,
            }
            for record in records
        ],
        "collection_timestamp": datetime.now().isoformat(),
    }
```

### **2. 배치 데이터 처리**

```python
async def process_data_batch(self, data_records: List[Dict], operation: str = "validate"):
    """배치 데이터 처리"""
    return {
        "success": len(errors) == 0,
        "operation": operation,
        "total_records": len(data_records),
        "processed_count": processed_count,
        "batch_size": batch_size,  # 최대 100개
        "processing_time": round(processing_time, 3),
        "results": results,
        "errors": errors,
        "processing_timestamp": datetime.now().isoformat(),
    }
```

### **3. 데이터 트렌드 분석**

```python
async def analyze_data_trends(self, data_records: List[Dict]):
    """데이터 트렌드 분석 (선형 회귀 알고리즘)"""
    return {
        "success": True,
        "trend_analysis": {
            "slope": round(slope, 4),
            "intercept": round(intercept, 4),
            "trend_direction": trend_direction,  # "상승", "하락", "안정"
            "trend_strength": trend_strength,    # "강함", "약함"
            "r_squared": r_squared,
            "predicted_next_value": round(predicted_value, 2),
            "confidence": "높음" if abs(slope) > 0.05 else "보통",
        },
        "statistics": statistics,
        "data_summary": {
            "total_records": len(data_records),
            "valid_records": len(values),
            "time_range": {
                "start": timestamps[0].isoformat(),
                "end": timestamps[-1].isoformat(),
            },
        },
        "analysis_timestamp": datetime.now().isoformat(),
    }
```

## 🚀 **FastMCP 서버 구현**

### **DataProcessingMCPServer**

**핵심 특징**:

- `FastMCP` 직접 사용 (상속 없음)
- 포트 8041 사용
- 도구 등록을 통한 기능 노출
- 비동기 도구 실행

**도구 등록 패턴**:

```python
@self.mcp.tool()
async def collect_data(category: str, max_records: int = 100, source: str = "default"):
    """데이터 수집 도구"""
    try:
        result = await self.client.collect_data(
            category=category,
            max_records=max_records,
            source=source
        )
        return result
    except Exception as e:
        logger.error(f"collect_data failed: {e}")
        return {"success": False, "error": str(e), "category": category}
```

## 📖 **학습 순서**

### **1단계: 기본 구조 이해**

1. `__init__.py`에서 전체 모듈 구조 파악
2. `client.py`의 클래스 구조와 메서드 이해
3. `server.py`의 FastMCP 서버 구현 방식 학습

### **2단계: 핵심 기술 학습**

1. **캐싱 시스템**: `_get_cache_key`, `_is_cache_valid` 메서드
2. **재시도 로직**: `_retry_with_backoff` 메서드
3. **배치 처리**: `process_data_batch` 메서드
4. **알고리즘**: `_calculate_linear_regression` 메서드
5. **데이터 구조**: `DataRecord` dataclass

### **3단계: 고급 기능 학습**

1. **통계 계산**: `_calculate_statistics` 메서드
2. **R-squared**: `_calculate_r_squared` 메서드
3. **배치 최적화**: 다양한 배치 크기와 처리 방식

## 💡 **실용 예시**

### **데이터 처리 워크플로우**

```python
# 1. 데이터 수집
collection_result = await client.collect_data(
    category="performance",
    max_records=100,
    source="system_monitor"
)

# 2. 배치 처리
processing_result = await client.process_data_batch(
    collection_result["records"],
    operation="validate"
)

# 3. 트렌드 분석
trend_result = await client.analyze_data_trends(
    processing_result["results"]
)
```

### **선형 회귀 결과 해석**

```python
trend_analysis = trend_result["trend_analysis"]

print(f"트렌드 방향: {trend_analysis['trend_direction']}")
print(f"트렌드 강도: {trend_analysis['trend_strength']}")
print(f"기울기: {trend_analysis['slope']}")
print(f"R-squared: {trend_analysis['r_squared']}")
print(f"다음 예측값: {trend_analysis['predicted_next_value']}")
```

## 🎯 **핵심 학습 포인트**

### **1. MCP 표준 준수**

- `BaseMCPClient` 상속으로 표준 인터페이스 구현
- `list_tools()`, `call_tool()` 메서드 구현

### **2. 비동기 프로그래밍**

- `asyncio`를 활용한 비동기 처리
- 동시성과 성능 최적화

### **3. 알고리즘 구현**

- 선형 회귀 알고리즘의 수학적 구현
- 통계 계산 및 예측 모델

### **4. 성능 최적화**

- 배치 처리로 대용량 데이터 효율적 처리 (최대 100개)
- 캐싱을 통한 중복 요청 방지 (5분 TTL)
- 재시도 로직으로 안정성 향상 (3회 최대)

### **5. 에러 처리**

- 커스텀 예외 클래스 정의
- 체계적인 에러 로깅 및 응답
- 배치별 에러 격리

## 🚀 **다음 단계**

### **1. 확장 가능한 기능**

- 다양한 머신러닝 알고리즘 (로지스틱 회귀, 랜덤 포레스트)
- 실시간 데이터 스트리밍
- 분산 처리 및 병렬화

### **2. 고급 기술 적용**

- Redis를 활용한 분산 캐싱
- 메시지 큐를 통한 비동기 처리
- 모니터링 및 메트릭 수집

### **3. 테스트 및 검증**

- 단위 테스트 작성
- 통합 테스트 구현
- 성능 테스트 및 최적화

## 🐛 **디버깅 팁**

### **1. 로그 확인**

```python
# 로그 레벨 설정
logging.basicConfig(level=logging.INFO)

# 특정 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### **2. 캐시 디버깅**

```python
# 캐시 상태 확인
print(f"Cache keys: {list(client._cache.keys())}")
print(f"Cache timestamps: {client._cache_timestamps}")
print(f"Cache TTL: {client._cache_ttl}초")
```

### **3. 알고리즘 디버깅**

```python
# 선형 회귀 계산 과정 확인
values = [100, 101, 102, 103, 104]
x = list(range(len(values)))
print(f"Values: {values}")
print(f"X coordinates: {x}")

# 기울기 계산 확인
slope = client._calculate_linear_regression(values, [datetime.now()] * len(values))
print(f"Calculated slope: {slope['slope']}")
```

### **4. 배치 처리 디버깅**

```python
# 배치 크기 확인
batch_size = min(100, len(data_records))  # 최대 100개
print(f"Total records: {len(data_records)}")
print(f"Batch size: {batch_size}")
print(f"Number of batches: {len(data_records) // batch_size + 1}")
```

## 📚 **참고 자료**

- [FastMCP 공식 문서](https://github.com/fastmcp/fastmcp)
- [Python asyncio 가이드](https://docs.python.org/3/library/asyncio.html)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [선형 회귀 수학](https://en.wikipedia.org/wiki/Linear_regression)
- [MCP 프로토콜 스펙](https://modelcontextprotocol.io/)

---

**이 학습 가이드는 개발 기술 중심의 MCP 서버 구현을 위한 것입니다.**
**도메인 지식보다는 MCP, FastMCP, 비동기 처리, 알고리즘 구현 등의 개발 기술에 집중하여 학습하세요.**
