# Macroeconomic 폴더 러닝 가이드

## 🎯 **폴더 목적**

거시경제 데이터 처리 시스템으로, 데이터 수집, 배치 처리, 트렌드 분석을 담당합니다.

## 📁 **파일 구조**

```
macroeconomic/
├── __init__.py              # 패키지 초기화
├── client.py                # 데이터 처리 클라이언트
└── server.py                # MCP 서버 구현
```

## 🔧 **핵심 개념**

### **1. MacroeconomicClient (client.py)**

- **역할**: 거시경제 데이터 수집 및 처리
- **주요 기능**:
  - 데이터 수집 (`collect_data`)
  - 배치 처리 (`process_data_batch`)
  - 트렌드 분석 (`analyze_trends`)
  - 데이터 검증 (`validate_data`)

### **2. MacroeconomicMCPServer (server.py)**

- **역할**: MCP 프로토콜을 통한 서비스 제공
- **주요 기능**:
  - 데이터 수집 도구 등록
  - 배치 처리 도구 등록
  - 트렌드 분석 도구 등록

## 📊 **데이터 처리 흐름**

### **1. 데이터 수집 단계**

```
요청 → 캐시 확인 → 실제 데이터 수집 → 결과 생성 → 캐시 저장
```

### **2. 배치 처리 단계**

```
데이터 입력 → 배치 분할 → 병렬 처리 → 결과 집계 → 에러 처리
```

### **3. 트렌드 분석 단계**

```
시계열 데이터 → 선형 회귀 → 트렌드 계산 → 신뢰도 평가
```

## 💡 **핵심 디자인 패턴**

### **1. 캐싱 패턴**

```python
# 캐시 키 생성
cache_key = self._get_cache_key("collect_data", **params)

# 캐시 확인
if self._is_cache_valid(cache_key):
    return self._cache[cache_key]

# 실제 데이터 수집 후 캐시 저장
self._cache[cache_key] = result
```

### **2. 재시도 패턴**

```python
@retry_with_backoff(max_attempts=3, exponential_backoff=True)
async def _fetch_data(self, endpoint: str):
    # API 호출 로직
    pass
```

### **3. 배치 처리 패턴**

```python
# 배치 크기 최적화
batch_size = min(100, len(data_records))

# 배치 단위로 처리
for i in range(0, len(data_records), batch_size):
    batch = data_records[i:i + batch_size]
    # 배치 처리 로직
```

## 🚀 **실습 예제**

### **데이터 수집 테스트**

```python
from src.mcp_servers.macroeconomic.client import MacroeconomicClient

async def test_data_collection():
    client = MacroeconomicClient()

    # 데이터 수집
    params = {
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'max_records': 10
    }

    result = await client.collect_data('test', params)
    print(f"수집된 데이터: {len(result['records'])}개")
```

### **배치 처리 테스트**

```python
# 배치 데이터 처리
data_records = [{"id": i, "value": i * 10} for i in range(1000)]
result = await client.process_data_batch(data_records, "validate")
print(f"처리된 데이터: {result['processed_count']}개")
```

## 🔍 **디버깅 팁**

### **1. 캐싱 문제**

- 캐시 TTL 설정 확인
- 캐시 키 생성 로직 점검
- 메모리 사용량 모니터링

### **2. 배치 처리 문제**

- 배치 크기 최적화
- 에러 발생 시 개별 배치 처리 상태 확인
- 메모리 누수 방지

### **3. 트렌드 분석 문제**

- 데이터 품질 검증
- 선형 회귀 가정 확인
- 신뢰도 임계값 조정

## 📈 **성능 최적화**

### **1. 캐싱 전략**

- **메모리 캐시**: 빠른 접근
- **TTL 설정**: 데이터 신선도 유지
- **캐시 키 최적화**: 효율적인 키 생성

### **2. 배치 처리 최적화**

- **배치 크기**: 100개 단위로 최적화
- **병렬 처리**: asyncio 활용
- **에러 격리**: 개별 배치 실패 시 전체 중단 방지

### **3. 메모리 관리**

- **데이터 스트리밍**: 대용량 데이터 처리
- **가비지 컬렉션**: 메모리 해제 최적화

## 🎯 **학습 목표**

1. **데이터 수집 시스템** 구축 및 최적화
2. **배치 처리 알고리즘** 구현 및 성능 튜닝
3. **트렌드 분석 알고리즘** 개발 및 검증
4. **캐싱 및 재시도 시스템** 활용
5. **MCP 서버 통합** 및 도구 등록

## 🔮 **향후 개선 방향**

1. **실제 데이터 소스** 연동 (FinanceDataReader, FRED 등)
2. **고급 분석 알고리즘** 추가 (시계열 분석, 머신러닝)
3. **실시간 데이터 처리** 구현
4. **데이터 품질 모니터링** 시스템 구축
