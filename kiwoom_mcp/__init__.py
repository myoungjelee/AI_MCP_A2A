"""
Kiwoom MCP Server Package

키움증권 API를 통합한 MCP 서버 패키지입니다.
5개 도메인별 서버로 구성됩니다:
- Market Domain (8031): 시장 데이터
- Trading Domain (8030): 거래 관리
- Investor Domain (8033): 투자자 정보
- Info Domain (8034): 종목 정보
- Portfolio Domain (8035): 포트폴리오 관리
"""

# 공통 모듈들
from src.mcp_servers.kiwoom_mcp.common.client.kiwoom_restapi_client import (
    KiwoomRESTAPIClient,
)
from src.mcp_servers.kiwoom_mcp.common.constants.api_types import (
    KiwoomAPIID,
    KiwoomCategory,
)
from src.mcp_servers.kiwoom_mcp.common.domain_base import KiwoomDomainServer

# 도메인 서버 팩토리 함수들
from src.mcp_servers.kiwoom_mcp.domains import (
    create_domain_server,
    create_info_domain_server,
    create_investor_domain_server,
    create_market_domain_server,
    create_portfolio_domain_server,
    create_trading_domain_server,
    get_domain_port,
    list_available_domains,
)

__version__ = "1.0.0"
__all__ = [
    # Common classes
    "KiwoomDomainServer",
    "KiwoomRESTAPIClient",
    "KiwoomAPIID",
    "KiwoomCategory",
    # Domain server factories
    "create_market_domain_server",
    "create_trading_domain_server",
    "create_investor_domain_server",
    "create_info_domain_server",
    "create_portfolio_domain_server",
    # Domain management
    "list_available_domains",
    "get_domain_port",
    "create_domain_server",
]
