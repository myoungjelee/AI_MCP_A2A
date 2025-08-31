"""
FastMCP 기반 MCP 클라이언트 베이스 클래스
FastCampus의 실제 구현체를 참조하여 2-3년차 수준으로 단순화했습니다.
FastMCP의 핵심 기능은 유지하되 복잡한 미들웨어 체인은 제거했습니다.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

# HTTP 클라이언트를 위한 의존성 (선택적)
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class CircuitBreakerError(Exception):
    """Circuit Breaker 활성화 시 발생하는 예외."""

    pass


class RateLimitError(Exception):
    """Rate Limit 초과 시 발생하는 예외."""

    pass


class SimpleCircuitBreaker:
    """간단한 Circuit Breaker 패턴 구현."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func):
        """Circuit Breaker를 통한 함수 호출."""

        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time < self.recovery_timeout:
                    raise CircuitBreakerError("Circuit breaker is OPEN")
                else:
                    self.state = "HALF_OPEN"

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception:
                self._on_failure()
                raise

        return wrapper

    def _on_success(self):
        """성공 시 호출."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """실패 시 호출."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class SimpleRateLimiter:
    """간단한 Rate Limiter 구현."""

    def __init__(self, requests_per_second: int = 10, requests_per_hour: int = 3600):
        self.requests_per_second = requests_per_second
        self.requests_per_hour = requests_per_hour
        self.second_window = []
        self.hour_window = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Rate limit 체크 및 허용."""
        async with self._lock:
            current_time = time.time()

            # 1초 윈도우 정리
            self.second_window = [
                t for t in self.second_window if current_time - t < 1.0
            ]

            # 1시간 윈도우 정리
            self.hour_window = [
                t for t in self.hour_window if current_time - t < 3600.0
            ]

            # Rate limit 체크
            if len(self.second_window) >= self.requests_per_second:
                raise RateLimitError("초당 요청 제한 초과")

            if len(self.hour_window) >= self.requests_per_hour:
                raise RateLimitError("시간당 요청 제한 초과")

            # 요청 기록
            self.second_window.append(current_time)
            self.hour_window.append(current_time)


class BaseHTTPClient:
    """HTTP 클라이언트 기본 클래스"""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        requests_per_second: int = 10,
        requests_per_hour: int = 3600,
    ):
        """
        HTTP 클라이언트 초기화

        Args:
            base_url: 기본 URL
            timeout: 요청 타임아웃 (초)
            requests_per_second: 초당 요청 제한
            requests_per_hour: 시간당 요청 제한
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limiter = SimpleRateLimiter(
            requests_per_second=requests_per_second, requests_per_hour=requests_per_hour
        )
        self.logger = logging.getLogger(f"http_client.{base_url}")

        # HTTP 클라이언트 인스턴스 (지연 초기화)
        self._client = None

    async def _get_client(self):
        """HTTP 클라이언트 인스턴스 가져오기 (지연 초기화)"""
        if self._client is None:
            if not HTTPX_AVAILABLE:
                raise ImportError(
                    "httpx 라이브러리가 필요합니다. pip install httpx로 설치하세요."
                )

            self._client = httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True, http2=True
            )
            self.logger.debug("HTTP 클라이언트 초기화 완료")
        return self._client

    async def get(
        self, endpoint: str, params: dict = None, headers: dict = None
    ) -> dict:
        """GET 요청 수행"""
        try:
            await self.rate_limiter.acquire()

            url = f"{self.base_url}{endpoint}"
            self.logger.debug(f"GET 요청: {url}")

            # HTTP 클라이언트 가져오기
            client = await self._get_client()

            # 실제 HTTP 요청 수행
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            # JSON 응답 파싱
            try:
                result = response.json()
                self.logger.debug(f"GET 요청 성공: {url} -> {response.status_code}")
                return result
            except ValueError:
                # JSON이 아닌 경우 텍스트 반환
                return {"content": response.text, "status_code": response.status_code}

        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP 에러 {e.response.status_code}: {url}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"요청 에러: {url} - {e}")
            raise
        except Exception as e:
            self.logger.error(f"GET 요청 실패: {e}")
            raise

    async def post(
        self, endpoint: str, data: dict = None, headers: dict = None
    ) -> dict:
        """POST 요청 수행"""
        try:
            await self.rate_limiter.acquire()

            url = f"{self.base_url}{endpoint}"
            self.logger.debug(f"POST 요청: {url}")

            # HTTP 클라이언트 가져오기
            client = await self._get_client()

            # 실제 HTTP 요청 수행
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()

            # JSON 응답 파싱
            try:
                result = response.json()
                self.logger.debug(f"POST 요청 성공: {url} -> {response.status_code}")
                return result
            except ValueError:
                # JSON이 아닌 경우 텍스트 반환
                return {"content": response.text, "status_code": response.status_code}

        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP 에러 {e.response.status_code}: {url}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"요청 에러: {url} - {e}")
            raise
        except Exception as e:
            self.logger.error(f"POST 요청 실패: {e}")
            raise

    async def close(self):
        """클라이언트 리소스 정리"""
        if self._client:
            await self._client.aclose()
            self._client = None
            self.logger.info("HTTP 클라이언트 리소스 정리 완료")


