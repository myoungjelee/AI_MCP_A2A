# `src/mcp_servers/kiwoom_mcp` 코드 인덱스

키움증권 OpenAPI와 통합하는 MCP 서버 모듈입니다.

## Breadcrumb

- 상위로: [mcp_servers](../code_index.md)
- 최상위: [src](../../code_index.md)

## 하위 디렉토리 코드 인덱스

- [common](common/code_index.md) - 키움 MCP 공통 컴포넌트
- [domains](domains/code_index.md) - 도메인별 MCP 서버 구현

## 디렉토리 트리

```text
kiwoom_mcp/
├── __init__.py
├── common/
│   ├── __init__.py
│   ├── client/
│   ├── constants/
│   ├── domain_base.py
│   └── korean_market.py
└── domains/
    ├── __init__.py
    ├── info_domain.py
    ├── investor_domain.py
    ├── market_domain.py
    ├── portfolio_domain.py
    └── trading_domain.py
```

## 각 파일 요약

- `__init__.py`: kiwoom_mcp 패키지 초기화
- `common/`: 키움 API 클라이언트, 상수, 기본 클래스 등 공통 컴포넌트
- `domains/`: 5개 도메인별 MCP 서버 구현 (시장, 종목, 거래, 투자자, 포트폴리오)

## 도메인 서버 구성

### 5개 도메인 서버
1. **market_domain** (포트 8031): 실시간 시세, 차트 데이터
2. **info_domain** (포트 8032): 종목 정보, 재무제표
3. **trading_domain** (포트 8030): 주문 실행, 계좌 관리
4. **investor_domain** (포트 8033): 기관/외국인 투자 동향
5. **portfolio_domain** (포트 8034): 포트폴리오 관리, 리스크 분석