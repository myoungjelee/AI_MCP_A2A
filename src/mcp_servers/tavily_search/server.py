"""
검색 시스템 MCP 서버 - FastMCP 기반
웹 검색, 뉴스 검색, 금융 정보 검색을 제공합니다.
복잡한 AI 기능 대신 깔끔한 코드 구조와 효율적인 검색 알고리즘을 보여줍니다.
"""

import logging
from typing import Any, Dict

from fastmcp import FastMCP

from .client import TavilySearchClient


class TavilySearchMCPServer:
    """검색 시스템 MCP 서버 (FastMCP 기반)"""

    def __init__(self, port: int = 3020, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.mcp = FastMCP("search_system")
        self.mcp.description = (
            "웹 검색, 뉴스 검색, 금융 정보 검색을 위한 MCP 서버 (개발 기술 중심)"
        )

        # 클라이언트 초기화
        self.search_client = TavilySearchClient()

        # 도구 등록
        self._register_tools()

        logging.info("검색 시스템 MCP 서버 초기화 완료")

    def _register_tools(self):
        """MCP 도구들을 등록합니다."""

        @self.mcp.tool()
        async def search_web(query: str, max_results: int = 10) -> Dict[str, Any]:
            """웹 검색 수행 (캐싱 + 재시도 로직)"""
            try:
                result = await self.search_client.search_web(query, max_results)
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "웹 검색에 실패했습니다",
                }

        @self.mcp.tool()
        async def search_news(query: str, max_results: int = 10) -> Dict[str, Any]:
            """뉴스 검색 수행 (캐싱 + 재시도 로직)"""
            try:
                result = await self.search_client.search_news(query, max_results)
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "뉴스 검색에 실패했습니다",
                }

        @self.mcp.tool()
        async def search_finance(query: str, max_results: int = 10) -> Dict[str, Any]:
            """금융 정보 검색 수행 (캐싱 + 재시도 로직)"""
            try:
                result = await self.search_client.search_finance(query, max_results)
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "금융 정보 검색에 실패했습니다",
                }

        logging.info("검색 시스템 MCP 도구 3개 등록 완료")

    def run(self):
        """서버를 실행합니다."""
        try:
            logging.info(f"검색 시스템 MCP 서버 시작: {self.host}:{self.port}")
            self.mcp.run(transport="streamable-http", host=self.host, port=self.port)
        except Exception as e:
            logging.error(f"서버 실행 실패: {e}")
            raise


if __name__ == "__main__":
    try:
        # 서버 생성 및 실행
        server = TavilySearchMCPServer()
        server.run()
    except KeyboardInterrupt:
        logging.info("서버 중단 신호 수신")
    except Exception as e:
        logging.error(f"서버 오류: {e}")
        raise
    finally:
        logging.info("검색 시스템 MCP 서버 종료")
