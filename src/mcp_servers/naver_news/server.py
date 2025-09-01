"""네이버 뉴스 MCP 서버 - 단순화된 버전

BaseMCPServer 패턴을 활용하여 핵심 뉴스 수집 및 감정 분석 기능에 집중한
간소한 구조로 구성된 뉴스 분석 전문 서버입니다.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_servers.base.base_mcp_server import BaseMCPServer  # noqa: E402
from src.mcp_servers.naver_news.client import NewsClient  # noqa: E402

logger = logging.getLogger(__name__)


class NaverNewsMCPServer(BaseMCPServer):
    """네이버 뉴스 MCP 서버 구현"""

    def __init__(
        self,
        server_name: str = "Naver News MCP Server",
        port: int = 8051,
        host: str = "0.0.0.0",
        debug: bool = False,
        **kwargs,
    ):
        """
        네이버 뉴스 MCP 서버 초기화

        Args:
            server_name: 서버 이름
            port: 서버 포트
            host: 호스트 주소
            debug: 디버그 모드
            **kwargs: 추가 옵션
        """
        # 기본 미들웨어 설정 (현재 지원되는 미들웨어만)
        default_middlewares = ["logging", "error_handling"]
        middleware_config = {
            "logging": {
                "log_requests": True,
                "log_responses": debug,
            },
            "error_handling": {
                "include_traceback": debug,
            },
        }

        super().__init__(
            name=server_name,
            port=port,
            host=host,
            debug=debug,
            server_instructions="네이버 뉴스 검색, 감정 분석, 주식 관련 뉴스 필터링 등 뉴스 기반 투자 정보를 제공합니다",
            enable_middlewares=kwargs.get("enable_middlewares", default_middlewares),
            middleware_config=kwargs.get("middleware_config", middleware_config),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["enable_middlewares", "middleware_config"]
            },
        )

    def _initialize_clients(self) -> None:
        """뉴스 분석 클라이언트 초기화"""
        try:
            # 환경변수 검증
            self._validate_environment()

            # 뉴스 클라이언트 초기화
            self.news_client = NewsClient()

            logger.info("News analysis client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize news analysis client: {e}")
            # 필수 환경변수 누락으로 인한 실패는 서버 시작 중단
            if "필수 환경변수" in str(e) or "NAVER_CLIENT" in str(e):
                raise
            self.news_client = None

    def _validate_environment(self) -> None:
        """환경변수 검증 - 필수"""
        # 필수 환경변수들
        required_vars = ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            error_msg = (
                f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _register_tools(self) -> None:
        """MCP 도구들을 등록"""

        # === 뉴스 검색 도구들 ===

        @self.mcp.tool()
        async def search_news_articles(
            query: str,
            max_articles: int = 10,
            sort_by: str = "date",
        ) -> dict[str, Any]:
            """
            네이버 뉴스 검색

            Args:
                query: 검색 키워드
                max_articles: 최대 기사 수 (기본 10개)
                sort_by: 정렬 방식 ("date" 또는 "sim")

            Returns:
                검색된 뉴스 기사 리스트
            """
            try:
                if not self.news_client:
                    return self.create_error_response(
                        error="NewsClient not initialized",
                        func_name="search_news_articles",
                        query=query,
                    )

                result = await self.news_client.search_news(
                    query=query, display=max_articles, sort=sort_by
                )

                return self.create_standard_response(
                    success=True,
                    query=f"search_news_articles: {query}",
                    data={
                        "query": query,
                        "total_found": len(result),
                        "articles": result,
                    },
                )

            except Exception as e:
                return await self.create_error_response(
                    func_name="search_news_articles",
                    error=e,
                    query=query,
                )

        @self.mcp.tool()
        async def get_stock_news(
            symbol: str,
            company_name: str = "",
            days_back: int = 7,
            max_articles: int = 30,
        ) -> dict[str, Any]:
            """
            주식 관련 뉴스 수집

            Args:
                symbol: 한국주식 종목코드
                company_name: 회사명 (선택사항)
                days_back: 수집 기간 (일수)
                max_articles: 최대 기사 수

            Returns:
                주식 관련 필터링된 뉴스 리스트
            """
            try:
                if not self.news_client:
                    return self.create_error_response(
                        query=f"get_stock_news: {symbol}",
                        error="NewsClient not initialized",
                        func_name="get_stock_news",
                    )

                result = await self.news_client.get_stock_related_news(
                    stock_symbol=symbol,
                    max_results=max_articles,
                )

                return self.create_standard_response(
                    success=True,
                    query=f"get_stock_news: {symbol}",
                    data={
                        "symbol": symbol,
                        "company_name": company_name,
                        "total_found": len(result),
                        "articles": result,
                        "collection_period_days": days_back,
                    },
                )

            except Exception as e:
                return self.create_error_response(
                    func_name="get_stock_news",
                    error=e,
                    symbol=symbol,
                )


def main():
    """메인 함수"""
    import asyncio

    # 서버 인스턴스 생성
    server = NaverNewsMCPServer(port=8051, debug=True)

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
