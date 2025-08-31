"""
MCP 서버 베이스 패키지

모든 MCP 서버에서 공통으로 사용할 수 있는 기본 클래스와 유틸리티를 제공합니다.
"""

from .base_mcp_client import BaseHTTPClient, BaseMCPClient
from .base_mcp_server import BaseMCPServer
from .config import (
    CacheConfig,
    LoggingConfig,
    MCPClientConfig,
    MonitoringConfig,
    RetryConfig,
)
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheError,
    CircuitBreakerError,
    ConfigurationError,
    ConnectionError,
    DataProcessingError,
    ExternalAPIError,
    MCPClientError,
    RateLimitError,
    RetryExhaustedError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
)
from .middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    MiddlewareManager,
    MonitoringMiddleware,
)
from .utils import (
    batch_processor,
    calculate_percentage,
    deep_get,
    deep_set,
    format_duration,
    generate_cache_key,
    is_cache_valid,
    merge_dicts,
    retry_with_backoff,
    sanitize_input_string,
    timeout_handler,
    validate_required_fields,
)

__all__ = [
    # 기본 클래스
    "BaseMCPClient",
    "BaseHTTPClient",
    "BaseMCPServer",
    # 미들웨어
    "MiddlewareManager",
    "LoggingMiddleware",
    "ErrorHandlingMiddleware",
    "MonitoringMiddleware",
    # 설정
    "MCPClientConfig",
    "LoggingConfig",
    "CacheConfig",
    "RetryConfig",
    "MonitoringConfig",
    # 예외
    "MCPClientError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "RateLimitError",
    "TimeoutError",
    "ConnectionError",
    "DataProcessingError",
    "CacheError",
    "RetryExhaustedError",
    "CircuitBreakerError",
    "ServiceUnavailableError",
    "ExternalAPIError",
    # 유틸리티
    "generate_cache_key",
    "is_cache_valid",
    "retry_with_backoff",
    "timeout_handler",
    "batch_processor",
    "validate_required_fields",
    "sanitize_input_string",
    "format_duration",
    "calculate_percentage",
    "merge_dicts",
    "deep_get",
    "deep_set",
]
