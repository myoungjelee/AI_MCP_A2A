"""
데이터 분석 시스템 MCP 서버 - FastMCP 기반
데이터 트렌드 분석, 통계적 지표 계산, 패턴 인식을 제공합니다.
복잡한 주식 분석 대신 깔끔한 코드 구조와 효율적인 분석 알고리즘을 보여줍니다.
"""

import logging
from typing import Any, Dict

from ..base.base_mcp_server import BaseMCPServer
from .client import StockAnalysisClient

logger = logging.getLogger(__name__)


class StockAnalysisMCPServer(BaseMCPServer):
    """주식 분석 시스템 MCP 서버 (BaseMCPServer 상속)"""

    def __init__(self, port: int = 8052, debug: bool = False):
        super().__init__("stock_analysis", port=port, debug=debug)

    def _initialize_clients(self) -> None:
        """분석 클라이언트 초기화"""
        try:
            self.analysis_client = StockAnalysisClient()
            self._clients_initialized = True
            self.logger.info("Stock analysis client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize stock analysis client: {e}")
            self.analysis_client = None
            self._clients_initialized = False

    def _register_tools(self):
        """MCP 도구들을 등록합니다."""
        try:
            # 미들웨어 적용
            if self.analysis_client:
                # 클라이언트 메서드에 미들웨어 적용
                self.analysis_client.analyze_data_trends = self.middleware.apply_all(
                    "데이터 트렌드 분석"
                )(self.analysis_client.analyze_data_trends)
                self.analysis_client.calculate_statistical_indicators = (
                    self.middleware.apply_all("통계적 지표 계산")(
                        self.analysis_client.calculate_statistical_indicators
                    )
                )
                self.analysis_client.perform_pattern_recognition = (
                    self.middleware.apply_all("패턴 인식")(
                        self.analysis_client.perform_pattern_recognition
                    )
                )

            @self.mcp.tool()
            async def analyze_data_trends(
                symbol: str, period: str = "1y"
            ) -> Dict[str, Any]:
                """데이터 트렌드 분석 수행 (캐싱 + 재시도 로직)"""
                try:
                    if not self.analysis_client:
                        return self.create_error_response(
                            "analyze_data_trends",
                            "Analysis client not initialized",
                            f"analyze_data_trends: {symbol}",
                        )

                    result = await self.analysis_client.analyze_data_trends(
                        symbol, period
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"analyze_data_trends: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "analyze_data_trends",
                        e,
                        f"analyze_data_trends: {symbol}",
                    )

            @self.mcp.tool()
            async def calculate_statistical_indicators(symbol: str) -> Dict[str, Any]:
                """통계적 지표 계산 수행 (캐싱 + 재시도 로직)"""
                try:
                    if not self.analysis_client:
                        return self.create_error_response(
                            "calculate_statistical_indicators",
                            "Analysis client not initialized",
                            f"calculate_statistical_indicators: {symbol}",
                        )

                    result = (
                        await self.analysis_client.calculate_statistical_indicators(
                            symbol
                        )
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"calculate_statistical_indicators: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "calculate_statistical_indicators",
                        e,
                        f"calculate_statistical_indicators: {symbol}",
                    )

            @self.mcp.tool()
            async def perform_pattern_recognition(symbol: str) -> Dict[str, Any]:
                """패턴 인식 수행 (캐싱 + 재시도 로직)"""
                try:
                    if not self.analysis_client:
                        return self.create_error_response(
                            "perform_pattern_recognition",
                            "Analysis client not initialized",
                            f"perform_pattern_recognition: {symbol}",
                        )

                    result = await self.analysis_client.perform_pattern_recognition(
                        symbol
                    )
                    return self.create_standard_response(
                        success=True,
                        query=f"perform_pattern_recognition: {symbol}",
                        data=result,
                    )
                except Exception as e:
                    return self.create_error_response(
                        "perform_pattern_recognition",
                        e,
                        f"perform_pattern_recognition: {symbol}",
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
                "Stock analysis MCP tools and HTTP endpoints registered successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise


def main():
    """메인 함수"""
    import asyncio

    # 서버 인스턴스 생성
    server = StockAnalysisMCPServer(port=8052, debug=True)

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
