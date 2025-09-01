# Naver News 폴더 러닝 가이드

## 🎯 **폴더 목적**

네이버 뉴스 API를 활용한 뉴스 수집 및 분석 시스템으로, 실시간 뉴스 데이터를 처리합니다.

## 📁 **파일 구조**

```
naver_news/
├── __init__.py              # 패키지 초기화
├── client.py                # 뉴스 수집 클라이언트
└── server.py                # MCP 서버 구현
```

## 🔧 **핵심 개념**

### **1. NewsClient (client.py)**

- **역할**: 네이버 뉴스 API를 통한 뉴스 수집 및 분석
- **주요 기능**:
  - 뉴스 검색 (`search_news`)
  - 주식 관련 뉴스 필터링 (`get_stock_related_news`)
  - 뉴스 감정 분석 (`analyze_news_sentiment`)

### **2. NaverNewsMCPServer (server.py)**

- **역할**: MCP 프로토콜을 통한 뉴스 서비스 제공
- **주요 기능**:
  - 뉴스 검색 도구 등록
  - 주식 관련 뉴스 도구 등록
  - 감정 분석 도구 등록

## 📊 **뉴스 처리 흐름**

### **1. 뉴스 수집 단계**

```
검색어 입력 → 네이버 API 호출 → 응답 파싱 → 데이터 정제 → 결과 반환
```

### **2. 뉴스 필터링 단계**

```
뉴스 데이터 → 키워드 매칭 → 관련성 점수 → 우선순위 정렬 → 필터링된 결과
```

### **3. 감정 분석 단계**

```
뉴스 텍스트 → 키워드 추출 → 감정 점수 계산 → 긍정/부정/중립 분류
```

## 💡 **핵심 디자인 패턴**

### **1. HTTP 클라이언트 패턴**

```python
# HTTP 세션 관리
async def get(self, endpoint: str, params: Dict[str, Any] = None, headers: Dict[str, Any] = None):
    """HTTP GET 요청 수행"""
    async with self.session.get(endpoint, params=params, headers=headers) as response:
        response.raise_for_status()
        return await response.json()
```

### **2. 키워드 매칭 패턴**

```python
# 긍정/부정 키워드 분류
positive_keywords = ["상승", "강세", "매수", "추천", "목표가상향"]
negative_keywords = ["하락", "약세", "매도", "하향조정", "실적부진"]

# 키워드 기반 감정 분석
sentiment_score = self._calculate_sentiment_score(text, positive_keywords, negative_keywords)
```

### **3. 에러 처리 패턴**

```python
# 계층적 에러 처리
try:
    result = await self._fetch_news_from_api(query, params)
    return self._process_news_data(result)
except httpx.HTTPStatusError as e:
    raise NewsAnalysisError(f"HTTP 에러: {e.response.status_code}")
except httpx.RequestError as e:
    raise NewsAnalysisError(f"요청 에러: {e}")
except Exception as e:
    raise NewsAnalysisError(f"예상치 못한 에러: {e}")
```

## 🚀 **실습 예제**

### **뉴스 검색 테스트**

```python
from src.mcp_servers.naver_news.client import NewsClient

async def test_news_search():
    client = NewsClient()

    # 뉴스 검색
    result = await client.search_news('주식', display=5)
    print(f"검색된 뉴스: {len(result)}개")

    # 첫 번째 뉴스 정보
    if result:
        first_news = result[0]
        print(f"제목: {first_news.get('title', 'N/A')}")
        print(f"링크: {first_news.get('link', 'N/A')}")
```

### **주식 관련 뉴스 필터링 테스트**

```python
# 주식 관련 뉴스만 필터링
stock_news = await client.get_stock_related_news('삼성전자', limit=10)
print(f"주식 관련 뉴스: {len(stock_news)}개")

# 각 뉴스의 관련성 점수
for news in stock_news:
    print(f"- {news['title']} (점수: {news.get('relevance_score', 'N/A')})")
```

### **감정 분석 테스트**

```python
# 뉴스 감정 분석
sentiment_result = await client.analyze_news_sentiment('삼성전자 실적 발표')
print(f"감정 분석 결과: {sentiment_result.get('sentiment', 'N/A')}")
print(f"신뢰도: {sentiment_result.get('confidence', 'N/A')}")
```

