"""
미들웨어 관리자

모든 미들웨어를 통합 관리하고 체인으로 적용합니다.
"""

from typing import Any, Callable, Dict

from .error_handling import ErrorHandlingMiddleware
from .logging import LoggingMiddleware
from .monitoring import MonitoringMiddleware


class MiddlewareManager:
    """미들웨어 관리자"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logging = LoggingMiddleware(service_name)
        self.error_handling = ErrorHandlingMiddleware(service_name)
        self.monitoring = MonitoringMiddleware(service_name)
        
        # 활성화된 미들웨어 추적
        self._active_middlewares = set(["logging", "error_handling", "monitoring"])

    def enable_middleware(self, middleware_name: str, config: Dict[str, Any] = None):
        """특정 미들웨어를 활성화합니다."""
        if middleware_name in ["logging", "error_handling", "monitoring"]:
            self._active_middlewares.add(middleware_name)
            # 설정 적용 (필요한 경우)
            if config and hasattr(getattr(self, middleware_name), 'configure'):
                getattr(self, middleware_name).configure(config)
        else:
            raise ValueError(f"지원하지 않는 미들웨어: {middleware_name}")

    def disable_middleware(self, middleware_name: str):
        """특정 미들웨어를 비활성화합니다."""
        if middleware_name in ["logging", "error_handling", "monitoring"]:
            self._active_middlewares.discard(middleware_name)
        else:
            raise ValueError(f"지원하지 않는 미들웨어: {middleware_name}")

    def is_active(self) -> bool:
        """미들웨어가 활성화되어 있는지 확인합니다."""
        return len(self._active_middlewares) > 0

    def apply_all(self, operation: str):
        """모든 미들웨어 적용"""

        def decorator(func: Callable):
            # 미들웨어 체인 적용 (순서 중요)
            decorated_func = func
            decorated_func = self.logging.log_operation(operation)(decorated_func)
            decorated_func = self.error_handling.handle_errors(operation)(
                decorated_func
            )
            decorated_func = self.monitoring.monitor_operation(operation)(
                decorated_func
            )
            return decorated_func

        return decorator

    def apply_logging_only(self, operation: str):
        """로깅 미들웨어만 적용"""
        return self.logging.log_operation(operation)

    def apply_error_handling_only(self, operation: str):
        """에러 처리 미들웨어만 적용"""
        return self.error_handling.handle_errors(operation)

    def apply_monitoring_only(self, operation: str):
        """모니터링 미들웨어만 적용"""
        return self.monitoring.monitor_operation(operation)

    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계 반환"""
        return {
            "service_name": self.service_name,
            "logging": self.logging.get_metrics_summary(),
            "monitoring": self.monitoring.get_monitoring_stats(),
            "timestamp": (
                self.logging.metrics[-1].timestamp.isoformat()
                if self.logging.metrics
                else None
            ),
        }
