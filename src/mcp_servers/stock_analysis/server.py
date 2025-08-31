"""
데이터 분석 시스템 MCP 서버 - FastMCP 기반
데이터 트렌드 분석, 통계적 지표 계산, 패턴 인식을 제공합니다.
복잡한 주식 분석 대신 깔끔한 코드 구조와 효율적인 분석 알고리즘을 보여줍니다.
"""

import logging
from typing import Any, Dict

from fastmcp import FastMCP

from .client import StockAnalysisClient


class StockAnalysisMCPServer:
    """주식 분석 시스템 MCP 서버 (FastMCP 기반)"""

    def __init__(self, port: int = 3021, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.mcp = FastMCP("stock_analysis_system")
        self.mcp.description = "주식 트렌드 분석, 통계적 지표 계산, 패턴 인식을 위한 MCP 서버 (개발 기술 중심)"

        # 클라이언트 초기화
        self.analysis_client = StockAnalysisClient()

        # 도구 등록
        self._register_tools()

        logging.info("주식 분석 시스템 MCP 서버 초기화 완료")

    def _register_tools(self):
        """MCP 도구들을 등록합니다."""

        @self.mcp.tool()
        async def analyze_data_trends(
            symbol: str, period: str = "1y"
        ) -> Dict[str, Any]:
            """데이터 트렌드 분석 수행 (캐싱 + 재시도 로직)"""
            try:
                result = await self.analysis_client.analyze_data_trends(symbol, period)
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "데이터 트렌드 분석에 실패했습니다",
                }

        @self.mcp.tool()
        async def calculate_statistical_indicators(symbol: str) -> Dict[str, Any]:
            """통계적 지표 계산 수행 (캐싱 + 재시도 로직)"""
            try:
                result = await self.analysis_client.calculate_statistical_indicators(
                    symbol
                )
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "통계적 지표 계산에 실패했습니다",
                }

        @self.mcp.tool()
        async def perform_pattern_recognition(symbol: str) -> Dict[str, Any]:
            """패턴 인식 수행 (캐싱 + 재시도 로직)"""
            try:
                result = await self.analysis_client.perform_pattern_recognition(symbol)
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "패턴 인식에 실패했습니다",
                }

        logging.info("주식 분석 시스템 MCP 도구 3개 등록 완료")

    def run(self):
        """서버를 실행합니다."""
        try:
            logging.info(f"주식 분석 시스템 MCP 서버 시작: {self.host}:{self.port}")
            self.mcp.run(transport="streamable-http", host=self.host, port=self.port)
        except Exception as e:
            logging.error(f"서버 실행 실패: {e}")
            raise


if __name__ == "__main__":
    try:
        # 서버 생성 및 실행
        server = StockAnalysisMCPServer()
        server.run()
    except KeyboardInterrupt:
        logging.info("서버 중단 신호 수신")
    except Exception as e:
        logging.error(f"서버 오류: {e}")
        raise
    finally:
        logging.info("주식 분석 시스템 MCP 서버 종료")
