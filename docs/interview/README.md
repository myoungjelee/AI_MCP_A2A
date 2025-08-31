# AI MCP A2A 프로젝트 - 면접용 포트폴리오

## 🎯 **프로젝트 개요**

**AI MCP A2A 프로젝트**는 **Model Context Protocol (MCP)**, **LangGraph**, **Agent-to-Agent (A2A) 통신**을 활용한 **지능형 데이터 처리 시스템**입니다.

### **핵심 목표**

- **개발 기술 어필**: MCP, LangGraph, A2A, Docker 등 최신 기술 스택 활용
- **실제 데이터 연동**: Mock 데이터가 아닌 실제 API를 통한 데이터 처리
- **확장 가능한 아키텍처**: 마이크로서비스 기반의 유연한 시스템 설계

## 🏗️ **현재 구현 상태**

### **✅ 완료된 부분**

- **MCP 서버 6개**: 각각의 도메인별 데이터 처리 시스템
- **FastMCP 기반**: 현대적인 MCP 서버 구현
- **실제 API 연동**: FinanceDataReader, Kiwoom API 등 실제 데이터 소스 활용

### **⏳ 진행 예정**

- **LangGraph 에이전트**: 복잡한 워크플로우 관리
- **A2A 통신**: 에이전트 간 협업 시스템
- **Docker 컨테이너**: 서비스 격리 및 배포 자동화

## 🔧 **기술 스택**

### **핵심 기술**

- **Python 3.12+**: 최신 Python 기능 활용
- **FastMCP**: MCP 서버 구현 프레임워크
- **asyncio**: 비동기 프로그래밍
- **httpx**: 비동기 HTTP 클라이언트

### **데이터 처리**

- **FinanceDataReader**: 주식/금융 데이터
- **numpy**: 수치 계산 및 분석
- **pandas**: 데이터 조작 및 분석

### **개발 도구**

- **uv**: 패키지 관리 및 가상환경
- **pytest**: 테스트 프레임워크
- **ruff**: 코드 품질 및 포맷팅

## 📊 **MCP 서버 상세**

### **1. 거시경제 분석 시스템 (Data Processing System)**

- **포트**: 8001
- **기능**: GDP, 인플레이션 데이터 처리 및 트렌드 분석
- **기술**: 캐싱, 재시도, 선형 회귀, 배치 처리

### **2. 주식 분석 시스템 (Data Analysis System)**

- **포트**: 8002
- **기능**: 주식 데이터 분석, RSI, 이동평균, 패턴 인식
- **기술**: 데이터 검증, 통계 계산, 알고리즘 구현

### **3. 콘텐츠 수집 시스템 (Content Collection System)**

- **포트**: 8003
- **기능**: RSS 파싱, 콘텐츠 필터링, 저장소 관리
- **기술**: 비동기 처리, 데이터 파싱, 메모리 관리

### **4. 검색 시스템 (Search System)**

- **포트**: 8004
- **기능**: 웹 검색, 결과 정렬, 캐싱
- **기술**: 검색 알고리즘, 결과 랭킹, 성능 최적화

### **5. 재무 분석 시스템 (Financial Analysis System)**

- **포트**: 8005
- **기능**: 재무 데이터 처리, 비율 계산, DCF 밸류에이션
- **기술**: 데이터 분석, 통계 계산, 문서 생성

### **6. 키움 API 연동 시스템 (Kiwoom API Integration System)**

- **포트**: 8006
- **기능**: 주식 가격, 계좌 정보, 시장 상태 조회
- **기술**: HTTP 클라이언트, 재시도 로직, 캐싱 시스템

## 🚀 **핵심 기술 구현**

### **1. FastMCP 기반 MCP 서버**

```python
from fastmcp import FastMCP

class DataProcessingServer:
    def __init__(self):
        self.fastmcp = FastMCP(
            name="data_processor",
            description="데이터 처리 시스템"
        )
        self._register_tools()

    def _register_tools(self):
        @self.fastmcp.tool()
        async def process_data(params: dict):
            # 실제 데이터 처리 로직
            pass
```