## 🔍 **디버깅 팁**

### **1. API 호출 문제**

- **HTTP 상태 코드**: 200, 401, 403, 429 등 확인
- **API 키 설정**: 네이버 개발자 센터에서 API 키 발급 확인
- **요청 제한**: API 호출 횟수 제한 확인

### **2. 데이터 파싱 문제**

- **응답 구조**: 네이버 API 응답 형식 변경 시 파싱 로직 수정
- **인코딩**: 한글 텍스트 인코딩 문제 확인
- **빈 데이터**: API 응답이 비어있는 경우 처리

### **3. 성능 문제**

- **캐싱**: 동일한 검색어에 대한 중복 API 호출 방지
- **배치 처리**: 여러 검색어를 한 번에 처리
- **비동기 처리**: 여러 API 호출을 동시에 수행

## 📈 **성능 최적화**

### **1. API 호출 최적화**

- **캐싱 전략**: 검색 결과를 메모리에 캐싱 (TTL: 5분)
- **배치 요청**: 여러 검색어를 하나의 요청으로 처리
- **연결 풀링**: HTTP 세션 재사용

### **2. 데이터 처리 최적화**

- **스트리밍 파싱**: 대용량 응답을 스트리밍으로 처리
- **병렬 처리**: 여러 뉴스 항목을 동시에 분석
- **메모리 관리**: 불필요한 데이터 즉시 해제

### **3. 에러 처리 최적화**

- **재시도 로직**: 일시적 오류 시 자동 재시도
- **Circuit Breaker**: 연속 실패 시 일시적 중단
- **Fallback**: API 실패 시 대체 데이터 제공

## 🎯 **학습 목표**

1. **HTTP API 연동** 시스템 구축 및 최적화
2. **뉴스 데이터 파싱** 및 정제 로직 구현
3. **키워드 기반 필터링** 알고리즘 개발
4. **감정 분석 시스템** 구현 및 정확도 향상
5. **MCP 서버 통합** 및 도구 등록

## 🔮 **향후 개선 방향**

### **1. 고급 분석 기능**

- **자연어 처리**: BERT, GPT 등 활용한 고급 텍스트 분석
- **주제 모델링**: LDA, BERTopic 등으로 뉴스 주제 분류
- **실시간 모니터링**: WebSocket을 통한 실시간 뉴스 스트리밍

### **2. 다중 소스 통합**

- **다른 뉴스 API**: 뉴스1, 연합뉴스 등 추가
- **소셜 미디어**: 트위터, 페이스북 등 소셜 데이터 통합
- **RSS 피드**: 다양한 뉴스 사이트 RSS 피드 수집

### **3. 시각화 및 리포트**

- **뉴스 대시보드**: 실시간 뉴스 모니터링 인터페이스
- **트렌드 차트**: 시간별 뉴스 양 및 감정 변화
- **자동 리포트**: 일일/주간 뉴스 요약 리포트 생성

## 📚 **참고 자료**

- `docs/kiwoom_rest_api_180_docs.md` - API 연동 관련 문서
- `docs/langchain-llms.txt` - LangChain 통합
- 네이버 개발자 센터 API 문서
- HTTP/2 및 비동기 HTTP 클라이언트 관련 자료

## 🚀 **실제 활용 시나리오**

### **1. 투자자**

- **시장 동향 파악**: 실시간 뉴스로 시장 심리 분석
- **기업 모니터링**: 특정 기업 관련 뉴스 추적
- **매매 타이밍**: 뉴스 기반 매매 시점 결정

### **2. 기업**

- **브랜드 모니터링**: 기업 관련 뉴스 및 여론 추적
- **위기 관리**: 부정적 뉴스 조기 감지 및 대응
- **시장 분석**: 경쟁사 및 산업 동향 파악

### **3. 연구자**

- **뉴스 데이터 분석**: 대량 뉴스 데이터로 연구 수행
- **감정 분석 연구**: 텍스트 마이닝 및 NLP 연구
- **시계열 분석**: 뉴스와 주가 상관관계 연구
