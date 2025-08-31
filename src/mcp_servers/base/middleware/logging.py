"""
로깅 미들웨어

작업 로깅과 성능 메트릭 수집을 담당합니다.
"""

import asyncio
import functools
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class LogContext:
    """로그 컨텍스트 정보"""

    service_name: str
    operation: str
    request_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""

    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None


class LoggingMiddleware:
    """로깅 미들웨어"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"mcp.{service_name}")
        self.metrics: List[PerformanceMetrics] = []

    def log_operation(self, operation: str):
        """작업 로깅 데코레이터"""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._log_async_operation(func, operation, *args, **kwargs)

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._log_sync_operation(func, operation, *args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    async def _log_async_operation(
        self, func: Callable, operation: str, *args, **kwargs
    ):
        """비동기 작업 로깅"""
        start_time = time.time()
        context = LogContext(
            service_name=self.service_name,
            operation=operation,
            request_id=f"req_{int(start_time * 1000)}",
        )

        try:
            # 시작 로그
            self.logger.info(
                f"작업 시작: {operation}",
                extra={"context": context, "args": str(args), "kwargs": str(kwargs)},
            )

            # 작업 실행
            result = await func(*args, **kwargs)

            # 성공 로그
            end_time = time.time()
            duration = end_time - start_time

            self.logger.info(
                f"작업 완료: {operation} (소요시간: {duration:.3f}초)",
                extra={"context": context, "duration": duration},
            )

            # 메트릭 기록
            self._record_metrics(operation, start_time, end_time, duration, True)

            return result

        except Exception as e:
            # 에러 로그
            end_time = time.time()
            duration = end_time - start_time
            error_msg = str(e)

            self.logger.error(
                f"작업 실패: {operation} (소요시간: {duration:.3f}초) - {error_msg}",
                extra={
                    "context": context,
                    "duration": duration,
                    "error": error_msg,
                    "traceback": traceback.format_exc(),
                },
            )

            # 메트릭 기록
            self._record_metrics(
                operation, start_time, end_time, duration, False, error_msg
            )

            raise

    def _log_sync_operation(self, func: Callable, operation: str, *args, **kwargs):
        """동기 작업 로깅"""
        start_time = time.time()
        context = LogContext(
            service_name=self.service_name,
            operation=operation,
            request_id=f"req_{int(start_time * 1000)}",
        )

        try:
            # 시작 로그
            self.logger.info(f"작업 시작: {operation}", extra={"context": context})

            # 작업 실행
            result = func(*args, **kwargs)

            # 성공 로그
            end_time = time.time()
            duration = end_time - start_time

            self.logger.info(
                f"작업 완료: {operation} (소요시간: {duration:.3f}초)",
                extra={"context": context, "duration": duration},
            )

            # 메트릭 기록
            self._record_metrics(operation, start_time, end_time, duration, True)

            return result

        except Exception as e:
            # 에러 로그
            end_time = time.time()
            duration = end_time - start_time
            error_msg = str(e)

            self.logger.error(
                f"작업 실패: {operation} (소요시간: {duration:.3f}초) - {error_msg}",
                extra={
                    "context": context,
                    "duration": duration,
                    "error": error_msg,
                    "traceback": traceback.format_exc(),
                },
            )

            # 메트릭 기록
            self._record_metrics(
                operation, start_time, end_time, duration, False, error_msg
            )

            raise

    def _record_metrics(
        self,
        operation: str,
        start_time: float,
        end_time: float,
        duration: float,
        success: bool,
        error_message: Optional[str] = None,
    ):
        """성능 메트릭 기록"""
        metric = PerformanceMetrics(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
        )
        self.metrics.append(metric)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약 반환"""
        if not self.metrics:
            return {"message": "수집된 메트릭이 없습니다"}

        total_operations = len(self.metrics)
        successful_operations = len([m for m in self.metrics if m.success])
        failed_operations = total_operations - successful_operations

        durations = [m.duration for m in self.metrics]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0

        return {
            "service_name": self.service_name,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": (
                (successful_operations / total_operations) * 100
                if total_operations > 0
                else 0
            ),
            "performance": {
                "average_duration": round(avg_duration, 3),
                "max_duration": round(max_duration, 3),
                "min_duration": round(min_duration, 3),
            },
            "recent_operations": [
                {
                    "operation": m.operation,
                    "duration": round(m.duration, 3),
                    "success": m.success,
                    "timestamp": datetime.fromtimestamp(m.start_time).isoformat(),
                }
                for m in self.metrics[-10:]  # 최근 10개
            ],
        }
