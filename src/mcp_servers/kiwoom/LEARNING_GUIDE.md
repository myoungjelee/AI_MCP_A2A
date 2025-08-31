# Kiwoom API 연동 MCP 서버 학습 가이드

## 🎯 **개요**

이 가이드는 **Kiwoom API 연동 MCP 서버**를 통해 개발 기술을 학습하는 방법을 설명합니다. 실제 트레이딩 로직은 제거하고 **API 연동 기술**에 집중합니다.

## 🏗️ **전체 구조**

```
kiwoom/
├── client.py           # API 연동 클라이언트
├── server.py           # FastMCP 기반 서버
├── __init__.py         # 모듈 초기화 및 export
└── LEARNING_GUIDE.md   # 이 파일
```

## 🔧 **핵심 클래스들**

### **1. KiwoomClient**

**역할**: 키움 API와의 통신을 담당하는 클라이언트

**주요 특징**:

- `BaseMCPClient` 상속으로 MCP 표준 준수
- API 연결 및 인증
- 데이터 조회 (주식 가격, 계좌 정보 등)
- 에러 처리 및 재시도
- 캐싱 시스템 (5분 TTL)
- API 실패 시 샘플 데이터 반환

**핵심 메서드**:

```python
async def connect_to_kiwoom(self, app_key: str, app_secret: str, account_no: str) -> bool
async def get_stock_price(self, stock_code: str) -> Dict[str, Any]
async def get_account_info(self) -> Dict[str, Any]
async def get_stock_info(self, stock_code: str) -> Dict[str, Any]
async def get_market_status(self) -> Dict[str, Any]
```

### **2. KiwoomMCPServer**

**역할**: FastMCP 기반 MCP 서버

**주요 특징**:

- `FastMCP` 직접 사용 (상속 없음)
- 포트 8030 사용
- HTTP 요청 처리
- 에러 응답 표준화

**핵심 메서드**:

```python
def _register_tools(self)  # FastMCP 도구 등록
async def run(self)        # 서버 실행
```

## 🚀 **핵심 기술 구현**

### **1. 비동기 HTTP 클라이언트**

```python
# httpx를 사용한 비동기 HTTP 통신
self._client = httpx.AsyncClient(
    timeout=self.timeout,  # 30초
    headers={
        "Content-Type": "application/json",
        "appkey": self.app_key,
        "appsecret": self.app_secret,
        "tr_id": "H0_CNT0",
    }
)

# API 호출
response = await self._client.get(url, params=params)
```

**학습 포인트**:

- `httpx` 라이브러리 사용법
- 비동기 HTTP 통신 패턴
- 헤더 및 파라미터 설정
- 타임아웃 설정 (30초)

### **2. 지수 백오프 재시도 로직**

```python
async def _retry_with_backoff(self, func, *args, **kwargs):
    """지수 백오프를 사용한 재시도 로직"""
    for attempt in range(self.max_retries):  # 최대 3회
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == self.max_retries - 1:
                raise KiwoomError(f"최대 재시도 횟수 초과: {e}")

            delay = self.retry_delay * (2**attempt)  # 1초 → 2초 → 4초
            self.logger.warning(f"재시도 {attempt + 1}/{self.max_retries}, {delay}초 후 재시도: {e}")
            await asyncio.sleep(delay)
```

**학습 포인트**:

- 재시도 로직 설계 (최대 3회)
- 지수 백오프 알고리즘 (1초 → 2초 → 4초)
- 비동기 함수 처리

### **3. 메모리 캐싱 시스템**

```python
def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
    """캐시 키 생성"""
    key_data = f"{operation}:{str(sorted(params.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def _is_cache_valid(self, cache_key: str) -> bool:
    """캐시 유효성 검사"""
    if cache_key not in self._cache_timestamps:
        return False

    age = datetime.now() - self._cache_timestamps[cache_key]
    return age.total_seconds() < self.cache_ttl  # 5분(300초)
```

**학습 포인트**:

- 캐시 키 생성 전략 (MD5 해시)
- TTL 기반 캐시 만료 (5분)
- 메모리 기반 캐싱

### **4. API 실패 시 샘플 데이터 반환**

