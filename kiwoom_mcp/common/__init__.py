"""
키움증권 공통 모듈

모든 키움 MCP 서버에서 사용하는 공통 기능을 제공합니다.
- API Constants: 178개 API 정의
- Unified Client: 통합 API 클라이언트
- API Registry: YAML 기반 API 관리
"""

# 상수 모듈
# 통합 클라이언트
from src.mcp_servers.kiwoom_mcp.common.client import (
    KiwoomAPIError,
    KiwoomRESTAPIClient,
    create_client,
)
from src.mcp_servers.kiwoom_mcp.common.constants import (
    APIEndpointPath,
    KiwoomAPIID,
    KiwoomCategory,
    KiwoomEndpoints,
    endpoints,
    get_api,
    get_required_params,
    validate_params,
)

# 도메인 서버 베이스
from src.mcp_servers.kiwoom_mcp.common.domain_base import KiwoomDomainServer

__version__ = "2.0.0"

__all__ = [
    # Types
    "KiwoomCategory",
    "KiwoomAPIID",
    "APIEndpointPath",
    # Endpoints
    "KiwoomEndpoints",
    "endpoints",
    # Functions
    "get_api",
    "get_required_params",
    "validate_params",
    # Client
    "KiwoomRESTAPIClient",
    "KiwoomAPIError",
    "create_client",
    # Domain Base
    "KiwoomDomainServer",
]
