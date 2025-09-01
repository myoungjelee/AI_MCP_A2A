"""
Kiwoom API 연동 MCP 서버 (개발 기술 중심)

키움증권 API를 연동하는 단순한 MCP 서버입니다.
실제 트레이딩 로직은 제거하고 API 연동 기술을 어필합니다.
"""

import logging
from typing import Any, Dict

from ..base.base_mcp_server import BaseMCPServer
from ..base.config import MCPServerConfig
from .client import KiwoomClient, KiwoomError


class KiwoomMCPServer(BaseMCPServer):
    """키움 API 연동 MCP 서버 (BaseMCPServer 상속)"""

    def __init__(self, port: int = 8044, host: str = "0.0.0.0", debug: bool = False, **kwargs):
        # 기본 설정
        config = MCPServerConfig.from_env(name="kiwoom")
        config.port = port
        config.host = host
        config.debug = debug
        
        # 미들웨어 설정
        middleware_config = {
            "logging": {
                "log_level": "DEBUG" if debug else "INFO",
                "include_traceback": debug,
            },
            "error_handling": {
                "include_traceback": debug,
            },
        }

        super().__init__(
            name="kiwoom",
            port=port,
            host=host,
            debug=debug,
            server_instructions="키움 API 연동 시스템 - 주식 데이터 조회 및 계좌 정보 제공",
            config=config,
            enable_middlewares=True,
            middleware_config=middleware_config,
            **kwargs
        )

    def _initialize_clients(self) -> None:
        """키움 클라이언트 초기화"""
        try:
            self.kiwoom_client = KiwoomClient(name="mcp_server_client")
            self._clients_initialized = True
            self.logger.info("Kiwoom client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize kiwoom client: {e}")
            self.kiwoom_client = None
            self._clients_initialized = False

    def _register_tools(self):
        """MCP 도구들을 등록합니다."""
        try:
            # 미들웨어 적용
            if self.kiwoom_client:
                # 클라이언트 메서드에 미들웨어 적용
                self.kiwoom_client.get_stock_price = self.middleware.apply_all("주식 가격 조회")(
                    self.kiwoom_client.get_stock_price
                )
                self.kiwoom_client.get_account_info = self.middleware.apply_all("계좌 정보 조회")(
                    self.kiwoom_client.get_account_info
                )
                self.kiwoom_client.get_stock_info = self.middleware.apply_all("주식 정보 조회")(
                    self.kiwoom_client.get_stock_info
                )
                self.kiwoom_client.get_market_status = self.middleware.apply_all("시장 상태 조회")(
                    self.kiwoom_client.get_market_status
                )

            @self.mcp.tool()
            async def get_stock_price(stock_code: str) -> Dict[str, Any]:
                """특정 종목의 현재 가격 정보를 조회합니다"""
                try:
                    if not self.kiwoom_client:
                        return self.create_error_response(
                            "get_stock_price",
                            "Kiwoom client not initialized",
                            f"get_stock_price: {stock_code}",
                        )

                    result = await self.kiwoom_client.get_stock_price(stock_code)
                    return self.create_standard_response(
                        success=True,
                        query=f"get_stock_price: {stock_code}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "get_stock_price",
                        e,
                        f"get_stock_price: {stock_code}",
                    )

            @self.mcp.tool()
            async def get_account_info() -> Dict[str, Any]:
                """연결된 계좌의 기본 정보를 조회합니다"""
                try:
                    if not self.kiwoom_client:
                        return self.create_error_response(
                            "get_account_info",
                            "Kiwoom client not initialized",
                            "get_account_info",
                        )

                    result = await self.kiwoom_client.get_account_info()
                    return self.create_standard_response(
                        success=True,
                        query="get_account_info",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "get_account_info",
                        e,
                        "get_account_info",
                    )

            @self.mcp.tool()
            async def get_stock_info(stock_code: str) -> Dict[str, Any]:
                """특정 종목의 기본 정보를 조회합니다"""
                try:
                    if not self.kiwoom_client:
                        return self.create_error_response(
                            "get_stock_info",
                            "Kiwoom client not initialized",
                            f"get_stock_info: {stock_code}",
                        )

                    result = await self.kiwoom_client.get_stock_info(stock_code)
                    return self.create_standard_response(
                        success=True,
                        query=f"get_stock_info: {stock_code}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "get_stock_info",
                        e,
                        f"get_stock_info: {stock_code}",
                    )

            @self.mcp.tool()
            async def get_market_status() -> Dict[str, Any]:
                """현재 시장 상태를 조회합니다"""
                try:
                    if not self.kiwoom_client:
                        return self.create_error_response(
                            "get_market_status",
                            "Kiwoom client not initialized",
                            "get_market_status",
                        )

                    result = await self.kiwoom_client.get_market_status()
                    return self.create_standard_response(
                        success=True,
                        query="get_market_status",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "get_market_status",
                        e,
                        "get_market_status",
                    )

            # 서버 상태 및 메트릭 도구 추가
            @self.mcp.tool()
            async def get_server_health() -> Dict[str, Any]:
                """서버 헬스 상태 조회"""
                return self.get_health_status()

            @self.mcp.tool()
            async def get_server_metrics() -> Dict[str, Any]:
                """서버 메트릭 조회"""
                return self.get_metrics()

            self.logger.info("Kiwoom MCP tools registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise


def main():
    """메인 함수"""
    import asyncio
    
    async def run_server():
        server = KiwoomMCPServer(port=8044, debug=True)
        await server.start_server()
        
        try:
            # 서버 실행 중 대기
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await server.stop_server()
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