class BaseMCPClient(ABC):
    """FastMCP 기반 MCP 클라이언트의 베이스 클래스"""

    def __init__(
        self,
        name: str,
        server_url: str = "",
        timeout: float = 30.0,
        requests_per_second: int = 10,
        requests_per_hour: int = 3600,
        enable_circuit_breaker: bool = True,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ):
        """
        MCP 클라이언트 초기화

        Args:
            name: 클라이언트 이름
            server_url: 서버 URL
            timeout: 요청 타임아웃 (초)
            requests_per_second: 초당 요청 제한
            requests_per_hour: 시간당 요청 제한
            enable_circuit_breaker: Circuit Breaker 활성화 여부
            failure_threshold: 실패 횟수 임계값
            recovery_timeout: 복구 대기 시간 (초)
        """
        self.name = name
        self.server_url = server_url
        self.timeout = timeout

        # FastMCP 클라이언트 인스턴스
        self.mcp_client = None

        # 기본 로거 설정
        self.logger = logging.getLogger(f"mcp_client.{name}")
        self._setup_logging()

        # Rate Limiter
        self.rate_limiter = SimpleRateLimiter(
            requests_per_second=requests_per_second, requests_per_hour=requests_per_hour
        )

        # Circuit Breaker
        self.circuit_breaker = (
            SimpleCircuitBreaker(
                failure_threshold=failure_threshold, recovery_timeout=recovery_timeout
            )
            if enable_circuit_breaker
            else None
        )

        self.logger.info(f"MCP 클라이언트 '{name}' 초기화 완료")

    def _setup_logging(self):
        """로깅을 설정합니다."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @abstractmethod
    async def connect(self, server_url: str = "") -> bool:
        """
        MCP 서버에 연결합니다.

        Args:
            server_url: 서버 URL (기본값: 초기화 시 설정된 URL)

        Returns:
            연결 성공 여부
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        MCP 서버와의 연결을 해제합니다.

        Returns:
            연결 해제 성공 여부
        """
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 도구 목록을 가져옵니다.

        Returns:
            도구 목록
        """
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구를 호출합니다.

        Args:
            tool_name: 도구 이름
            params: 도구 파라미터

        Returns:
            도구 실행 결과
        """
        pass

    async def call_tool_with_rate_limit(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Rate limiting과 Circuit Breaker를 적용하여 도구를 호출합니다.

        Args:
            tool_name: 도구 이름
            params: 도구 파라미터

        Returns:
            도구 실행 결과
        """
        try:
            # Rate limiting 체크
            await self.rate_limiter.acquire()

            # Circuit Breaker 적용
            if self.circuit_breaker:
                call_func = self.circuit_breaker.call(self.call_tool)
                return await call_func(tool_name, params)
            else:
                return await self.call_tool(tool_name, params)

        except RateLimitError as e:
            self.logger.warning(f"Rate limit 초과: {e}")
            raise
        except CircuitBreakerError as e:
            self.logger.warning(f"Circuit breaker 활성화: {e}")
            raise
        except Exception as e:
            self.logger.error(f"도구 호출 실패: {e}")
            raise

    async def call_tool_stream(self, tool_name: str, params: Dict[str, Any]):
        """
        도구를 스트리밍 방식으로 호출합니다.

        Args:
            tool_name: 도구 이름
            params: 도구 파라미터

        Yields:
            스트리밍 결과
        """
        try:
            # Rate limiting 체크
            await self.rate_limiter.acquire()

            # 스트리밍 호출 (하위 클래스에서 구현)
            async for result in self._call_tool_stream_internal(tool_name, params):
                yield result

        except RateLimitError as e:
            self.logger.warning(f"Rate limit 초과: {e}")
            raise
        except Exception as e:
            self.logger.error(f"스트리밍 도구 호출 실패: {e}")
            raise

    @abstractmethod
    async def _call_tool_stream_internal(self, tool_name: str, params: Dict[str, Any]):
        """내부 스트리밍 호출 구현. 하위 클래스에서 구현해야 합니다."""
        pass

    def is_connected(self) -> bool:
        """
        서버와 연결되어 있는지 확인합니다.

        Returns:
            연결 상태
        """
        try:
            return self.mcp_client is not None
        except Exception as e:
            self.logger.error(f"연결 상태 확인 실패: {e}")
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        연결 정보를 반환합니다.

        Returns:
            연결 정보
        """
        return {
            "name": self.name,
            "server_url": self.server_url,
            "connected": self.is_connected(),
            "timeout": self.timeout,
            "rate_limit_second": self.rate_limiter.requests_per_second,
            "rate_limit_hour": self.rate_limiter.requests_per_hour,
            "circuit_breaker_enabled": self.circuit_breaker is not None,
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        클라이언트 상태를 확인합니다.

        Returns:
            상태 정보
        """
        try:
            tools = await self.list_tools()
            return {
                "status": "healthy",
                "connected": self.is_connected(),
                "available_tools": len(tools),
                "circuit_breaker_state": (
                    self.circuit_breaker.state if self.circuit_breaker else "disabled"
                ),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": self.is_connected(),
            }
