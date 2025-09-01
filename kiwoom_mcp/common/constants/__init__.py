"""
키움증권 API 상수 모듈

180개 API에 대한 상수, 타입, 엔드포인트를 제공합니다.
"""

# API 타입 정의
# API 로더 관리
from src.mcp_servers.kiwoom_mcp.common.constants.api_loader import (
    APIRegistryLoader,
    get_api,
    get_loader,
    get_required_params,
    validate_params,
)
from src.mcp_servers.kiwoom_mcp.common.constants.api_types import (
    API_CATEGORY_MAP,
    API_ENDPOINT_MAP,
    APIEndpointPath,
    KiwoomAPIID,
    KiwoomCategory,
)

# 엔드포인트 관리
from src.mcp_servers.kiwoom_mcp.common.constants.endpoints import (
    KiwoomEndpoints,
    endpoints,
)

__all__ = [
    # Types
    "KiwoomCategory",
    "KiwoomAPIID",
    "APIEndpointPath",
    "API_CATEGORY_MAP",
    "API_ENDPOINT_MAP",
    # Endpoints
    "KiwoomEndpoints",
    "endpoints",
    # Loader
    "APIRegistryLoader",
    "get_loader",
    "get_api",
    "get_required_params",
    "validate_params",
]
