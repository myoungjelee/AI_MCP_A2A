# 재무 분석 시스템 MCP 서버 학습 가이드

## 📋 **전체 구조**

### **파일 구성**

```
financial_analysis/
├── __init__.py          # 모듈 초기화 및 export
├── client.py            # 재무 분석 클라이언트 (핵심 비즈니스 로직)
├── server.py            # FastMCP 기반 MCP 서버
└── LEARNING_GUIDE.md    # 이 학습 가이드
```

### **아키텍처 패턴**

- **Client-Server 패턴**: 클라이언트가 비즈니스 로직을 처리하고, 서버가 MCP 인터페이스를 제공
- **FastMCP 기반**: 표준 MCP 프로토콜을 FastMCP로 구현
- **비동기 처리**: asyncio를 사용한 비동기 데이터 처리
- **BaseMCPClient 상속**: MCP 표준 준수를 위한 기본 클래스 상속

## 🏗️ **핵심 클래스**

### **1. FinancialAnalysisClient**

재무 분석의 핵심 비즈니스 로직을 담당하는 클라이언트

**주요 특징**:

- `BaseMCPClient` 상속으로 MCP 표준 준수
- 캐싱 시스템 (10분 TTL)
- 재시도 로직 (지수 백오프, 최대 3회)
- 실제 데이터 연동 (FinanceDataReader)

**주요 메서드**:

- `get_financial_data()`: 재무 데이터 조회 (FinanceDataReader 사용)
- `calculate_financial_ratios()`: 재무비율 계산
- `calculate_dcf_valuation()`: DCF 밸류에이션 계산
- `generate_investment_report()`: 투자 분석 리포트 생성

**기술적 특징**:

- 캐싱 시스템 (메모리 기반, 10분 TTL)
- 재시도 로직 (지수 백오프, 1초 → 2초 → 4초)
- 에러 처리 및 로깅
- 실제 데이터 연동 (FinanceDataReader)

### **2. FinancialAnalysisMCPServer**

FastMCP 기반 MCP 서버로 클라이언트의 기능을 MCP 도구로 노출

**등록된 도구들** (총 5개):

1. `get_financial_data`: 재무 데이터 조회
2. `calculate_financial_ratios`: 재무비율 계산 및 분석
3. `perform_dcf_valuation`: DCF 밸류에이션
4. `generate_investment_report`: 투자 분석 리포트
5. `compare_peer_valuation`: 동종업계 비교

## 🔧 **핵심 기술 구현**

### **1. 캐싱 시스템**

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
    return age.total_seconds() < self.cache_ttl  # 10분(600초)
```

**학습 포인트**:

- MD5 해시를 사용한 캐시 키 생성
- TTL 기반 캐시 만료 관리 (10분)
- 메모리 효율적인 캐시 구조

### **2. 재시도 로직**

```python
async def _retry_with_backoff(self, func, *args, **kwargs):
    """지수 백오프를 사용한 재시도 로직"""
    for attempt in range(self.max_retries):  # 최대 3회
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == self.max_retries - 1:
                raise

            delay = self.retry_delay * (2 ** attempt)  # 1초 → 2초 → 4초
            self.logger.warning(f"재시도 {attempt + 1}/{self.max_retries}, {delay}초 후 재시도: {e}")
            await asyncio.sleep(delay)
```

**학습 포인트**:

- 지수 백오프 알고리즘 (2^attempt, 1초 → 2초 → 4초)
- 비동기 함수의 재시도 처리 (최대 3회)
- 로깅을 통한 재시도 추적

### **3. DCF 밸류에이션 알고리즘**

```python
# 미래 현금흐름 추정
projected_fcf = []
for year in range(1, projection_years + 1):
    fcf = base_fcf * ((1 + growth_rate / 100) ** year)
    projected_fcf.append(fcf)

# 터미널 가치 계산
terminal_fcf = projected_fcf[-1] * (1 + terminal_growth / 100)
terminal_value = terminal_fcf / (discount_rate / 100 - terminal_growth / 100)

