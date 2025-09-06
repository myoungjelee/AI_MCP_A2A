"""
FinanceDataReader 연동 MCP 서버

- 기존 KiwoomMCPServer → FDRMCPServer 로 대체
- BaseMCPServer 상속, 미들웨어/표준 응답 포맷은 기존과 동일하게 사용
- 실시간/계좌/체결/호가/외국인동향 등은 미지원 처리
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from ..base.base_mcp_server import BaseMCPServer  # 프로젝트 공용 베이스
from ..base.config import MCPServerConfig
from .client import FinanceDataReaderClient

logger = logging.getLogger(__name__)


class FDRMCPServer(BaseMCPServer):
    """FinanceDataReader 연동 MCP 서버"""

    def __init__(
        self, port: int = 8030, host: str = "0.0.0.0", debug: bool = False, **kwargs
    ):
        config = MCPServerConfig.from_env(name="fdr")
        config.port = port
        config.host = host
        config.debug = debug

        super().__init__(
            name="fdr",
            port=port,
            host=host,
            debug=debug,
            server_instructions="FinanceDataReader 기반 한국 주식 데이터 제공 (일봉/리스트/검색/지수)",
            config=config,
            enable_middlewares=True,
            middleware_config={
                "logging": {
                    "log_level": "DEBUG" if debug else "INFO",
                    "include_traceback": debug,
                },
                "error_handling": {"include_traceback": debug},
            },
            **kwargs,
        )

    # ----- lifecycle -----

    def _initialize_clients(self) -> None:
        try:
            self.fdr_client = FinanceDataReaderClient(name="mcp_server_client")
            self._clients_initialized = True
            self.logger.info("FDR client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize FDR client: {e}")
            self.fdr_client = None
            self._clients_initialized = False

    def _register_tools(self) -> None:
        if not getattr(self, "fdr_client", None):
            self.logger.error(
                "FDR client not initialized; tools will not be registered."
            )
            return

        # 미들웨어 적용 (가능하면)
        # wrap = self.middleware.apply_all

        # ===== 지원 도구 =====

        @self.mcp.tool()
        async def get_stock_basic_info(stock_code: str) -> Dict[str, Any]:
            """일일 종가 기반 기본정보(변동률 포함)"""
            try:
                res = await self.fdr_client.get_stock_basic_info(stock_code)
                return self.create_standard_response(
                    success=True, query=f"get_stock_basic_info:{stock_code}", data=res
                )
            except Exception as e:
                return self.create_error_response(
                    "get_stock_basic_info", e, f"{stock_code}"
                )

        @self.mcp.tool()
        async def get_stock_info(stock_code: str) -> Dict[str, Any]:
            """상장정보(이름, 섹터 등). FDR StockListing 기반."""
            try:
                res = await self.fdr_client.get_stock_info(stock_code)
                return self.create_standard_response(
                    success=True, query=f"get_stock_info:{stock_code}", data=res
                )
            except Exception as e:
                return self.create_error_response("get_stock_info", e, f"{stock_code}")

        @self.mcp.tool()
        async def get_stock_list(market_type: str = "ALL") -> Dict[str, Any]:
            """종목 리스트(KRX/KOSPI/KOSDAQ)"""
            try:
                res = await self.fdr_client.get_stock_list(market_type)
                return self.create_standard_response(
                    success=True, query=f"get_stock_list:{market_type}", data=res
                )
            except Exception as e:
                return self.create_error_response("get_stock_list", e, f"{market_type}")

        @self.mcp.tool()
        async def get_daily_chart(
            stock_code: str, start_date: str | None = None, end_date: str | None = None
        ) -> Dict[str, Any]:
            """일봉 OHLCV (YYYYMMDD/ISO 범위)"""
            try:
                res = await self.fdr_client.get_daily_chart(
                    stock_code, start_date, end_date
                )
                return self.create_standard_response(
                    success=True, query=f"get_daily_chart:{stock_code}", data=res
                )
            except Exception as e:
                return self.create_error_response("get_daily_chart", e, f"{stock_code}")

        @self.mcp.tool()
        async def search_stock_by_name(
            query: str, limit: int | None = None
        ) -> Dict[str, Any]:
            """종목명 부분검색"""
            try:
                res = await self.fdr_client.search_stock_by_name(query, limit)
                return self.create_standard_response(
                    success=True, query=f"search_stock_by_name:{query}", data=res
                )
            except Exception as e:
                return self.create_error_response("search_stock_by_name", e, f"{query}")

        @self.mcp.tool()
        async def get_market_overview() -> Dict[str, Any]:
            """KOSPI/KOSDAQ 간단 요약"""
            try:
                res = await self.fdr_client.get_market_overview()
                return self.create_standard_response(
                    success=True, query="get_market_overview", data=res
                )
            except Exception as e:
                return self.create_error_response(
                    "get_market_overview", e, "get_market_overview"
                )

        @self.mcp.tool()
        async def get_market_status() -> Dict[str, Any]:
            """간단한 장 상태(09:00~15:30)"""
            try:
                res = await self.fdr_client.get_market_status()
                return self.create_standard_response(
                    success=True, query="get_market_status", data=res
                )
            except Exception as e:
                return self.create_error_response(
                    "get_market_status", e, "get_market_status"
                )

        # ===== 미지원 도구(호환성 유지를 위해 에러 형태로 제공) =====

        def _unsupported(name: str, detail: str):
            @self.mcp.tool(name=name)
            async def _tool() -> Dict[str, Any]:
                return self.create_standard_response(
                    success=False,
                    query=name,
                    data={"error_code": "NOT_SUPPORTED", "message": detail},
                )

            return _tool

        _unsupported(
            "get_minute_chart", "FinanceDataReader does not provide minute bars."
        )
        _unsupported(
            "get_stock_orderbook", "FinanceDataReader does not provide orderbook data."
        )
        _unsupported(
            "get_stock_execution_info",
            "FinanceDataReader does not provide tick execution data.",
        )
        _unsupported(
            "get_price_change_ranking",
            "Ranking endpoints are not provided by FinanceDataReader.",
        )
        _unsupported(
            "get_volume_top_ranking",
            "Ranking endpoints are not provided by FinanceDataReader.",
        )
        _unsupported(
            "get_foreign_trading_trend",
            "FinanceDataReader does not provide investor trends.",
        )

        # 서버 자체 상태
        @self.mcp.tool()
        async def get_server_health() -> Dict[str, Any]:
            return self.get_health_status()

        @self.mcp.tool()
        async def get_server_metrics() -> Dict[str, Any]:
            return self.get_metrics()


def main() -> None:
    server = FDRMCPServer(port=8030, debug=True)
    try:
        server.run_server()
    except KeyboardInterrupt:
        logger.info("서버가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {e}")
    finally:
        asyncio.run(server.stop_server())


if __name__ == "__main__":
    main()
