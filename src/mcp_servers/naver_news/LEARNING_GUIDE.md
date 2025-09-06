# Naver News MCP 서버 러닝 가이드

## 🎯 목적
네이버 뉴스 기반의 **키워드/종목 뉴스 검색**을 MCP 툴로 제공합니다.

## 🧱 폴더 구조
```
naver_news/
├── __init__.py
├── client.py    # 뉴스 검색/정규화 로직
├── server.py    # MCP 서버(툴 등록, run_server 엔트리)
└── LEARNING_GUIDE.md
```

## 🚀 실행
```bash
python server.py    # 또는: python -m naver_news.server
# 권장 포트: 8033
```

## 🛠 제공 툴
- `search_news_articles(query, max_articles=10, sort_by="date")`
- `get_stock_news(symbol, company_name="", days_back=7, max_articles=30)`

## 🧩 설계 포인트
- 기사 중복/유사제목 병합, 출처/발행일/URL **항상 포함**
- 기간/정렬 명확화, 오류는 **구조화 에러**로