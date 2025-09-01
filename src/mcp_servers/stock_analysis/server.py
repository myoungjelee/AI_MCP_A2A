"""
데이터 분석 시스템 MCP 서버 - FastMCP 기반
데이터 트렌드 분석, 통계적 지표 계산, 패턴 인식을 제공합니다.
복잡한 주식 분석 대신 깔끔한 코드 구조와 효율적인 분석 알고리즘을 보여줍니다.
"""

import logging
from typing import Any, Dict

from ..base.base_mcp_server import BaseMCPServer
from ..base.config import MCPServerConfig
from .client import StockAnalysisClient


class StockAnalysisMCPServer(BaseMCPServer):
    """주식 분석 시스템 MCP 서버 (BaseMCPServer 상속)"""

    def __init__(self, port: int = 8042, host: str = "0.0.0.0", debug: bool = False, **kwargs):
        # 기본 설정
        config = MCPServerConfig.from_env(name="stock_analysis")
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
            name="stock_analysis",
            port=port,
            host=host,
            debug=debug,
            server_instructions="주식 트렌드 분석, 통계적 지표 계산, 패턴 인식을 위한 MCP 서버 (개발 기술 중심)",
            config=config,
            enable_middlewares=True,
            middleware_config=middleware_config,
            **kwargs
        )

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
                self.analysis_client.analyze_data_trends = self.middleware.apply_all("데이터 트렌드 분석")(
                    self.analysis_client.analyze_data_trends
                )
                self.analysis_client.calculate_statistical_indicators = self.middleware.apply_all("통계적 지표 계산")(
                    self.analysis_client.calculate_statistical_indicators
                )
                self.analysis_client.perform_pattern_recognition = self.middleware.apply_all("패턴 인식")(
                    self.analysis_client.perform_pattern_recognition
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

                    result = await self.analysis_client.analyze_data_trends(symbol, period)
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

                    result = await self.analysis_client.calculate_statistical_indicators(symbol)
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

                    result = await self.analysis_client.perform_pattern_recognition(symbol)
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

            self.logger.info("Stock analysis MCP tools registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise


def main():
    """메인 함수"""
    import asyncio
    
    async def run_server():
        server = StockAnalysisMCPServer(port=8042, debug=True)
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
