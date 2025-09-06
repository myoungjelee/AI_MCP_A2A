"""
MCP 서버 패키지

현업 3-4년차 수준의 MCP 서버들을 제공합니다.
각 서버는 FastMCP 기반으로 구현되어 있으며, 미들웨어 시스템을 통해
로깅, 에러 처리, 모니터링 기능을 제공합니다.
"""

__version__ = "1.0.0"
__author__ = "AI MCP A2A Team"

# 모든 MCP 서버들을 import하여 통합 인터페이스 제공
from .base import (
    BaseHTTPClient,
    BaseMCPClient,
    BaseMCPServer,
    CacheConfig,
    LoggingConfig,
    MCPClientConfig,
    MiddlewareManager,
    MonitoringConfig,
    RetryConfig,
)
from .financedatareader import FDRMCPServer, FinanceDataReaderClient
from .financial_analysis import FinancialAnalysisClient
from .financial_analysis.server import FinancialAnalysisMCPServer
from .macroeconomic import MacroeconomicClient

# MCP 서버들
from .macroeconomic.server import MacroeconomicMCPServer
from .naver_news import NewsClient
from .naver_news.server import NaverNewsMCPServer
from .stock_analysis import StockAnalysisClient
from .stock_analysis.server import StockAnalysisMCPServer
from .tavily_search import TavilySearchClient
from .tavily_search.server import TavilySearchMCPServer

__all__ = [
    # 베이스 클래스들
    "BaseMCPClient",
    "BaseHTTPClient",
    "BaseMCPServer",
    "MiddlewareManager",
    "MCPClientConfig",
    "LoggingConfig",
    "CacheConfig",
    "RetryConfig",
    "MonitoringConfig",
    # MCP 클라이언트들
    "MacroeconomicClient",
    "StockAnalysisClient",
    "NewsClient",
    "TavilySearchClient",
    "FinanceDataReaderClient",
    "FinancialAnalysisClient",
    # MCP 서버들
    "MacroeconomicMCPServer",
    "StockAnalysisMCPServer",
    "NaverNewsMCPServer",
    "TavilySearchMCPServer",
    "FDRMCPServer",
    "FinancialAnalysisMCPServer",
]

# 서버 포트 정보
MCP_SERVER_PORTS = {
    "macroeconomic": 8041,
    "stock_analysis": 3021,
    "naver_news": 8050,
    "tavily_search": 3020,
    "financedatareader": 8030,
    "financial_analysis": 8040,
}


def get_server_port(server_name: str) -> int:
    """MCP 서버의 포트 번호를 반환합니다."""
    return MCP_SERVER_PORTS.get(server_name, 8000)


def get_all_server_ports() -> dict:
    """모든 MCP 서버의 포트 정보를 반환합니다."""
    return MCP_SERVER_PORTS.copy()


def get_server_info(server_name: str) -> dict:
    """MCP 서버의 정보를 반환합니다."""
    if server_name not in MCP_SERVER_PORTS:
        return {"error": f"알 수 없는 서버: {server_name}"}

    return {
        "name": server_name,
        "port": MCP_SERVER_PORTS[server_name],
        "status": "available",
    }
