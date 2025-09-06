# Stock Analysis MCP 서버 러닝 가이드

## 🎯 목적
OHLCV 시계열을 입력으로 **기술적 지표/통계/패턴** 분석을 MCP 툴로 제공합니다.

## 🧱 폴더 구조
```
stock_analysis/
├── __init__.py
├── client.py    # 분석 파이프라인/지표 계산
├── server.py    # MCP 서버(툴 등록, run_server 엔트리)
└── LEARNING_GUIDE.md
```

## 🚀 실행
```bash
python server.py    # 또는: python -m stock_analysis.server
# 권장 포트: 8034
```

## 🛠 제공 툴 (예시)
- `analyze_data_trends(symbol, period="1y")`
- `calculate_statistical_indicators(symbol)`
- `perform_pattern_recognition(symbol)`
- `get_server_health`, `get_server_metrics`

## 🧩 설계 포인트
- 계산량 큰 구간은 캐시/샘플링
- 지표 파라미터 기본값/범위 명확화
- 실패는 **구조화 에러**, 빈값 반환 금지