```python
async def _fetch_stock_price(self, stock_code: str) -> Dict[str, Any]:
    """실제 주식 가격 API 호출"""
    try:
        # 키움 API 호출 (실제 구현)
        response = await self._client.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data and "output" in data:
                return {
                    "stock_code": stock_code,
                    "price": data["output"].get("stck_prpr", 0),
                    "change": data["output"].get("prdy_vrss", 0),
                    "change_rate": data["output"].get("prdy_ctrt", 0),
                    "volume": data["output"].get("acml_vol", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # API 응답이 비어있거나 예상과 다른 경우 샘플 데이터 반환
                return {
                    "stock_code": stock_code,
                    "price": 50000,
                    "change": 500,
                    "change_rate": 1.0,
                    "volume": 1000000,
                    "timestamp": datetime.now().isoformat(),
                    "note": "샘플 데이터 (API 응답 없음)",
                }
        else:
            raise KiwoomError(f"API 응답 오류: {response.status_code}")

    except Exception as e:
        # API 호출 실패 시 샘플 데이터 반환
        self.logger.warning(f"API 호출 실패, 샘플 데이터 반환: {e}")
        return {
            "stock_code": stock_code,
            "price": 50000,
            "change": 500,
            "change_rate": 1.0,
            "volume": 1000000,
            "timestamp": datetime.now().isoformat(),
            "note": "샘플 데이터 (API 호출 실패)",
        }
```

**학습 포인트**:

- API 실패 시 graceful degradation
- 샘플 데이터를 통한 서비스 연속성 보장
- 사용자 경험 개선

### **5. FastMCP 도구 등록**

```python
@self.fastmcp.tool()
async def get_stock_price(stock_code: str) -> Dict[str, Any]:
    """주식 가격 조회"""
    try:
        self.logger.info(f"주식 가격 조회 요청: {stock_code}")
        result = await self.kiwoom_client.get_stock_price(stock_code)
        self.logger.info(f"주식 가격 조회 성공: {stock_code}")
        return {
            "success": True,
            "data": result,
            "message": f"{stock_code} 종목 가격 조회 완료",
        }
    except KiwoomError as e:
        self.logger.error(f"주식 가격 조회 실패: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"{stock_code} 종목 가격 조회 실패",
        }
    except Exception as e:
        self.logger.error(f"예상치 못한 에러: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "시스템 오류가 발생했습니다",
        }
```

**학습 포인트**:

- FastMCP 데코레이터 사용법
- 도구 함수 설계 패턴
- 에러 처리 및 응답 표준화
- 로깅을 통한 모니터링

## 🔍 **실제 API 응답 구조**

### **1. 주식 가격 조회**

```python
async def get_stock_price(self, stock_code: str):
    """주식 가격 조회 - 실제 데이터 또는 샘플 데이터"""
    return {
        "stock_code": stock_code,
        "price": 50000,           # 실제 가격 또는 샘플
        "change": 500,            # 등락폭
        "change_rate": 1.0,       # 등락률
        "volume": 1000000,        # 거래량
        "timestamp": "2024-01-01T10:00:00",
        "note": "샘플 데이터 (API 호출 실패)"  # API 실패 시에만
    }
```

### **2. 계좌 정보 조회**

```python
async def get_account_info(self):
    """계좌 정보 조회"""
    return {
        "account_no": "1234567890",
        "balance": 10000000,      # 예수금
        "total_value": 50000000,  # 총 평가금액
        "profit_loss": 5000000,   # 손익
        "timestamp": "2024-01-01T10:00:00"
    }
```

### **3. 주식 기본 정보**

```python
async def get_stock_info(self, stock_code: str):
    """주식 기본 정보 조회"""
    return {
        "stock_code": stock_code,
        "name": "삼성전자",        # 종목명
        "market": "KOSPI",        # 시장구분
        "sector": "전기전자",      # 업종
        "timestamp": "2024-01-01T10:00:00"
    }
```

### **4. 시장 상태**

```python
async def get_market_status(self):
    """시장 상태 조회"""
    return {
        "market_open": True,      # 시장 개장 여부
        "current_time": "2024-01-01T10:00:00",
        "market_type": "KOSPI",   # 시장 유형
        "status": "OPEN"          # 상태 (OPEN/CLOSED)
    }
```

## 📚 **학습 순서**

### **1단계: 기본 구조 이해**

