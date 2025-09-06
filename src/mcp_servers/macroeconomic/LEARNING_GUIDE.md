# Macroeconomic MCP 서버 러닝 가이드

## 🎯 목적
FRED/IMF/OECD 등에서 거시지표를 수집/전처리하고 **추세 분석**을 MCP 툴로 제공합니다.

## 🧱 폴더 구조
```
macroeconomic/
├── __init__.py
├── client.py    # 지표 수집/전처리/분석 로직
├── server.py    # MCP 서버(툴 등록, run_server 엔트리)
└── LEARNING_GUIDE.md
```

## 🚀 실행
```bash
python server.py    # 또는: python -m macroeconomic.server
# 권장 포트: 8032
```

## 🛠 제공 툴 (예시)
- `collect_data(category, max_records=100, source="default")`
- `process_data_batch(data_records, operation="validate")`
- `analyze_data_trends(data_records)`
- `get_server_health`, `get_server_metrics`

## 🧩 설계 포인트
- 지표명/주기(월/분기/년) 일관성 유지
- 대용량/긴 기간은 **limit/pagination** 제공
- 실패는 **구조화 에러**로 반환