### **2. 비동기 데이터 처리**

```python
async def get_data_with_retry(self, params: dict):
    """재시도 로직이 포함된 데이터 조회"""
    for attempt in range(self.max_retries):
        try:
            return await self._fetch_data(params)
        except Exception as e:
            if attempt == self.max_retries - 1:
                raise DataProcessingError(f"최대 재시도 횟수 초과: {e}") from e
            delay = self.retry_delay * (2**attempt)
            await asyncio.sleep(delay)
```

### **3. 캐싱 시스템**

```python
def _get_cache_key(self, operation: str, params: dict) -> str:
    """캐시 키 생성"""
    key_data = f"{operation}:{str(sorted(params.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def _is_cache_valid(self, cache_key: str) -> bool:
    """TTL 기반 캐시 유효성 검사"""
    if cache_key not in self._cache_timestamps:
        return False
    age = datetime.now() - self._cache_timestamps[cache_key]
    return age.total_seconds() < self.cache_ttl
```

### **4. 에러 처리 및 로깅**

```python
class DataProcessingError(Exception):
    """데이터 처리 전용 예외"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## 📈 **성능 최적화**

### **1. 배치 처리**

- 대용량 데이터를 청크 단위로 처리
- 메모리 사용량 최적화
- 처리 시간 단축

### **2. 비동기 처리**

- I/O 작업의 비동기 처리
- 동시 요청 처리 능력 향상
- 응답 시간 개선

### **3. 캐싱 전략**

- 메모리 기반 캐싱
- TTL 기반 자동 만료
- 중복 요청 최소화

## 🧪 **테스트 및 품질**

### **1. 단위 테스트**

- 각 MCP 서버별 전용 테스트 파일
- pytest 기반 테스트 작성
- 모킹을 통한 격리된 테스트

### **2. 통합 테스트**

- 모든 MCP 서버 동시 테스트
- 실제 API 연동 테스트
- 성능 및 안정성 검증

### **3. 코드 품질**

- ruff를 통한 자동 포맷팅
- 타입 힌트 활용
- 문서화 및 주석

## 🔮 **향후 확장 계획**

### **Phase 2: LangGraph 에이전트**

- 복잡한 워크플로우 관리
- 상태 기반 에이전트 설계
- 에러 처리 및 복구 시스템

### **Phase 3: A2A 통신**

- 에이전트 간 메시지 교환
- 감독자 패턴 구현
- 분산 시스템 아키텍처

### **Phase 4: Docker 배포**

- 마이크로서비스 컨테이너화
- 자동화된 배포 파이프라인
- 확장성 및 가용성 향상

## 💡 **면접 시 강조 포인트**

### **1. 기술적 역량**

- **FastMCP**: 최신 MCP 프레임워크 활용 능력
- **비동기 프로그래밍**: asyncio 기반 고성능 시스템
- **API 연동**: 실제 외부 서비스와의 통합 경험

### **2. 아키텍처 설계**

- **모듈화**: 각 서버의 독립적 설계
- **확장성**: 새로운 기능 추가의 용이성
- **유지보수성**: 명확한 코드 구조와 문서화

### **3. 실무 적용 능력**

- **실제 데이터**: Mock이 아닌 실제 API 활용
- **에러 처리**: 견고한 예외 처리 시스템
- **성능 최적화**: 캐싱, 재시도, 배치 처리

## 📚 **학습 자료**

각 MCP 서버별로 `LEARNING_GUIDE.md` 파일을 제공하여:

- 코드 구조 이해
- 핵심 기술 학습
- 확장 방법 안내
- 실무 적용 예시

---

**이 프로젝트는 단순한 코드 구현을 넘어, 현대적인 AI 시스템 개발에 필요한 핵심 기술들을 체계적으로 구현한 포트폴리오입니다.** 🚀
