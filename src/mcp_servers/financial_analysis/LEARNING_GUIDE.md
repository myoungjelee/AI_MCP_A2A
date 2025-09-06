# Financial Analysis MCP 서버 러닝 가이드

## 🎯 목적
재무제표(손익/대차/현금흐름) 수집·정규화, 재무비율 계산, DCF 등 **펀더멘털 분석**을 MCP 툴로 제공합니다.

## 🧱 폴더 구조
```
financial_analysis/
├── __init__.py
├── client.py    # 재무데이터 어댑터/분석 로직
├── server.py    # MCP 서버(툴 등록, run_server 엔트리)
└── LEARNING_GUIDE.md
```

## 🚀 실행
```bash
python server.py    # 또는: python -m financial_analysis.server
# 권장 포트: 8031
```

## 🛠 제공 툴
- `get_financial_data(symbol, data_type="income"|"balance"|"cashflow"|"all")`
- `calculate_financial_ratios(symbol)`
- `perform_dcf_valuation(symbol, growth_rate=5.0, discount_rate=10.0)`
- `generate_investment_report(symbol)`
- `get_server_health`, `get_server_metrics`

## 🧩 설계 포인트
- 외부 소스(FMP/Yahoo/사내 DB 등) 교체 가능한 **어댑터 패턴**
- 예외는 **구조화 에러**로 일관 반환, 입력 검증 필수
- 대용량 처리 시 페이지네이션/limit 권장