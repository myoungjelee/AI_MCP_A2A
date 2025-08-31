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

from fastmcp import FastMCP

from .client import FinancialAnalysisClient


class FinancialAnalysisMCPServer:
    """재무 분석 시스템 MCP 서버"""

    def __init__(
        self, name: str = "financial_analysis", port: int = 8040, host: str = "0.0.0.0"
    ):
        self.name = name
        self.port = port
        self.host = host

        # FastMCP 서버 초기화
        self.mcp = FastMCP(
            name=name,
            instructions="재무 데이터 수집, 재무비율 계산, DCF 밸류에이션, 투자 분석 리포트 생성 등 재무 분석 기능을 제공합니다",
        )

        # 클라이언트 초기화
        self.financial_client = FinancialAnalysisClient()

        # 도구 등록
        self._register_tools()

        self.logger = logging.getLogger(f"financial_analysis.{name}")
        self._setup_logging()
        self.logger.info("재무 분석 MCP 서버 초기화 완료")

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _register_tools(self):
        """MCP 도구들을 등록합니다"""

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
                result = await self.financial_client.get_financial_data(
                    symbol, data_type
                )
                return {
                    "success": True,
                    "query": f"get_financial_data: {symbol}",
                    "data": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "query": f"get_financial_data: {symbol}",
                    "error": str(e),
                    "func_name": "get_financial_data",
                }

        @self.mcp.tool()
        async def calculate_financial_ratios(symbol: str) -> Dict[str, Any]:
            """
            재무비율 계산

            Args:
                symbol: 종목코드

            Returns:
                수익성, 안전성, 활동성 비율 분석 결과
            """
            try:
                financial_data = await self.financial_client.get_financial_data(symbol)
                ratios = self.financial_client.calculate_financial_ratios(
                    financial_data
                )

                result = {
                    "symbol": symbol,
                    "financial_ratios": ratios,
                    "ratio_analysis": {
                        "roe_assessment": (
                            "우수"
                            if ratios["profitability"]["roe"] >= 12
                            else (
                                "양호"
                                if ratios["profitability"]["roe"] >= 8
                                else "개선필요"
                            )
                        ),
                        "debt_assessment": (
                            "안전"
                            if ratios["stability"]["debt_to_equity"] <= 100
                            else (
                                "주의"
                                if ratios["stability"]["debt_to_equity"] <= 200
                                else "위험"
                            )
                        ),
                        "efficiency_assessment": (
                            "우수"
                            if ratios["activity"]["asset_turnover"] >= 1.2
                            else (
                                "양호"
                                if ratios["activity"]["asset_turnover"] >= 0.7
                                else "개선필요"
                            )
                        ),
                    },
                }

                return {
                    "success": True,
                    "query": f"calculate_financial_ratios: {symbol}",
                    "data": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "query": f"calculate_financial_ratios: {symbol}",
                    "error": str(e),
                    "func_name": "calculate_financial_ratios",
                }

        @self.mcp.tool()
        async def perform_dcf_valuation(
            symbol: str,
            growth_rate: float = 5.0,
            terminal_growth: float = 2.5,
            discount_rate: float = 10.0,
            projection_years: int = 5,
        ) -> Dict[str, Any]:
            """
            DCF 밸류에이션 수행

            Args:
                symbol: 종목코드
                growth_rate: 성장률 (%)
                terminal_growth: 영구성장률 (%)
                discount_rate: 할인율 (%)
                projection_years: 예측 연도 수

            Returns:
                DCF 밸류에이션 결과 및 적정주가
            """
            try:
                result = await self.financial_client.calculate_dcf_valuation(
                    symbol,
                    growth_rate=growth_rate,
                    terminal_growth=terminal_growth,
                    discount_rate=discount_rate,
                    projection_years=projection_years,
                )

                return {
                    "success": True,
                    "query": f"perform_dcf_valuation: {symbol}",
                    "data": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "query": f"perform_dcf_valuation: {symbol}",
                    "error": str(e),
                    "func_name": "perform_dcf_valuation",
                }

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
                result = await self.financial_client.generate_investment_report(symbol)

                return {
                    "success": True,
                    "query": f"generate_investment_report: {symbol}",
                    "data": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "query": f"generate_investment_report: {symbol}",
                    "error": str(e),
                    "func_name": "generate_investment_report",
                }

        @self.mcp.tool()
        async def compare_peer_valuation(
            symbols: str, valuation_metrics: str = "per,pbr"
        ) -> Dict[str, Any]:
            """
            동종업계 밸류에이션 비교

            Args:
                symbols: 비교할 종목코드 (쉼표로 구분된 문자열, 예: "005930,000660")
                valuation_metrics: 비교할 밸류에이션 지표 (쉼표로 구분, 기본값: "per,pbr")

            Returns:
                동종업계 대비 밸류에이션 비교 결과
            """
            try:
                # 입력 검증 및 변환
                symbols_list = [s.strip() for s in symbols.split(",") if s.strip()]
                if not symbols_list:
                    return {
                        "success": False,
                        "query": f"compare_peer_valuation: {symbols}",
                        "error": "종목코드 리스트가 비어있습니다",
                        "func_name": "compare_peer_valuation",
                    }

                metrics_list = [
                    m.strip() for m in valuation_metrics.split(",") if m.strip()
                ]
                if not metrics_list:
                    metrics_list = ["per", "pbr"]

                # 유효한 메트릭 검증
                valid_metrics = ["per", "pbr"]
                metrics_list = [m for m in metrics_list if m in valid_metrics]

                if not metrics_list:
                    return {
                        "success": False,
                        "query": f"compare_peer_valuation: {symbols}",
                        "error": "유효한 밸류에이션 지표가 없습니다. 사용 가능: per, pbr",
                        "func_name": "compare_peer_valuation",
                    }

                # 각 종목별 재무 데이터 수집
                comparison_results = {}
                for symbol in symbols_list:
                    try:
                        financial_data = await self.financial_client.get_financial_data(
                            symbol
                        )
                        market_data = financial_data.get("market_data", {})

                        comparison_results[symbol] = {
                            "company_name": financial_data.get("company_name", symbol),
                            "current_price": market_data.get("current_price", 0),
                            "market_cap": market_data.get("market_cap", 0),
                            "data_source": "FinanceDataReader",
                        }
                    except Exception as e:
                        comparison_results[symbol] = {
                            "error": f"데이터 조회 실패: {str(e)}"
                        }

                result = {
                    "comparison_data": comparison_results,
                    "methodology": "실제 재무 데이터 기반 동종업계 밸류에이션 비교",
                    "data_source": "FinanceDataReader (실제 데이터)",
                }

                return {
                    "success": True,
                    "query": f"compare_peer_valuation: {len(symbols_list)} symbols",
                    "data": result,
                }

            except Exception as e:
                return {
                    "success": False,
                    "query": f"compare_peer_valuation: {symbols}",
                    "error": str(e),
                    "func_name": "compare_peer_valuation",
                }

        self.logger.info("재무 분석 MCP 서버에 5개 도구 등록 완료")

    def run(self):
        """FastMCP 서버를 실행합니다"""
        try:
            self.logger.info(f"서버 시작: {self.host}:{self.port}")
            self.mcp.run(transport="streamable-http", host=self.host, port=self.port)
        except KeyboardInterrupt:
            self.logger.info("사용자에 의해 서버가 중단되었습니다")
        except Exception as e:
            self.logger.error(f"서버 실행 중 오류 발생: {e}")
            raise


if __name__ == "__main__":
    # 서버 생성 및 실행
    server = FinancialAnalysisMCPServer()
    server.run()
