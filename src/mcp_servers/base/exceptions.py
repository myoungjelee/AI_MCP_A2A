"""
MCP 클라이언트 공통 예외 클래스

모든 MCP 클라이언트에서 사용할 수 있는 표준화된 예외를 제공합니다.
"""

from typing import Any, Dict, Optional


class MCPClientError(Exception):
    """MCP 클라이언트 공통 예외"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """예외를 딕셔너리로 변환"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "status_code": self.status_code,
        }


class ConfigurationError(MCPClientError):
    """설정 관련 에러"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key


class AuthenticationError(MCPClientError):
    """인증 관련 에러"""

    def __init__(self, message: str, auth_type: Optional[str] = None):
        super().__init__(message, "AUTHENTICATION_ERROR")
        self.auth_type = auth_type


class AuthorizationError(MCPClientError):
    """권한 관련 에러"""

    def __init__(self, message: str, required_permission: Optional[str] = None):
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.required_permission = required_permission


class ValidationError(MCPClientError):
    """입력값 검증 에러"""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class RateLimitError(MCPClientError):
    """Rate Limit 초과 에러"""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class TimeoutError(MCPClientError):
    """타임아웃 에러"""

    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        super().__init__(message, "TIMEOUT_ERROR")
        self.timeout_seconds = timeout_seconds


class ConnectionError(MCPClientError):
    """연결 에러"""

    def __init__(self, message: str, endpoint: Optional[str] = None):
        super().__init__(message, "CONNECTION_ERROR")
        self.endpoint = endpoint


class DataProcessingError(MCPClientError):
    """데이터 처리 에러"""

    def __init__(self, message: str, data_type: Optional[str] = None):
        super().__init__(message, "DATA_PROCESSING_ERROR")
        self.data_type = data_type


class CacheError(MCPClientError):
    """캐시 관련 에러"""

    def __init__(self, message: str, cache_operation: Optional[str] = None):
        super().__init__(message, "CACHE_ERROR")
        self.cache_operation = cache_operation


class RetryExhaustedError(MCPClientError):
    """재시도 소진 에러"""

    def __init__(self, message: str, max_attempts: Optional[int] = None):
        super().__init__(message, "RETRY_EXHAUSTED_ERROR")
        self.max_attempts = max_attempts


class CircuitBreakerError(MCPClientError):
    """Circuit Breaker 활성화 에러"""

    def __init__(self, message: str, circuit_state: Optional[str] = None):
        super().__init__(message, "CIRCUIT_BREAKER_ERROR")
        self.circuit_state = circuit_state


class ServiceUnavailableError(MCPClientError):
    """서비스 불가 에러"""

    def __init__(self, message: str, service_name: Optional[str] = None):
        super().__init__(message, "SERVICE_UNAVAILABLE_ERROR")
        self.service_name = service_name


class ExternalAPIError(MCPClientError):
    """외부 API 에러"""

    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        api_response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "EXTERNAL_API_ERROR")
        self.api_name = api_name
        self.api_response = api_response


def create_error_from_response(
    response: Dict[str, Any], default_message: str = "Unknown error"
) -> MCPClientError:
    """API 응답에서 에러 객체 생성"""

    error_code = response.get("errorCode", "UNKNOWN_ERROR")
    message = response.get("errorMessage", default_message)
    details = response.get("details", {})

    # 에러 코드별로 적절한 예외 클래스 선택
    if "AUTH" in error_code.upper():
        return AuthenticationError(message, details)
    elif "RATE_LIMIT" in error_code.upper():
        return RateLimitError(message, details.get("retry_after"))
    elif "TIMEOUT" in error_code.upper():
        return TimeoutError(message, details.get("timeout_seconds"))
    elif "VALIDATION" in error_code.upper():
        return ValidationError(message, details.get("field"), details.get("value"))
    else:
        return MCPClientError(message, error_code, details)
