# MCP 서버 기술 구현 상세

## 🏗️ **아키텍처 설계**

### **1. 전체 시스템 구조**

```
┌─────────────────────────────────────────────────────────────┐
│                    AI MCP A2A 시스템                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   거시경제   │  │   주식분석   │  │  콘텐츠수집  │        │
│  │   MCP서버   │  │   MCP서버   │  │   MCP서버   │        │
│  │   (8001)    │  │   (8002)    │  │   (8003)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    검색     │  │   재무분석   │  │   키움API   │        │
│  │   MCP서버   │  │   MCP서버   │  │   MCP서버   │        │
│  │   (8004)    │  │   (8005)    │  │   (8006)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### **2. 각 MCP 서버의 독립적 설계**

- **포트 분리**: 각 서버가 고유한 포트에서 동작
- **독립적 실행**: 개별적으로 시작/중지 가능
- **모듈화**: 공통 기능은 별도 모듈로 분리

## 🔧 **핵심 기술 구현**

### **1. FastMCP 프레임워크 활용**

#### **서버 초기화**

```python
from fastmcp import FastMCP

class MacroeconomicServer:
    def __init__(self, port: int = 8001):
        self.port = port
        self.fastmcp = FastMCP(
            name="macroeconomic_processor",
            description="거시경제 데이터 처리 시스템",
            instructions="""
            이 서버는 거시경제 데이터를 처리하고 분석합니다.
            GDP, 인플레이션, 고용률 등의 경제 지표를 제공합니다.
            """
        )
        self._register_tools()
```

#### **도구 등록 패턴**

```python
def _register_tools(self):
    @self.fastmcp.tool()
    async def get_gdp_data(params: dict) -> dict:
        """GDP 데이터 조회 및 분석"""
        try:
            result = await self.client.get_gdp_data(params)
            return {
                "success": True,
                "data": result,
                "message": "GDP 데이터 조회 완료"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "GDP 데이터 조회 실패"
            }
```

### **2. 비동기 프로그래밍 패턴**

#### **비동기 HTTP 클라이언트**

```python
import httpx
import asyncio

class DataClient:
    def __init__(self):
        self._client = None
        self.timeout = 30.0

    async def _ensure_client(self):
        """HTTP 클라이언트 생성 보장"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "AI-MCP-System/1.0"}
            )

    async def get_data(self, url: str, params: dict = None) -> dict:
        """비동기 데이터 조회"""
        await self._ensure_client()
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise DataFetchError(f"HTTP 오류: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise DataFetchError(f"요청 오류: {e}") from e
```

#### **비동기 배치 처리**

```python
async def process_batch(self, items: list, batch_size: int = 100) -> list:
    """배치 단위 비동기 처리"""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        # 배치 단위로 동시 처리
        batch_tasks = [self._process_item(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        # 성공한 결과만 수집
        for result in batch_results:
            if not isinstance(result, Exception):
                results.append(result)

        self.logger.info(f"배치 처리 진행률: {min(i + batch_size, len(items))}/{len(items)}")

    return results
```

### **3. 재시도 및 에러 처리**

#### **지수 백오프 재시도**

```python
async def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs):
    """지수 백오프를 사용한 재시도 로직"""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise RetryExhaustedError(f"최대 재시도 횟수 초과: {e}") from e

            # 지수 백오프: 1초, 2초, 4초...
            delay = self.retry_delay * (2 ** attempt)
            self.logger.warning(
                f"재시도 {attempt + 1}/{max_retries}, "
                f"{delay}초 후 재시도: {e}"
            )
            await asyncio.sleep(delay)
```

#### **커스텀 예외 클래스**

```python
class DataProcessingError(Exception):
    """데이터 처리 전용 예외"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict:
        """예외를 딕셔너리로 변환"""
        return {
            "error": str(self),
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }

class ValidationError(DataProcessingError):
    """데이터 검증 오류"""
    pass

class APIError(DataProcessingError):
    """API 호출 오류"""
    pass
