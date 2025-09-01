"""
검색 시스템 MCP 서버 - FastMCP 기반
웹 검색, 뉴스 검색, 금융 정보 검색을 제공합니다.
복잡한 AI 기능 대신 깔끔한 코드 구조와 효율적인 검색 알고리즘을 보여줍니다.
"""

import logging
from typing import Any, Dict

from ..base.base_mcp_server import BaseMCPServer
from ..base.config import MCPServerConfig
from .client import TavilySearchClient

logger = logging.getLogger(__name__)


class TavilySearchMCPServer(BaseMCPServer):
    """검색 시스템 MCP 서버 (BaseMCPServer 상속)"""

    def __init__(
        self, port: int = 8053, host: str = "0.0.0.0", debug: bool = False, **kwargs
    ):
        # 기본 설정
        config = MCPServerConfig.from_env(name="tavily_search")
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
            name="tavily_search",
            port=port,
            host=host,
            debug=debug,
            server_instructions="웹 검색, 뉴스 검색, 금융 정보 검색을 위한 MCP 서버 (개발 기술 중심)",
            config=config,
            enable_middlewares=True,
            middleware_config=middleware_config,
            **kwargs,
        )

    def _initialize_clients(self) -> None:
        """검색 클라이언트 초기화"""
        try:
            self.search_client = TavilySearchClient()
            self._clients_initialized = True
            self.logger.info("Tavily search client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize tavily search client: {e}")
            self.search_client = None
            self._clients_initialized = False

    def _register_tools(self):
        """MCP 도구들을 등록합니다."""
        try:
            # 미들웨어 적용
            if self.search_client:
                # 클라이언트 메서드에 미들웨어 적용
                self.search_client.search_web = self.middleware.apply_all("웹 검색")(
                    self.search_client.search_web
                )
                self.search_client.search_news = self.middleware.apply_all("뉴스 검색")(
                    self.search_client.search_news
                )
                self.search_client.search_finance = self.middleware.apply_all(
                    "금융 정보 검색"
                )(self.search_client.search_finance)

            @self.mcp.tool()
            async def search_web(query: str, max_results: int = 10) -> Dict[str, Any]:
                """웹 검색 수행 (캐싱 + 재시도 로직)"""
                try:
                    if not self.search_client:
                        return self.create_error_response(
                            "search_web",
                            "Search client not initialized",
                            f"search_web: {query}",
                        )

                    result = await self.search_client.search_web(query, max_results)
                    return self.create_standard_response(
                        success=True,
                        query=f"search_web: {query}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "search_web",
                        e,
                        f"search_web: {query}",
                    )

            @self.mcp.tool()
            async def search_news(query: str, max_results: int = 10) -> Dict[str, Any]:
                """뉴스 검색 수행 (캐싱 + 재시도 로직)"""
                try:
                    if not self.search_client:
                        return self.create_error_response(
                            "search_news",
                            "Search client not initialized",
                            f"search_news: {query}",
                        )

                    result = await self.search_client.search_news(query, max_results)
                    return self.create_standard_response(
                        success=True,
                        query=f"search_news: {query}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "search_news",
                        e,
                        f"search_news: {query}",
                    )

            @self.mcp.tool()
            async def search_finance(
                query: str, max_results: int = 10
            ) -> Dict[str, Any]:
                """금융 정보 검색 수행 (캐싱 + 재시도 로직)"""
                try:
                    if not self.search_client:
                        return self.create_error_response(
                            "search_finance",
                            "Search client not initialized",
                            f"search_finance: {query}",
                        )

                    result = await self.search_client.search_finance(query, max_results)
                    return self.create_standard_response(
                        success=True,
                        query=f"search_finance: {query}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "search_finance",
                        e,
                        f"search_finance: {query}",
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

            self.logger.info("Tavily search MCP tools registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise


def main():
    """메인 함수"""
    import asyncio

    # 서버 인스턴스 생성
    server = TavilySearchMCPServer(port=8053, debug=True)

    try:
        # 서버 시작 준비
        asyncio.run(server.start_server())

        # FastMCP 서버 실행 (HTTP 모드)
        server.run_server()

    except KeyboardInterrupt:
        logger.info("서버가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {e}")
    finally:
        # 서버 정리
        asyncio.run(server.stop_server())


if __name__ == "__main__":
    main()
