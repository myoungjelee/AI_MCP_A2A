"""
FastMCP 기반 MCP 서버 베이스 클래스
FastCampus의 실제 구현체를 참조하여 현업 3-4년차 수준으로 개선했습니다.
FastMCP의 핵심 기능은 유지하되 미들웨어 체인과 설정 관리를 강화했습니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import MCPServerConfig
from .middleware import MiddlewareManager


class StandardResponse(BaseModel):
    """표준화된 MCP Server 응답 모델"""

    success: bool = Field(True, description="성공 여부")
    query: str = Field(..., description="원본 쿼리")
    data: Any = Field(None, description="응답 데이터")
    message: str = Field("", description="응답 메시지")
    timestamp: str = Field("", description="응답 시간")
    service_name: str = Field("", description="서비스 이름")


class ErrorResponse(BaseModel):
    """표준 에러 MCP Server 응답 모델"""

    success: bool = Field(False, description="성공 여부")
    query: str = Field(..., description="원본 쿼리")
    error: str = Field(..., description="에러 메시지")
    func_name: Optional[str] = Field(None, description="에러가 발생한 함수명")
    error_code: Optional[str] = Field(None, description="에러 코드")
    timestamp: str = Field("", description="에러 발생 시간")
    service_name: str = Field("", description="서비스 이름")


class BaseMCPServer(ABC):
    """FastMCP 기반 MCP 서버의 베이스 클래스"""

    def __init__(
        self,
        name: str,
        port: int = 8000,
        host: str = "0.0.0.0",
        debug: bool = False,
        server_instructions: str = "",
        config: Optional[Union[Dict[str, Any], MCPServerConfig]] = None,
        enable_middlewares: Optional[List[str]] = None,
        middleware_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        MCP 서버 초기화

        Args:
            name: 서버 이름
            port: 서버 포트 (기본값: 8000)
            host: 호스트 주소 (기본값: "0.0.0.0")
            debug: 디버그 모드 (기본값: False)
            server_instructions: 서버 설명 (기본값: "")
            config: 서버 설정 (기본값: None)
            enable_middlewares: 활성화할 미들웨어 목록 (기본값: None)
            middleware_config: 미들웨어 설정 (기본값: None)
            **kwargs: 추가 옵션
        """
        self.name = name
        self.port = port
        self.host = host
        self.debug = debug
        self.server_instructions = server_instructions

        # 설정 초기화
        self.config = self._initialize_config(config)

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager(name)
        self._setup_middlewares(enable_middlewares, middleware_config)

        # FastMCP 인스턴스 생성
        self.mcp = FastMCP(name=name, instructions=server_instructions)

        # 헬스체크 엔드포인트 설정
        self._setup_health_endpoints()

        # 로거 설정
        self.logger = logging.getLogger(f"mcp_server.{name}")
        self._setup_logging()

        # 클라이언트 초기화
        self._initialize_clients()

        # 도구 등록
        self._register_tools()

        # 서버 상태 초기화
        self._server_start_time = None
        self._request_count = 0
        self._error_count = 0

        self.logger.info(f"MCP 서버 '{name}' 초기화 완료")

    def _initialize_config(
        self, config: Optional[Union[Dict[str, Any], MCPServerConfig]]
    ) -> MCPServerConfig:
        """설정을 초기화합니다."""
        if isinstance(config, MCPServerConfig):
            return config
        elif isinstance(config, dict):
            return MCPServerConfig(**config)
        else:
            # 기본 설정 사용
            return MCPServerConfig(
                name=self.name,
                port=self.port,
                host=self.host,
                debug=self.debug,
                max_connections=100,
                request_timeout=30,
                enable_metrics=True,
                enable_health_check=True,
            )

    def _setup_logging(self):
        """로깅을 설정합니다."""
        log_level = logging.DEBUG if self.debug else logging.INFO
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # 이미 설정된 로거가 있다면 레벨만 변경
        if not self.logger.handlers:
            logging.basicConfig(
                level=log_level,
                format=log_format,
            )
        else:
            self.logger.setLevel(log_level)

    def _setup_middlewares(
        self,
        enable_middlewares: Optional[List[str]],
        middleware_config: Optional[Dict[str, Any]],
    ):
        """미들웨어를 설정합니다."""
        if enable_middlewares:
            # bool 타입인 경우 기본 미들웨어 사용
            if isinstance(enable_middlewares, bool):
                enable_middlewares = ["logging", "error_handling", "monitoring"]

            for middleware_name in enable_middlewares:
                config = (
                    middleware_config.get(middleware_name, {})
                    if middleware_config
                    else {}
                )
                self.middleware.enable_middleware(middleware_name, config)

    @abstractmethod
    def _initialize_clients(self):
        """클라이언트들을 초기화합니다. 하위 클래스에서 구현해야 합니다."""
        pass

    @abstractmethod
    def _register_tools(self):
        """MCP 도구들을 등록합니다. 하위 클래스에서 구현해야 합니다."""
        pass

    def create_standard_response(
        self, success: bool, query: str, data: Any = None, message: str = ""
    ) -> StandardResponse:
        """
        표준 응답을 생성합니다.

        Args:
            success: 성공 여부
            query: 원본 쿼리
            data: 응답 데이터
            message: 응답 메시지

        Returns:
            표준 응답 객체
        """
        from datetime import datetime

        return StandardResponse(
            success=success,
            query=query,
            data=data,
            message=message,
            timestamp=datetime.now().isoformat(),
            service_name=self.name,
        )

    def create_error_response(
        self,
        func_name: str,
        error: Any,
        query: str = "",
        error_code: Optional[str] = None,
        **kwargs,
    ) -> ErrorResponse:
        """
        에러 응답을 생성합니다.

        Args:
            func_name: 에러가 발생한 함수명
            error: 에러 객체 또는 메시지
            query: 원본 쿼리
            error_code: 에러 코드
            **kwargs: 추가 필드

        Returns:
            에러 응답 객체
        """
        from datetime import datetime

        error_message = str(error) if hasattr(error, "__str__") else str(error)

        # 에러 카운트 증가
        self._error_count += 1

        return ErrorResponse(
            success=False,
            query=query,
            error=error_message,
            func_name=func_name,
            error_code=error_code,
            timestamp=datetime.now().isoformat(),
            service_name=self.name,
            **kwargs,
        )

    def get_server_status(self) -> Dict[str, Any]:
        """
        서버 상태를 반환합니다.

        Returns:
            서버 상태 정보
        """
        from datetime import datetime

        uptime = None
        if self._server_start_time:
            uptime = (datetime.now() - self._server_start_time).total_seconds()

        return {
            "name": self.name,
            "status": "running",
            "port": self.port,
            "host": self.host,
            "debug": self.debug,
            "instructions": self.server_instructions,
            "uptime_seconds": uptime,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": (self._error_count / max(self._request_count, 1)) * 100,
            "middleware_stats": (
                self.middleware.get_service_stats()
                if hasattr(self, "middleware")
                else {}
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 도구 목록을 반환합니다.

        Returns:
            도구 목록
        """
        # FastMCP에서 등록된 도구들을 가져옴
        tools = []
        if hasattr(self.mcp, "tools"):
            for tool_name, tool_info in self.mcp.tools.items():
                tools.append(
                    {
                        "name": tool_name,
                        "description": getattr(tool_info, "description", ""),
                        "parameters": getattr(tool_info, "parameters", {}),
                    }
                )
        return tools

    def get_health_status(self) -> Dict[str, Any]:
        """
        서버 헬스 상태를 반환합니다.

        Returns:
            헬스 상태 정보
        """
        try:
            # 기본 헬스 체크
            health_status = {
                "status": "healthy",
                "service": self.name,
                "timestamp": self.get_server_status()["timestamp"],
                "checks": {
                    "server_running": True,
                    "clients_initialized": hasattr(self, "_clients_initialized")
                    and self._clients_initialized,
                    "tools_registered": True,  # FastMCP에서 도구는 자동으로 등록됨
                    "middleware_active": hasattr(self, "middleware")
                    and self.middleware.is_active(),
                },
            }

            # 실패한 체크가 있으면 상태를 unhealthy로 변경
            failed_checks = [
                check for check, status in health_status["checks"].items() if not status
            ]
            if failed_checks:
                health_status["status"] = "unhealthy"
                health_status["failed_checks"] = failed_checks

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "service": self.name,
                "error": str(e),
                "timestamp": self.get_server_status()["timestamp"],
            }

    def _setup_health_endpoints(self):
        """Health Check 엔드포인트 설정"""
        from starlette.responses import JSONResponse

        @self.mcp.custom_route("/health", methods=["GET"])
        async def health_check(request):
            """Docker Health Check용 엔드포인트"""
            return JSONResponse(
                {
                    "status": "healthy",
                    "service": self.name,
                    "timestamp": self.get_server_status()["timestamp"],
                }
            )

        @self.mcp.custom_route("/metrics", methods=["GET"])
        async def metrics_endpoint(request):
            """메트릭 엔드포인트"""
            return JSONResponse(self.get_metrics())

    async def start_server(self):
        """서버를 시작합니다."""
        try:
            self.logger.info(f"서버 시작 중: {self.host}:{self.port}")

            # 서버 시작 시간 기록
            from datetime import datetime

            self._server_start_time = datetime.now()

            # FastMCP 서버는 run 메서드로 실행되므로 여기서는 상태만 기록
            self.logger.info(f"서버 시작 준비 완료: {self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"서버 시작 실패: {e}")
            raise

    async def stop_server(self):
        """서버를 중지합니다."""
        try:
            self.logger.info("서버 중지 중...")

            # FastMCP 서버는 별도의 중지 메서드가 없으므로 로그만 기록
            self.logger.info("서버 중지 완료")

        except Exception as e:
            self.logger.error(f"서버 중지 실패: {e}")
            raise

    def run_server(self):
        """서버를 실행합니다 (HTTP 모드)."""
        try:
            self.logger.info(f"FastMCP 서버 시작: {self.host}:{self.port}")

            # FastMCP 서버 실행 (헬스체크는 custom_route로 포함됨)
            self.mcp.run(transport="http", host=self.host, port=self.port)

        except Exception as e:
            self.logger.error(f"FastMCP 서버 실행 실패: {e}")
            raise

    def run_stdio(self):
        """서버를 stdio 모드로 실행합니다."""
        try:
            self.logger.info("stdio 모드로 서버 실행 중...")
            self.mcp.run_stdio_async()
        except Exception as e:
            self.logger.error(f"stdio 모드 실행 실패: {e}")
            raise

    def stdio_communication(self):
        """stdio 통신을 처리합니다."""
        self.logger.info("stdio 통신 모드로 실행 중...")
        # FastMCP에서 stdio 통신을 처리하므로 여기서는 기본 구현만

    def increment_request_count(self):
        """요청 카운트를 증가시킵니다."""
        self._request_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        서버 메트릭을 반환합니다.

        Returns:
            서버 메트릭 정보
        """
        return {
            "server_name": self.name,
            "uptime_seconds": self.get_server_status().get("uptime_seconds", 0),
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": (self._error_count / max(self._request_count, 1)) * 100,
            "middleware_stats": (
                self.middleware.get_service_stats()
                if hasattr(self, "middleware")
                else {}
            ),
            "timestamp": self.get_server_status()["timestamp"],
        }