```

### **4. 캐싱 시스템**

#### **메모리 기반 캐싱**

```python
import hashlib
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, default_ttl: int = 300):
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl

    def _generate_key(self, operation: str, params: dict) -> str:
        """캐시 키 생성 (MD5 해시)"""
        key_data = f"{operation}:{str(sorted(params.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, operation: str, params: dict):
        """캐시에서 데이터 조회"""
        cache_key = self._generate_key(operation, params)

        if cache_key in self._cache:
            if self._is_valid(cache_key):
                self.logger.info(f"캐시 히트: {operation}")
                return self._cache[cache_key]
            else:
                # 만료된 캐시 제거
                del self._cache[cache_key]
                del self._timestamps[cache_key]

        return None

    def set(self, operation: str, params: dict, data: any, ttl: int = None):
        """캐시에 데이터 저장"""
        cache_key = self._generate_key(operation, params)
        ttl = ttl or self.default_ttl

        self._cache[cache_key] = data
        self._timestamps[cache_key] = datetime.now()

        self.logger.info(f"캐시 업데이트: {operation}, TTL: {ttl}초")

    def _is_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self._timestamps:
            return False

        age = datetime.now() - self._timestamps[cache_key]
        return age.total_seconds() < self.default_ttl
```

### **5. 데이터 검증 및 변환**

#### **Pydantic 모델 활용**

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class GDPData(BaseModel):
    country: str = Field(..., description="국가 코드")
    year: int = Field(..., ge=1900, le=2100, description="연도")
    gdp_value: float = Field(..., gt=0, description="GDP 값")
    currency: str = Field(default="USD", description="통화")

    @validator('country')
    def validate_country(cls, v):
        valid_countries = ['KOR', 'USA', 'JPN', 'CHN']
        if v not in valid_countries:
            raise ValueError(f"지원하지 않는 국가: {v}")
        return v

    @validator('gdp_value')
    def validate_gdp(cls, v):
        if v <= 0:
            raise ValueError("GDP는 0보다 커야 합니다")
        return v

class GDPRequest(BaseModel):
    country: str
    start_year: int = Field(..., ge=1900, le=2100)
    end_year: int = Field(..., ge=1900, le=2100)

    @validator('end_year')
    def validate_year_range(cls, v, values):
        if 'start_year' in values and v < values['start_year']:
            raise ValueError("종료 연도는 시작 연도보다 커야 합니다")
        return v
```

#### **데이터 변환 및 정규화**

```python
class DataTransformer:
    @staticmethod
    def normalize_gdp_data(raw_data: dict) -> GDPData:
        """원시 데이터를 정규화된 형태로 변환"""
        try:
            return GDPData(
                country=raw_data.get('country_code', 'KOR'),
                year=int(raw_data.get('year', 2024)),
                gdp_value=float(raw_data.get('gdp', 0)),
                currency=raw_data.get('currency', 'USD')
            )
        except (ValueError, TypeError) as e:
            raise DataTransformationError(f"GDP 데이터 변환 실패: {e}") from e

    @staticmethod
    def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
        """통화 변환 (간단한 예시)"""
        # 실제 구현에서는 외부 환율 API 사용
        exchange_rates = {
            'USD': 1.0,
            'KRW': 1300.0,
            'JPY': 150.0,
            'CNY': 7.2
        }

        if from_currency not in exchange_rates or to_currency not in exchange_rates:
            raise ValueError(f"지원하지 않는 통화: {from_currency} -> {to_currency}")

        usd_amount = amount / exchange_rates[from_currency]
        return usd_amount * exchange_rates[to_currency]
```

## 📊 **성능 최적화 기법**

### **1. 연결 풀링**

```python
class ConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connections = []
        self._semaphore = asyncio.Semaphore(max_connections)

    async def get_connection(self):
        """연결 획득"""
        await self._semaphore.acquire()
        if self._connections:
            return self._connections.pop()
        return await self._create_connection()

    async def return_connection(self, connection):
        """연결 반환"""
        if len(self._connections) < self.max_connections:
            self._connections.append(connection)
        else:
            await self._close_connection(connection)
        self._semaphore.release()
```

