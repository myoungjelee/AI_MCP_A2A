"""
키움 도메인 서버 패키지 (5개 새로운 도메인)

키움증권 API를 도메인별로 분류한 MCP 서버들:
- MarketDomainServer: 시장 데이터 관련 (포트 8031)
- InfoDomainServer: 종목 정보 관련 (포트 8032)
- TradingDomainServer: 거래 관련 (포트 8030)
- InvestorDomainServer: 투자자 정보 관련 (포트 8033)
- PortfolioDomainServer: 포트폴리오 관련 (포트 8034)

레거시 서버들은 모두 제거되고 새로운 도메인 아키텍처로 통합됨.
"""

from src.mcp_servers.kiwoom_mcp.domains.info_domain import (
    InfoDomainServer,
    create_info_domain_server,
)
from src.mcp_servers.kiwoom_mcp.domains.investor_domain import (
    InvestorDomainServer,
    create_investor_domain_server,
)
from src.mcp_servers.kiwoom_mcp.domains.market_domain import (
    MarketDomainServer,
    create_market_domain_server,
)
from src.mcp_servers.kiwoom_mcp.domains.portfolio_domain import (
    PortfolioDomainServer,
    create_portfolio_domain_server,
)
from src.mcp_servers.kiwoom_mcp.domains.trading_domain import (
    TradingDomainServer,
    create_trading_domain_server,
)

__all__ = [
    "MarketDomainServer",
    "create_market_domain_server",
    "TradingDomainServer",
    "create_trading_domain_server",
    "InvestorDomainServer",
    "create_investor_domain_server",
    "InfoDomainServer",
    "create_info_domain_server",
    "PortfolioDomainServer",
    "create_portfolio_domain_server",
]

# 도메인 서버 포트 매핑 (5개 새로운 도메인)
DOMAIN_PORTS = {
    "market": 8031,  # 시장 데이터 (market_data, chart 등)
    "info": 8032,  # 종목 정보 (stock_info, etf, theme 등)
    "trading": 8030,  # 거래 관리 (order, account 등)
    "investor": 8033,  # 투자자 정보 (institutional, foreign 등)
    "portfolio": 8034,  # 포트폴리오 관리 (portfolio, risk 등)
}

# 도메인 서버 팩토리
DOMAIN_FACTORIES = {
    "market": create_market_domain_server,
    "trading": create_trading_domain_server,
    "investor": create_investor_domain_server,
    "info": create_info_domain_server,
    "portfolio": create_portfolio_domain_server,
}


def create_domain_server(domain_name: str, debug: bool = False):
    """
    도메인 이름으로 서버 생성

    Args:
        domain_name: 도메인 이름 (market, trading, info, investor, portfolio)
        debug: 디버그 모드 활성화

    Returns:
        해당 도메인 서버 인스턴스

    Raises:
        ValueError: 지원하지 않는 도메인 이름
    """
    if domain_name not in DOMAIN_FACTORIES:
        available = ", ".join(DOMAIN_FACTORIES.keys())
        raise ValueError(f"Unknown domain '{domain_name}'. Available: {available}")

    factory = DOMAIN_FACTORIES[domain_name]
    return factory(debug=debug)


def get_domain_port(domain_name: str) -> int:
    """
    도메인 이름으로 포트 번호 조회

    Args:
        domain_name: 도메인 이름

    Returns:
        포트 번호

    Raises:
        ValueError: 지원하지 않는 도메인 이름
    """
    if domain_name not in DOMAIN_PORTS:
        available = ", ".join(DOMAIN_PORTS.keys())
        raise ValueError(f"Unknown domain '{domain_name}'. Available: {available}")

    return DOMAIN_PORTS[domain_name]


def list_available_domains() -> list[str]:
    """사용 가능한 도메인 목록 반환"""
    return list(DOMAIN_FACTORIES.keys())
