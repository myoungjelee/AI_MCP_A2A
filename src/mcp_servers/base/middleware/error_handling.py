"""
에러 처리 미들웨어

에러 발생 시 일관된 처리와 로깅을 담당합니다.
"""

import asyncio
import functools
import logging
from datetime import datetime
from typing import Callable


class ErrorHandlingMiddleware:
    """에러 처리 미들웨어"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"mcp.error.{service_name}")

    def handle_errors(self, operation: str):
        """에러 처리 데코레이터"""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    await self._handle_error(operation, e, args, kwargs)
                    raise

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self._handle_error_sync(operation, e, args, kwargs)
                    raise

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    async def _handle_error(
        self, operation: str, error: Exception, args: tuple, kwargs: dict
    ):
        """비동기 에러 처리"""
        error_context = {
            "operation": operation,
            "service": self.service_name,
            "args": str(args),
            "kwargs": str(kwargs),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.error(f"에러 발생: {operation}", extra=error_context)

        # 에러 타입별 처리
        if isinstance(error, (ValueError, TypeError)):
            self.logger.warning(f"입력값 검증 실패: {operation}")
        elif isinstance(error, (ConnectionError, TimeoutError)):
            self.logger.error(f"네트워크 오류: {operation}")
        else:
            self.logger.critical(f"예상치 못한 오류: {operation}")

    def _handle_error_sync(
        self, operation: str, error: Exception, args: tuple, kwargs: dict
    ):
        """동기 에러 처리"""
        error_context = {
            "operation": operation,
            "service": self.service_name,
            "args": str(args),
            "kwargs": str(kwargs),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.error(f"에러 발생: {operation}", extra=error_context)