# 현재가치로 할인
pv_fcf = []
for year, fcf in enumerate(projected_fcf, 1):
    pv = fcf / ((1 + discount_rate / 100) ** year)
    pv_fcf.append(pv)
```

**학습 포인트**:

- 복합 이자 계산 공식
- 터미널 가치의 무한급수 계산
- 할인율을 사용한 현재가치 변환

### **4. FastMCP 도구 등록**

```python
@self.mcp.tool()
async def get_financial_data(
    symbol: str,
    data_type: Literal["income", "balance", "cashflow", "all"] = "all",
) -> Dict[str, Any]:
    """재무 데이터 조회"""
    try:
        result = await self.financial_client.get_financial_data(symbol, data_type)
        return {
            "success": True,
            "query": f"get_financial_data: {symbol}",
            "data": result,
        }
    except Exception as e:
        return {
            "success": False,
            "query": f"get_financial_data: {symbol}",
            "error": str(e),
            "func_name": "get_financial_data",
        }
```

**학습 포인트**:

- FastMCP의 `@tool()` 데코레이터 사용
- 비동기 함수의 MCP 도구 등록
- 표준화된 응답 형식 (success, query, data, error)
- Literal 타입을 사용한 파라미터 검증

## 🔍 **실제 등록된 도구들**

### **1. get_financial_data**

- **기능**: 재무 데이터 조회
- **파라미터**: `symbol` (종목코드), `data_type` (income/balance/cashflow/all)
- **응답**: 손익계산서, 재무상태표, 현금흐름표, 시장 데이터

### **2. calculate_financial_ratios**

- **기능**: 재무비율 계산 및 분석
- **파라미터**: `symbol` (종목코드)
- **응답**: 수익성, 안전성, 활동성 비율 + 종합 평가

### **3. perform_dcf_valuation**

- **기능**: DCF 밸류에이션 수행
- **파라미터**: `symbol`, `growth_rate`, `terminal_growth`, `discount_rate`, `projection_years`
- **응답**: DCF 밸류에이션 결과 및 적정주가

### **4. generate_investment_report**

- **기능**: 투자 분석 리포트 생성
- **파라미터**: `symbol` (종목코드)
- **응답**: 종합 투자 분석 리포트 (투자 등급, 권고사항)

### **5. compare_peer_valuation**

- **기능**: 동종업계 밸류에이션 비교
- **파라미터**: `symbols` (쉼표로 구분된 종목코드), `valuation_metrics` (per,pbr)
- **응답**: 동종업계 대비 밸류에이션 비교 결과

## 📚 **학습 순서**

### **1단계: 기본 구조 이해**

1. `__init__.py` 파일로 모듈 구조 파악
2. `client.py`의 클래스 구조와 메서드 이해
3. `server.py`의 FastMCP 서버 구조 파악

### **2단계: 핵심 기능 학습**

1. 캐싱 시스템 구현 방식 (10분 TTL)
2. 재시도 로직의 지수 백오프 (3회 최대)
3. DCF 밸류에이션 알고리즘
4. 재무비율 계산 로직

### **3단계: MCP 서버 구현**

1. FastMCP 도구 등록 패턴 (5개 도구)
2. 에러 처리 및 응답 형식
3. 비동기 함수의 MCP 연동

### **4단계: 실제 데이터 연동**

1. FinanceDataReader 사용법
2. 실제 주식 데이터 처리
3. 재무 데이터 구조화

## 💡 **실용적 예시**

### **재무 데이터 조회 예시**

```python
# 클라이언트 생성
client = FinancialAnalysisClient()

# 삼성전자 재무 데이터 조회
financial_data = await client.get_financial_data("005930")

# 재무비율 계산
ratios = client.calculate_financial_ratios(financial_data)

# DCF 밸류에이션
dcf_result = await client.calculate_dcf_valuation("005930", growth_rate=5.0)

# 투자 분석 리포트
report = await client.generate_investment_report("005930")
```

### **MCP 서버 실행 예시**

```python
# 서버 생성 (포트 8040)
server = FinancialAnalysisMCPServer(port=8040)

