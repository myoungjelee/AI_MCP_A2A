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
