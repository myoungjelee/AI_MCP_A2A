"""
데이터 처리 시스템 MCP 서버 - FastMCP 기반

데이터 수집, 배치 처리, 트렌드 분석 기능을 제공하는 MCP 서버입니다.
개발 기술: FastMCP, 비동기 처리, 도구 등록, 선형 회귀 알고리즘
"""

import logging
from typing import Any

from src.mcp_servers.base.base_mcp_server import BaseMCPServer

from .client import MacroeconomicClient

logger = logging.getLogger(__name__)


class MacroeconomicMCPServer(BaseMCPServer):
    """거시경제 데이터 처리 시스템 MCP 서버"""

    def __init__(self, port: int = 8042, debug: bool = False):
        super().__init__("macroeconomic", port=port, debug=debug)

    def _initialize_clients(self):
        """클라이언트들을 초기화합니다."""
        try:
            # 거시경제 클라이언트 초기화
            self.macroeconomic_client = MacroeconomicClient()

            # 클라이언트 초기화 완료 표시
            self._clients_initialized = True

            logger.info("Macroeconomic client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize macroeconomic client: {e}")
            self._clients_initialized = False
            raise

    def _register_tools(self):
        """MCP 도구들을 등록합니다."""

        @self.mcp.tool()
        async def collect_data(
            category: str, max_records: int = 100, source: str = "default"
        ) -> dict[str, Any]:
            """데이터 수집

            Args:
                category: 데이터 카테고리
                max_records: 최대 수집 레코드 수
                source: 데이터 소스

            Returns:
                수집된 데이터 정보
            """
            try:
                # 요청 카운트 증가
                self.increment_request_count()

                # 미들웨어 적용
                result = await self.middleware.apply_all("데이터 수집")(
                    self.macroeconomic_client.collect_data
                )(category=category, max_records=max_records, source=source)

                return self.create_standard_response(
                    success=True,
                    query=f"collect_data(category={category}, max_records={max_records}, source={source})",
                    data=result,
                    message="데이터 수집 완료",
                ).dict()

            except Exception as e:
                logger.error(f"collect_data failed: {e}")
                return self.create_error_response(
                    func_name="collect_data",
                    error=e,
                    query=f"collect_data(category={category}, max_records={max_records}, source={source})",
                    error_code="DATA_COLLECTION_FAILED",
                ).dict()

        @self.mcp.tool()
        async def process_data_batch(
            data_records: list[dict[str, Any]], operation: str = "validate"
        ) -> dict[str, Any]:
            """배치 데이터 처리

            Args:
                data_records: 처리할 데이터 레코드 리스트
                operation: 처리 작업 (validate/transform/aggregate)

            Returns:
                처리된 데이터 정보
            """
            try:
                # 요청 카운트 증가
                self.increment_request_count()

                # 미들웨어 적용
                result = await self.middleware.apply_all("배치 데이터 처리")(
                    self.macroeconomic_client.process_data_batch
                )(data_records=data_records, operation=operation)

                return self.create_standard_response(
                    success=True,
                    query=f"process_data_batch(operation={operation}, records_count={len(data_records)})",
                    data=result,
                    message="배치 데이터 처리 완료",
                ).dict()

            except Exception as e:
                logger.error(f"process_data_batch failed: {e}")
                return self.create_error_response(
                    func_name="process_data_batch",
                    error=e,
                    query=f"process_data_batch(operation={operation}, records_count={len(data_records)})",
                    error_code="BATCH_PROCESSING_FAILED",
                ).dict()

        @self.mcp.tool()
        async def analyze_data_trends(
            data_records: list[dict[str, Any]],
        ) -> dict[str, Any]:
            """데이터 트렌드 분석

            Args:
                data_records: 분석할 데이터 레코드 리스트

            Returns:
                트렌드 분석 결과
            """
            try:
                # 요청 카운트 증가
                self.increment_request_count()

                # 미들웨어 적용
                result = await self.middleware.apply_all("데이터 트렌드 분석")(
                    self.macroeconomic_client.analyze_data_trends
                )(data_records=data_records)

                return self.create_standard_response(
                    success=True,
                    query=f"analyze_data_trends(records_count={len(data_records)})",
                    data=result,
                    message="데이터 트렌드 분석 완료",
                ).dict()

            except Exception as e:
                logger.error(f"analyze_data_trends failed: {e}")
                return self.create_error_response(
                    func_name="analyze_data_trends",
                    error=e,
                    query=f"analyze_data_trends(records_count={len(data_records)})",
                    error_code="TREND_ANALYSIS_FAILED",
                ).dict()

        @self.mcp.tool()
        async def get_server_health() -> dict[str, Any]:
            """서버 헬스 상태 조회

            Returns:
                서버 헬스 상태 정보
            """
            try:
                return self.get_health_status()
            except Exception as e:
                logger.error(f"get_server_health failed: {e}")
                return self.create_error_response(
                    func_name="get_server_health",
                    error=e,
                    query="get_server_health()",
                    error_code="HEALTH_CHECK_FAILED",
                ).dict()

        @self.mcp.tool()
        async def get_server_metrics() -> dict[str, Any]:
            """서버 메트릭 조회

            Returns:
                서버 메트릭 정보
            """
            try:
                return self.get_metrics()
            except Exception as e:
                logger.error(f"get_server_metrics failed: {e}")
                return self.create_error_response(
                    func_name="get_server_metrics",
                    error=e,
                    query="get_server_metrics()",
                    error_code="METRICS_COLLECTION_FAILED",
                ).dict()

        logger.info("Macroeconomic MCP tools registered successfully")


def main():
    """메인 함수"""
    import asyncio

    # 서버 인스턴스 생성
    server = MacroeconomicMCPServer(debug=True)

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
