"""에이전트 에러 처리 모듈.

이 모듈은 모든 에이전트에서 일관된 에러 처리를 위한
데코레이터, 예외 클래스, 에러 포맷팅 유틸리티를 제공합니다.
"""

import functools
import traceback
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# 공통 예외 클래스들
class AgentValidationError(Exception):
    """에이전트 요청 검증 실패 예외."""

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value
        self.timestamp = datetime.now(UTC)


class AgentExecutionError(Exception):
    """에이전트 실행 실패 예외."""

    def __init__(
        self,
        message: str,
        agent_name: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.agent_name = agent_name
        self.original_error = original_error
        self.timestamp = datetime.now(UTC)


class AgentTimeoutError(Exception):
    """에이전트 실행 타임아웃 예외."""

    def __init__(self, message: str, timeout_seconds: float | None = None):
        super().__init__(message)
        self.message = message
        self.timeout_seconds = timeout_seconds
        self.timestamp = datetime.now(UTC)


class AgentResourceError(Exception):
    """에이전트 리소스 부족 예외."""

    def __init__(self, message: str, resource_type: str | None = None):
        super().__init__(message)
        self.message = message
        self.resource_type = resource_type
        self.timestamp = datetime.now(UTC)


class AgentConfigurationError(Exception):
    """에이전트 설정 오류 예외."""

    def __init__(self, message: str, config_key: str | None = None):
        super().__init__(message)
        self.message = message
        self.config_key = config_key
        self.timestamp = datetime.now(UTC)


# MCP 관련 예외 클래스들
class McpConnectionError(Exception):
    """MCP 도구 연결 관련 에러"""

    def __init__(self, message: str, server_name: str = None, retry_count: int = 0):
        super().__init__(message)
        self.server_name = server_name
        self.retry_count = retry_count
        self.timestamp = datetime.now(UTC)


class DataQualityError(Exception):
    """데이터 품질 관련 에러"""

    def __init__(self, message: str, data_source: str = None, severity: str = "medium"):
        super().__init__(message)
        self.data_source = data_source
        self.severity = severity
        self.timestamp = datetime.now(UTC)


class AnalysisCalculationError(Exception):
    """분석 계산 관련 에러"""

    def __init__(self, message: str, method: str = None, input_data: Any = None):
        super().__init__(message)
        self.method = method
        self.input_data = input_data
        self.timestamp = datetime.now(UTC)


# 에러 처리 데코레이터들
def handle_agent_errors(
    reraise: bool = True,
    log_level: str = "error",
    default_return: Any = None,
):
    """
    에이전트 메서드에서 발생하는 예외를 일관되게 처리하는 데코레이터.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 에러 정보 수집
                error_info = {
                    "function": getattr(func, "__name__", "unknown"),
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                }

                # 로깅
                log_func = getattr(logger, log_level, logger.error)
                log_func("agent_method_error", **error_info)

                if reraise:
                    raise
                return default_return

        return wrapper

    return decorator


def handle_async_agent_errors(
    reraise: bool = True,
    log_level: str = "error",
    default_return: Any = None,
):
    """
    비동기 에이전트 메서드에서 발생하는 예외를 일관되게 처리하는 데코레이터.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 에러 정보 수집
                error_info = {
                    "function": getattr(func, "__name__", "unknown"),
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                }

                # 로깅
                log_func = getattr(logger, log_level, logger.error)
                log_func("async_agent_method_error", **error_info)

                if reraise:
                    raise
                return default_return

        return wrapper

    return decorator


def log_and_reraise(
    message: str = "",
    agent_name: str | None = None,
    context: dict | None = None,
):
    """
    에러를 로그에 기록하고 다시 발생시키는 데코레이터.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = {
                    "function": getattr(func, "__name__", "unknown"),
                    "agent_name": agent_name,
                    "custom_message": message,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
                if context:
                    error_context.update(context)

                logger.error("agent_error_caught", **error_context)
                raise

        return wrapper

    return decorator


# 에러 포맷팅 유틸리티들
class ErrorFormatter:
    """에러 메시지 포맷팅 클래스."""

    @staticmethod
    def format_validation_error(error: AgentValidationError) -> dict:
        """검증 에러를 구조화된 형태로 포맷팅."""
        return {
            "error_type": "validation_error",
            "message": error.message,
            "field": error.field,
            "value": str(error.value) if error.value is not None else None,
            "timestamp": error.timestamp.isoformat(),
        }

    @staticmethod
    def format_execution_error(error: AgentExecutionError) -> dict:
        """실행 에러를 구조화된 형태로 포맷팅."""
        return {
            "error_type": "execution_error",
            "message": error.message,
            "agent_name": error.agent_name,
            "original_error": str(error.original_error)
            if error.original_error
            else None,
            "timestamp": error.timestamp.isoformat(),
        }

    @staticmethod
    def format_timeout_error(error: AgentTimeoutError) -> dict:
        """타임아웃 에러를 구조화된 형태로 포맷팅."""
        return {
            "error_type": "timeout_error",
            "message": error.message,
            "timeout_seconds": error.timeout_seconds,
            "timestamp": error.timestamp.isoformat(),
        }

    @staticmethod
    def format_generic_error(error: Exception, context: dict | None = None) -> dict:
        """일반 에러를 구조화된 형태로 포맷팅."""
        result = {
            "error_type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if context:
            result["context"] = context
        return result


# 상태 검증 유틸리티들
def validate_agent_state(state: dict, required_fields: list[str]) -> None:
    """
    에이전트 상태의 필수 필드를 검증합니다.
    """
    missing_fields = []

    for field in required_fields:
        if field not in state or state[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise AgentValidationError(
            f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}",
            field=missing_fields[0] if len(missing_fields) == 1 else None,
        )


def validate_parameter_types(params: dict, type_mapping: dict) -> None:
    """
    파라미터 타입을 검증합니다.
    """
    for field, expected_type in type_mapping.items():
        if (
            field in params
            and params[field] is not None
            and not isinstance(params[field], expected_type)
        ):
            raise AgentValidationError(
                f"필드 '{field}'의 타입이 올바르지 않습니다. "
                f"예상: {expected_type.__name__}, 실제: {type(params[field]).__name__}",
                field=field,
                value=params[field],
            )


# 컨텍스트 매니저들
class ErrorContext:
    """에러 발생 시 컨텍스트 정보를 자동으로 수집하는 컨텍스트 매니저."""

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now(UTC)
        logger.debug("operation_started", operation=self.operation, **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now(UTC) - self.start_time).total_seconds()

        if exc_type is not None:
            logger.error(
                "operation_failed",
                operation=self.operation,
                duration=duration,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context,
            )
        else:
            logger.debug(
                "operation_completed",
                operation=self.operation,
                duration=duration,
                **self.context,
            )

        return False  # 예외를 전파
