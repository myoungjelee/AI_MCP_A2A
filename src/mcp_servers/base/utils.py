"""
MCP 클라이언트 공통 유틸리티 함수

모든 MCP 클라이언트에서 사용할 수 있는 재사용 가능한 함수들을 제공합니다.
"""

import asyncio
import hashlib
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .exceptions import MCPClientError, RetryExhaustedError, TimeoutError

T = TypeVar("T")


def generate_cache_key(operation: str, params: Dict[str, Any]) -> str:
    """캐시 키 생성"""
    # 파라미터를 정렬하여 일관된 키 생성
    sorted_params = sorted(params.items())
    param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
    key_data = f"{operation}:{param_str}"

    # MD5 해시로 고정 길이 키 생성
    return hashlib.md5(key_data.encode()).hexdigest()


def is_cache_valid(
    cache_timestamp: float, cache_ttl: int, current_time: Optional[float] = None
) -> bool:
    """캐시 유효성 검사"""
    if current_time is None:
        current_time = time.time()

    elapsed = current_time - cache_timestamp
    return elapsed < cache_ttl


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exponential_backoff: bool = True,
    max_delay: float = 60.0,
    retry_on_exceptions: tuple = (Exception,),
    **kwargs,
) -> T:
    """지수 백오프를 사용한 재시도 로직"""

    last_exception = None

    for attempt in range(max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except retry_on_exceptions as e:
            last_exception = e

            if attempt == max_attempts - 1:
                raise RetryExhaustedError(
                    f"재시도 {max_attempts}회 모두 실패: {e}", max_attempts
                )

            # 지수 백오프 계산
            if exponential_backoff:
                delay = min(base_delay * (2**attempt), max_delay)
            else:
                delay = base_delay

            logging.warning(
                f"재시도 {attempt + 1}/{max_attempts}, {delay}초 후 재시도: {e}"
            )

            await asyncio.sleep(delay)

    # 이 부분은 실행되지 않지만 타입 체커를 위해 필요
    raise last_exception


def timeout_handler(timeout_seconds: float, timeout_error: Optional[Exception] = None):
    """타임아웃 핸들러 데코레이터"""

    if timeout_error is None:
        timeout_error = TimeoutError(
            f"작업이 {timeout_seconds}초 내에 완료되지 않았습니다"
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise timeout_error

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # 동기 함수의 경우 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, lambda: func(*args, **kwargs))

            try:
                return loop.run_until_complete(
                    asyncio.wait_for(future, timeout=timeout_seconds)
                )
            except asyncio.TimeoutError:
                raise timeout_error

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def batch_processor(batch_size: int = 1000, max_concurrent: int = 5):
    """배치 처리 데코레이터"""

    def decorator(func: Callable[[List[Any]], T]) -> Callable[[List[Any]], List[T]]:
        @wraps(func)
        async def async_wrapper(items: List[Any]) -> List[T]:
            results = []

            # 배치 단위로 분할
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]

                if asyncio.iscoroutinefunction(func):
                    result = await func(batch)
                else:
                    result = func(batch)

                results.append(result)

            return results

        @wraps(func)
        def sync_wrapper(items: List[Any]) -> List[T]:
            results = []

            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                result = func(batch)
                results.append(result)

            return sync_wrapper

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def validate_required_fields(
    data: Dict[str, Any], required_fields: List[str], data_name: str = "데이터"
) -> None:
    """필수 필드 검증"""
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]

    if missing_fields:
        raise MCPClientError(
            f"{data_name}에 필수 필드가 누락되었습니다: {', '.join(missing_fields)}",
            "VALIDATION_ERROR",
        )


def sanitize_input_string(input_str: str, max_length: int = 1000) -> str:
    """입력 문자열 정제"""
    if not isinstance(input_str, str):
        raise MCPClientError("입력값은 문자열이어야 합니다", "VALIDATION_ERROR")

    # 길이 제한
    if len(input_str) > max_length:
        input_str = input_str[:max_length]

    # 위험한 문자 제거 (XSS 방지)
    dangerous_chars = ["<", ">", '"', "'", "&"]
    for char in dangerous_chars:
        input_str = input_str.replace(char, "")

    return input_str.strip()


def format_duration(seconds: float) -> str:
    """지속 시간을 읽기 쉬운 형태로 포맷팅"""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}초"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}분"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}시간"


def calculate_percentage(part: int, total: int) -> float:
    """백분율 계산"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """여러 딕셔너리 병합 (뒤의 것이 우선)"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_get(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """중첩된 딕셔너리에서 값 조회"""
    current = dictionary

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def deep_set(dictionary: Dict[str, Any], keys: List[str], value: Any) -> None:
    """중첩된 딕셔너리에 값 설정"""
    current = dictionary

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
