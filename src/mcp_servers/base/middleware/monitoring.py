"""
모니터링 미들웨어

작업 통계와 성능 모니터링을 담당합니다.
"""

import asyncio
import functools
import logging
from datetime import datetime
from typing import Any, Callable, Dict


class MonitoringMiddleware:
    """모니터링 미들웨어"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"mcp.monitoring.{service_name}")
        self.operation_counts = {}
        self.error_counts = {}

    def monitor_operation(self, operation: str):
        """작업 모니터링 데코레이터"""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._monitor_async_operation(
                    func, operation, *args, **kwargs
                )

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._monitor_sync_operation(func, operation, *args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    async def _monitor_async_operation(
        self, func: Callable, operation: str, *args, **kwargs
    ):
        """비동기 작업 모니터링"""
        # 작업 카운트 증가
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            # 에러 카운트 증가
            self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
            raise

    def _monitor_sync_operation(self, func: Callable, operation: str, *args, **kwargs):
        """동기 작업 모니터링"""
        # 작업 카운트 증가
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1

        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            # 에러 카운트 증가
            self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
            raise

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """모니터링 통계 반환"""
        total_operations = sum(self.operation_counts.values())
        total_errors = sum(self.error_counts.values())

        return {
            "service_name": self.service_name,
            "total_operations": total_operations,
            "total_errors": total_errors,
            "error_rate": (
                (total_errors / total_operations * 100) if total_operations > 0 else 0
            ),
            "operation_breakdown": self.operation_counts.copy(),
            "error_breakdown": self.error_counts.copy(),
            "timestamp": datetime.now().isoformat(),
        }
