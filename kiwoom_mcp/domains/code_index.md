# `src/mcp_servers/kiwoom_mcp/domains` 코드 인덱스

키움증권 API를 도메인별로 분리한 MCP 서버 구현체들입니다.

## Breadcrumb

- 상위로: [kiwoom_mcp](../code_index.md)
- 최상위: [src](../../../code_index.md)

## 하위 디렉토리 코드 인덱스

- (하위 디렉토리 없음)

## 디렉토리 트리

```text
domains/
├── __init__.py
├── info_domain.py
├── investor_domain.py
├── market_domain.py
├── portfolio_domain.py
└── trading_domain.py
```

## 각 파일 요약

- `__init__.py`: domains 패키지 초기화
- `info_domain.py`: 종목 정보 도메인 서버 - 종목 상세정보, 재무제표, ETF 정보 제공 (포트 8032)
- `investor_domain.py`: 투자자 정보 도메인 서버 - 기관/외국인 매매동향, 투자자별 거래량 (포트 8033)
- `market_domain.py`: 시장 데이터 도메인 서버 - 실시간 시세, 차트, 호가, 체결 데이터 (포트 8031)
- `portfolio_domain.py`: 포트폴리오 도메인 서버 - 자산 관리, 리스크 분석, 성과 평가 (포트 8034)
- `trading_domain.py`: 거래 도메인 서버 - 주문 실행, 계좌 조회, 거래 내역 (포트 8030)