# 서버 실행
server.run()
```

### **동종업계 비교 예시**

```python
# 동종업계 비교 (삼성전자, SK하이닉스)
comparison = await server.compare_peer_valuation("005930,000660", "per,pbr")
```

## 🎯 **핵심 학습 포인트**

### **1. 비동기 프로그래밍**

- `asyncio.to_thread()`를 사용한 동기 함수의 비동기 래핑
- `async/await` 패턴의 일관된 사용
- 비동기 함수의 에러 처리

### **2. 데이터 구조화**

- `dataclass`를 사용한 데이터 모델 정의
- `Enum`을 사용한 타입 안전성 확보
- 계층적 데이터 구조 설계

### **3. 성능 최적화**

- 캐싱을 통한 중복 API 호출 방지 (10분 TTL)
- 재시도 로직을 통한 안정성 향상 (3회 최대)
- 메모리 효율적인 데이터 처리

### **4. 에러 처리**

- 커스텀 예외 클래스 정의 (`FinancialAnalysisError`)
- `raise ... from e` 패턴을 사용한 예외 체이닝
- 구조화된 에러 응답 형식

### **5. MCP 표준 준수**

- `BaseMCPClient` 상속으로 표준 인터페이스 구현
- `connect()`, `disconnect()`, `_call_tool_stream_internal()` 메서드 구현
- 표준화된 도구 호출 및 응답 형식

## 🚀 **다음 단계**

### **1. 확장 가능한 기능**

- 더 많은 재무 지표 추가
- 시계열 데이터 분석
- 머신러닝 기반 예측 모델

### **2. 성능 개선**

- Redis를 사용한 분산 캐싱
- 데이터베이스 연동
- 배치 처리 최적화

### **3. 모니터링 및 로깅**

- 구조화된 로깅 (structlog)
- 메트릭 수집
- 성능 프로파일링

## 🐛 **디버깅 팁**

### **1. 일반적인 문제**

- **FinanceDataReader 오류**: 종목코드 형식 확인 (6자리 숫자)
- **캐시 문제**: TTL 설정 (10분) 및 캐시 키 생성 로직 확인
- **비동기 오류**: `await` 키워드 누락 확인

### **2. 로깅 활용**

```python
# 로그 레벨 설정
logging.basicConfig(level=logging.DEBUG)

# 상세한 에러 정보
self.logger.error(f"재무 데이터 조회 실패: {e}", exc_info=True)
```

### **3. 테스트 방법**

```python
# 단위 테스트
import pytest
import asyncio

@pytest.mark.asyncio
async def test_get_financial_data():
    client = FinancialAnalysisClient()
    result = await client.get_financial_data("005930")
    assert result is not None
    assert "income_statement" in result
```

### **4. 캐시 상태 확인**

```python
# 캐시 상태 확인
print(f"Cache keys: {list(client._cache.keys())}")
print(f"Cache timestamps: {client._cache_timestamps}")
print(f"Cache TTL: {client.cache_ttl}초")
```

## 📖 **참고 자료**

### **1. 공식 문서**

- [FastMCP Documentation](https://github.com/fastmcp/fastmcp)
- [FinanceDataReader Documentation](https://github.com/financedata-org/FinanceDataReader)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### **2. 관련 개념**

- **MCP (Model Context Protocol)**: AI 모델과 도구 간의 표준 통신 프로토콜
- **DCF (Discounted Cash Flow)**: 할인현금흐름법을 사용한 기업 가치 평가
- **재무비율**: ROE, ROA, 부채비율 등 기업의 재무 건전성 지표

### **3. 확장 학습**

- **포트폴리오 이론**: 현대 포트폴리오 이론과 리스크 관리
- **기술적 분석**: 차트 패턴과 기술적 지표
- **퀀트 분석**: 정량적 분석 방법론

---

**이 학습 가이드를 통해 재무 분석 시스템 MCP 서버의 구현 방식을 이해하고, 실제 프로젝트에 적용할 수 있는 기술적 역량을 기를 수 있습니다.**

**특히 5개의 실제 등록된 도구와 10분 TTL 캐싱, 3회 재시도 로직 등 구체적인 구현 세부사항을 통해 개발 기술 중심의 포트폴리오를 완성할 수 있습니다.**