1. `__init__.py`에서 전체 모듈 구조 파악
2. `client.py`의 클래스 구조 이해
3. `server.py`의 서버 구조 이해

### **2단계: 핵심 기술 학습**

1. **비동기 HTTP 통신**: `httpx` 사용법
2. **재시도 로직**: 지수 백오프 알고리즘 (3회 최대)
3. **캐싱 시스템**: 메모리 기반 캐싱 (5분 TTL)
4. **FastMCP**: 도구 등록 및 실행
5. **API 실패 처리**: 샘플 데이터 반환 로직

### **3단계: 실제 구현 연습**

1. 새로운 API 엔드포인트 추가
2. 캐싱 전략 개선
3. 에러 처리 강화
4. 로깅 시스템 개선

## 💡 **실용적 예시**

### **새로운 도구 추가하기**

```python
@self.fastmcp.tool()
async def get_stock_history(self, stock_code: str, days: int = 30) -> Dict[str, Any]:
    """주식 히스토리 조회"""
    try:
        result = await self.kiwoom_client.get_stock_history(stock_code, days)
        return {"success": True, "data": result}
    except KiwoomError as e:
        return {"success": False, "error": str(e)}
```

### **캐싱 전략 개선**

```python
# Redis 기반 캐싱으로 확장
async def _get_redis_cache(self, key: str):
    return await self.redis_client.get(key)

async def _set_redis_cache(self, key: str, value: Any, ttl: int = 300):
    await self.redis_client.setex(key, ttl, json.dumps(value))
```

## 🎯 **핵심 학습 포인트**

### **1. API 연동 패턴**

- HTTP 클라이언트 설계
- 인증 및 헤더 관리
- 응답 데이터 파싱
- API 실패 시 graceful degradation

### **2. 에러 처리 전략**

- 커스텀 예외 클래스 (`KiwoomError`)
- 재시도 로직 (3회 최대)
- 사용자 친화적 에러 메시지
- 샘플 데이터를 통한 서비스 연속성

### **3. 성능 최적화**

- 캐싱 시스템 (5분 TTL)
- 비동기 처리
- 연결 풀링
- MD5 해시 기반 캐시 키

### **4. MCP 서버 설계**

- FastMCP 프레임워크 활용
- 도구 등록 및 관리
- 표준화된 응답 형식
- 포트 8030 사용

## 🚀 **다음 단계**

### **1. 고급 기능 추가**

- WebSocket을 통한 실시간 데이터
- 배치 처리 시스템
- 메트릭 수집 및 모니터링

### **2. 아키텍처 개선**

- 마이크로서비스 분리
- 로드 밸런싱
- 장애 복구 시스템

### **3. 테스트 강화**

- 단위 테스트 작성
- 통합 테스트 구현
- 성능 테스트 수행

## 🔍 **디버깅 팁**

### **1. 로깅 활용**

```python
self.logger.info(f"API 호출 시작: {url}")
self.logger.debug(f"요청 파라미터: {params}")
self.logger.error(f"API 호출 실패: {e}")
```

### **2. 에러 추적**

```python
try:
    result = await self._make_api_call()
except Exception as e:
    self.logger.error(f"에러 발생: {e}", exc_info=True)
    raise
```

### **3. 성능 모니터링**

```python
import time

start_time = time.time()
result = await self._make_api_call()
execution_time = time.time() - start_time
self.logger.info(f"API 호출 완료: {execution_time:.2f}초")
```

### **4. 캐시 상태 확인**

```python
# 캐시 상태 확인
print(f"Cache keys: {list(client._cache.keys())}")
print(f"Cache timestamps: {client._cache_timestamps}")
print(f"Cache TTL: {client.cache_ttl}초")
```

## 📖 **참고 자료**

- [FastMCP 공식 문서](https://github.com/fastmcp/fastmcp)
- [httpx 공식 문서](https://www.python-httpx.org/)
- [Python asyncio 가이드](https://docs.python.org/3/library/asyncio.html)
- [MCP 프로토콜 스펙](https://modelcontextprotocol.io/)

---

**이 가이드를 통해 Kiwoom API 연동 MCP 서버의 핵심 기술을 마스터하고, 실제 프로젝트에 적용할 수 있는 실력을 기르세요!** 🚀
