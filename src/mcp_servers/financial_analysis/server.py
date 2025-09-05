"""
재무 분석 시스템 MCP 서버 - FastMCP 기반

핵심 재무 분석 기능을 제공하는 MCP 서버입니다.
실제 데이터를 사용하여 MCP, FastMCP, 비동기 처리 기술을 보여줍니다.

주요 기능:
- 재무 데이터 수집 및 분석
- 재무비율 계산
- DCF 밸류에이션
- 투자 분석 리포트 생성

개발 기술:
- FastMCP 기반 MCP 서버
- 비동기 처리 (asyncio)
- 에러 처리 및 로깅
- 데이터 구조화
"""

import logging
from typing import Any, Dict, Literal

from ..base.base_mcp_server import BaseMCPServer
from .client import FinancialAnalysisClient


class FinancialAnalysisMCPServer(BaseMCPServer):
    """재무 분석 시스템 MCP 서버 (BaseMCPServer 상속)"""

    def __init__(self, port: int = 8040, debug: bool = False):
        super().__init__("financial_analysis", port=port, debug=debug)

    def _initialize_clients(self) -> None:
        """재무 분석 클라이언트 초기화"""
        try:
            self.financial_client = FinancialAnalysisClient()
            self._clients_initialized = True
            self.logger.info("Financial analysis client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize financial analysis client: {e}")
            self.financial_client = None
            self._clients_initialized = False

    def _register_tools(self):
        """MCP 도구들을 등록합니다"""
        try:
            # 미들웨어 적용
            if self.financial_client:
                # 클라이언트 메서드에 미들웨어 적용
                self.financial_client.get_financial_data = self.middleware.apply_all(
                    "재무 데이터 조회"
                )(self.financial_client.get_financial_data)
                self.financial_client.calculate_financial_ratios = (
                    self.middleware.apply_all("재무비율 계산")(
                        self.financial_client.calculate_financial_ratios
                    )
                )
                self.financial_client.calculate_dcf_valuation = (
                    self.middleware.apply_all("DCF 밸류에이션")(
                        self.financial_client.calculate_dcf_valuation
                    )
                )
                self.financial_client.generate_investment_report = (
                    self.middleware.apply_all("투자 분석 리포트 생성")(
                        self.financial_client.generate_investment_report
                    )
                )

            @self.mcp.tool()
            async def get_financial_data(
                symbol: str,
                data_type: Literal["income", "balance", "cashflow", "all"] = "all",
            ) -> Dict[str, Any]:
                """
                재무 데이터 조회

                Args:
                    symbol: 종목코드
                    data_type: 데이터 타입 (income, balance, cashflow, all)

                Returns:
                    재무 데이터 (손익계산서, 재무상태표, 현금흐름표, 시장 데이터)
                """
                try:
                    if not self.financial_client:
                        return self.create_error_response(
                            "get_financial_data",
                            "Financial client not initialized",
                            f"get_financial_data: {symbol}",
                        )

                    result = await self.financial_client.get_financial_data(
                        symbol, data_type
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"get_financial_data: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "get_financial_data",
                        e,
                        f"get_financial_data: {symbol}",
                    )

            @self.mcp.tool()
            async def calculate_financial_ratios(symbol: str) -> Dict[str, Any]:
                """
                재무비율 계산

                Args:
                    symbol: 종목코드

                Returns:
                    주요 재무비율 (ROE, ROA, 부채비율, 유동비율 등)
                """
                try:
                    if not self.financial_client:
                        return self.create_error_response(
                            "calculate_financial_ratios",
                            "Financial client not initialized",
                            f"calculate_financial_ratios: {symbol}",
                        )

                    result = await self.financial_client.calculate_financial_ratios(
                        symbol
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"calculate_financial_ratios: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "calculate_financial_ratios",
                        e,
                        f"calculate_financial_ratios: {symbol}",
                    )

            @self.mcp.tool()
            async def perform_dcf_valuation(
                symbol: str, growth_rate: float = 5.0, discount_rate: float = 10.0
            ) -> Dict[str, Any]:
                """
                DCF 밸류에이션 수행

                Args:
                    symbol: 종목코드
                    growth_rate: 성장률 (%)
                    discount_rate: 할인율 (%)

                Returns:
                    DCF 밸류에이션 결과 (내재가치, 적정주가 등)
                """
                try:
                    if not self.financial_client:
                        return self.create_error_response(
                            "perform_dcf_valuation",
                            "Financial client not initialized",
                            f"perform_dcf_valuation: {symbol}",
                        )

                    result = await self.financial_client.calculate_dcf_valuation(
                        symbol, growth_rate=growth_rate, discount_rate=discount_rate
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"perform_dcf_valuation: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "perform_dcf_valuation",
                        e,
                        f"perform_dcf_valuation: {symbol}",
                    )

            @self.mcp.tool()
            async def generate_investment_report(symbol: str) -> Dict[str, Any]:
                """
                투자 분석 리포트 생성

                Args:
                    symbol: 종목코드

                Returns:
                    종합 투자 분석 리포트
                """
                try:
                    if not self.financial_client:
                        return self.create_error_response(
                            "generate_investment_report",
                            "Financial client not initialized",
                            f"generate_investment_report: {symbol}",
                        )

                    result = await self.financial_client.generate_investment_report(
                        symbol
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"generate_investment_report: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "generate_investment_report",
                        e,
                        f"generate_investment_report: {symbol}",
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

            self.logger.info(
                "Financial analysis MCP tools and HTTP endpoints registered successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise


def main():
    """메인 함수"""
    import asyncio

    # 로거 설정
    logger = logging.getLogger(__name__)

    # 서버 인스턴스 생성
    server = FinancialAnalysisMCPServer(port=8040, debug=True)

    try:
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