### **2. 메모리 관리**

```python
import gc
import psutil
import os

class MemoryManager:
    def __init__(self, memory_threshold: float = 0.8):
        self.memory_threshold = memory_threshold

    def check_memory_usage(self) -> bool:
        """메모리 사용량 확인"""
        process = psutil.Process(os.getpid())
        memory_percent = process.memory_percent()

        if memory_percent > self.memory_threshold * 100:
            self.logger.warning(f"메모리 사용량 높음: {memory_percent:.1f}%")
            return False
        return True

    def cleanup_memory(self):
        """메모리 정리"""
        # 가비지 컬렉션 실행
        collected = gc.collect()
        self.logger.info(f"가비지 컬렉션 완료: {collected}개 객체 정리")

        # 캐시 크기 조정
        if hasattr(self, '_cache'):
            cache_size = len(self._cache)
            if cache_size > 1000:
                # 오래된 캐시 항목 제거
                self._cleanup_old_cache()
```

## 🧪 **테스트 전략**

### **1. 단위 테스트**

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestDataProcessor:
    @pytest.fixture
    def processor(self):
        return DataProcessor()

    @pytest.mark.asyncio
    async def test_data_fetch_success(self, processor):
        """데이터 조회 성공 테스트"""
        with patch.object(processor.client, 'fetch_data') as mock_fetch:
            mock_fetch.return_value = {"gdp": 1000000, "year": 2024}

            result = await processor.get_gdp_data({"country": "KOR"})

            assert result["success"] is True
            assert result["data"]["gdp"] == 1000000
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_fetch_failure(self, processor):
        """데이터 조회 실패 테스트"""
        with patch.object(processor.client, 'fetch_data') as mock_fetch:
            mock_fetch.side_effect = Exception("API 오류")

            result = await processor.get_gdp_data({"country": "KOR"})

            assert result["success"] is False
            assert "API 오류" in result["error"]
```

### **2. 통합 테스트**

```python
class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_data_pipeline(self):
        """전체 데이터 파이프라인 테스트"""
        # 1. 데이터 조회
        raw_data = await self.fetch_raw_data()
        assert raw_data is not None

        # 2. 데이터 검증
        validated_data = self.validate_data(raw_data)
        assert validated_data is not None

        # 3. 데이터 변환
        transformed_data = self.transform_data(validated_data)
        assert transformed_data is not None

        # 4. 결과 저장
        saved_result = await self.save_data(transformed_data)
        assert saved_result["success"] is True
```

## 🔍 **모니터링 및 로깅**

### **1. 구조화된 로깅**

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logging()

    def _setup_logging(self):
        """로깅 설정"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_operation(self, operation: str, params: dict, result: dict, duration: float):
        """작업 로그 기록"""
        log_data = {
            "operation": operation,
            "params": params,
            "result": result,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.now().isoformat()
        }

        if result.get("success"):
            self.logger.info(f"작업 성공: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.error(f"작업 실패: {json.dumps(log_data, ensure_ascii=False)}")
```

### **2. 성능 메트릭**

```python
import time
from functools import wraps

def measure_performance(func):
    """성능 측정 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            # 성공 메트릭 기록
            if hasattr(args[0], 'logger'):
                args[0].logger.info(
                    f"함수 {func.__name__} 실행 완료: {duration:.3f}초"
                )

            return result

        except Exception as e:
            duration = time.time() - start_time

            # 실패 메트릭 기록
            if hasattr(args[0], 'logger'):
                args[0].logger.error(
                    f"함수 {func.__name__} 실행 실패: {duration:.3f}초, 에러: {e}"
                )
            raise

    return wrapper
```

---

**이 문서는 MCP 서버 구현의 기술적 세부사항을 상세히 설명합니다. 각 기술의 구현 방법과 실제 코드 예시를 통해 개발 역량을 어필할 수 있습니다.** 🚀
