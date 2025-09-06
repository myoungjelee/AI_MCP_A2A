# Tavily Search MCP 서버 러닝 가이드

## 🎯 목적
Tavily API를 사용한 **웹/뉴스/파이낸스 검색**을 MCP 툴로 제공합니다. 근거 URL/스니펫을 함께 반환하여 RAG/검증에 유리합니다.

## 🧱 폴더 구조
```
tavily_search/
├── __init__.py
├── client.py    # Tavily 호출/정규화 로직
├── server.py    # MCP 서버(툴 등록, run_server 엔트리)
└── LEARNING_GUIDE.md
```

## 🚀 실행
```bash
python server.py    # 또는: python -m tavily_search.server
# 권장 포트: 8035
```

## 🛠 제공 툴
- `search_web(query, max_results=10)`
- `search_news(query, max_results=10)`
- `search_finance(query, max_results=10)`
- `get_server_health`, `get_server_metrics`

## 🧩 설계 포인트
- URL/발행일/요약 포함, 중복 제거
- 요청 수/비용 관리: 캐시/쿼리 디듀플리케이션 권장
- 실패는 **구조화 에러**로