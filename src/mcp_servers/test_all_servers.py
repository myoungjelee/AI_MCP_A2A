"""
모든 MCP 서버 통합 테스트 스크립트
각 서버의 연결성과 기본 기능을 테스트합니다.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 상대 경로로 import (IDE 경고 해결)
from .financial_analysis.server import FinancialAnalysisMCPServer
from .kiwoom.server import KiwoomMCPServer
from .macroeconomic.server import MacroeconomicMCPServer
from .naver_news.server import NaverNewsMCPServer
from .stock_analysis.server import StockAnalysisMCPServer
from .tavily_search.server import TavilySearchMCPServer

logger = logging.getLogger(__name__)


class MCPServerTester:
    """MCP 서버 통합 테스터"""

    def __init__(self, debug: bool = False):
        """초기화"""
        self.debug = debug
        self.test_results: Dict[str, Dict[str, Any]] = {}

        # 테스트할 서버들
        self.test_servers = {
            "macroeconomic": MacroeconomicMCPServer(port=8041, debug=debug),
            "naver_news": NaverNewsMCPServer(port=8050, debug=debug),
            "stock_analysis": StockAnalysisMCPServer(port=8042, debug=debug),
            "tavily_search": TavilySearchMCPServer(port=8043, debug=debug),
            "kiwoom": KiwoomMCPServer(port=8044, debug=debug),
            "financial_analysis": FinancialAnalysisMCPServer(port=8045, debug=debug),
        }

        # 로깅 설정
        self._setup_logging()

        logger.info("MCP Server Tester initialized")

    def _setup_logging(self):
        """로깅 설정"""
        log_level = logging.DEBUG if self.debug else logging.INFO
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("mcp_server_test.log", encoding="utf-8"),
            ],
        )

    async def test_server_connection(
        self, server_name: str, server: Any
    ) -> Dict[str, Any]:
        """서버 연결 테스트"""
        start_time = time.time()
        result = {
            "server_name": server_name,
            "test_type": "connection",
            "success": False,
            "error": None,
            "response_time": 0,
            "details": {},
        }

        try:
            logger.info(f"서버 {server_name} 연결 테스트 시작...")

            # 서버 시작
            await server.start_server()
            result["details"]["startup_success"] = True

            # 잠시 대기
            await asyncio.sleep(1)

            # 서버 상태 확인
            if hasattr(server, "get_server_status"):
                status = server.get_server_status()
                result["details"]["server_status"] = status
                result["details"]["status_check_success"] = True

            # 헬스 체크
            if hasattr(server, "get_health_status"):
                health = server.get_health_status()
                result["details"]["health_status"] = health
                result["details"]["health_check_success"] = True

            # 메트릭 수집
            if hasattr(server, "get_metrics"):
                metrics = server.get_metrics()
                result["details"]["metrics"] = metrics
                result["details"]["metrics_collection_success"] = True

            # 서버 중지
            await server.stop_server()
            result["details"]["shutdown_success"] = True

            result["success"] = True
            logger.info(f"서버 {server_name} 연결 테스트 성공")

        except Exception as e:
            result["error"] = str(e)
            result["details"]["error_type"] = type(e).__name__
            logger.error(f"서버 {server_name} 연결 테스트 실패: {e}")

            # 서버가 실행 중이면 중지 시도
            try:
                if hasattr(server, "stop_server"):
                    await server.stop_server()
            except Exception as stop_error:
                logger.warning(f"서버 {server_name} 중지 시도 실패: {stop_error}")

        finally:
            result["response_time"] = time.time() - start_time

        return result

    async def test_server_functionality(
        self, server_name: str, server: Any
    ) -> Dict[str, Any]:
        """서버 기능 테스트"""
        start_time = time.time()
        result = {
            "server_name": server_name,
            "test_type": "functionality",
            "success": False,
            "error": None,
            "response_time": 0,
            "details": {},
        }

        try:
            logger.info(f"서버 {server_name} 기능 테스트 시작...")

            # 서버 시작
            await server.start_server()
            await asyncio.sleep(1)

            # 사용 가능한 도구 확인
            if hasattr(server, "get_available_tools"):
                tools = server.get_available_tools()
                result["details"]["available_tools"] = tools
                result["details"]["tools_count"] = len(tools)
                result["details"]["tools_check_success"] = True

            # 서버별 특화 테스트
            if server_name == "macroeconomic":
                await self._test_macroeconomic_functionality(server, result)
            elif server_name == "naver_news":
                await self._test_naver_news_functionality(server, result)
            elif server_name == "stock_analysis":
                await self._test_stock_analysis_functionality(server, result)
            elif server_name == "tavily_search":
                await self._test_tavily_search_functionality(server, result)
            elif server_name == "kiwoom":
                await self._test_kiwoom_functionality(server, result)
            elif server_name == "financial_analysis":
                await self._test_financial_analysis_functionality(server, result)

            # 서버 중지
            await server.stop_server()
            result["details"]["shutdown_success"] = True

            result["success"] = True
            logger.info(f"서버 {server_name} 기능 테스트 성공")

        except Exception as e:
            result["error"] = str(e)
            result["details"]["error_type"] = type(e).__name__
            logger.error(f"서버 {server_name} 기능 테스트 실패: {e}")

            # 서버가 실행 중이면 중지 시도
            try:
                if hasattr(server, "stop_server"):
                    await server.stop_server()
            except Exception as stop_error:
                logger.warning(f"서버 {server_name} 중지 시도 실패: {stop_error}")

        finally:
            result["response_time"] = time.time() - start_time

        return result

    async def _test_macroeconomic_functionality(
        self, server: Any, result: Dict[str, Any]
    ):
        """거시경제 서버 기능 테스트"""
        try:
            # 데이터 수집 테스트
            if hasattr(server, "macroeconomic_client"):
                client = server.macroeconomic_client

                # 간단한 데이터 수집 테스트
                test_result = await client.collect_data(
                    category="test", max_records=5, source="test"
                )
                result["details"]["data_collection_test"] = {
                    "success": True,
                    "result": test_result,
                }

        except Exception as e:
            result["details"]["data_collection_test"] = {
                "success": False,
                "error": str(e),
            }

    async def _test_naver_news_functionality(self, server: Any, result: Dict[str, Any]):
        """네이버 뉴스 서버 기능 테스트"""
        try:
            # 뉴스 검색 테스트
            if hasattr(server, "news_client"):
                client = server.news_client

                # 간단한 뉴스 검색 테스트
                test_result = await client.search_news(query="테스트", max_results=3)
                result["details"]["news_search_test"] = {
                    "success": True,
                    "result": test_result,
                }

        except Exception as e:
            result["details"]["news_search_test"] = {"success": False, "error": str(e)}

    async def _test_stock_analysis_functionality(
        self, server: Any, result: Dict[str, Any]
    ):
        """주식 분석 서버 기능 테스트"""
        try:
            # 주식 분석 테스트
            if hasattr(server, "stock_client"):
                client = server.stock_client

                # 간단한 주식 분석 테스트
                test_result = await client.analyze_data_trends(
                    data_records=[{"value": 100, "timestamp": "2024-01-01"}]
                )
                result["details"]["stock_analysis_test"] = {
                    "success": True,
                    "result": test_result,
                }

        except Exception as e:
            result["details"]["stock_analysis_test"] = {
                "success": False,
                "error": str(e),
            }

    async def _test_tavily_search_functionality(
        self, server: Any, result: Dict[str, Any]
    ):
        """Tavily 검색 서버 기능 테스트"""
        try:
            # 검색 테스트
            if hasattr(server, "search_client"):
                client = server.search_client

                # 간단한 검색 테스트
                test_result = await client.search(query="테스트", max_results=3)
                result["details"]["search_test"] = {
                    "success": True,
                    "result": test_result,
                }

        except Exception as e:
            result["details"]["search_test"] = {"success": False, "error": str(e)}

    async def _test_kiwoom_functionality(self, server: Any, result: Dict[str, Any]):
        """키움 서버 기능 테스트"""
        try:
            # 키움 API 연결 테스트
            if hasattr(server, "kiwoom_client"):
                client = server.kiwoom_client

                # 연결 상태 확인
                test_result = await client.get_connection_status()
                result["details"]["connection_test"] = {
                    "success": True,
                    "result": test_result,
                }

        except Exception as e:
            result["details"]["connection_test"] = {"success": False, "error": str(e)}

    async def _test_financial_analysis_functionality(
        self, server: Any, result: Dict[str, Any]
    ):
        """재무 분석 서버 기능 테스트"""
        try:
            # 재무 분석 테스트
            if hasattr(server, "financial_client"):
                client = server.financial_client

                # 간단한 재무 분석 테스트
                test_result = await client.analyze_financial_data(
                    data_records=[{"revenue": 1000, "profit": 100}]
                )
                result["details"]["financial_analysis_test"] = {
                    "success": True,
                    "result": test_result,
                }

        except Exception as e:
            result["details"]["financial_analysis_test"] = {
                "success": False,
                "error": str(e),
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트를 실행합니다"""
        logger.info("모든 MCP 서버 테스트 시작...")

        start_time = time.time()
        all_results = {}

        for server_name, server in self.test_servers.items():
            logger.info(f"=== {server_name} 서버 테스트 시작 ===")

            # 연결 테스트
            connection_result = await self.test_server_connection(server_name, server)
            all_results[f"{server_name}_connection"] = connection_result

            # 기능 테스트
            functionality_result = await self.test_server_functionality(
                server_name, server
            )
            all_results[f"{server_name}_functionality"] = functionality_result

            logger.info(f"=== {server_name} 서버 테스트 완료 ===\n")

        # 전체 테스트 결과 요약
        total_time = time.time() - start_time
        summary = self._generate_test_summary(all_results, total_time)

        self.test_results = all_results
        self.test_results["summary"] = summary

        logger.info("모든 테스트 완료")
        return self.test_results

    def _generate_test_summary(
        self, results: Dict[str, Any], total_time: float
    ) -> Dict[str, Any]:
        """테스트 결과 요약을 생성합니다"""
        total_tests = len(results)
        successful_tests = sum(
            1 for result in results.values() if result.get("success", False)
        )
        failed_tests = total_tests - successful_tests

        # 서버별 성공률
        server_results = {}
        for key, result in results.items():
            if "_connection" in key or "_functionality" in key:
                server_name = key.split("_")[0]
                if server_name not in server_results:
                    server_results[server_name] = {
                        "connection": False,
                        "functionality": False,
                    }

                if "_connection" in key:
                    server_results[server_name]["connection"] = result.get(
                        "success", False
                    )
                elif "_functionality" in key:
                    server_results[server_name]["functionality"] = result.get(
                        "success", False
                    )

        # 성공률 계산
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round(success_rate, 2),
            "total_execution_time": round(total_time, 2),
            "server_results": server_results,
            "overall_status": "PASS" if success_rate >= 80 else "FAIL",
        }

    def print_test_results(self):
        """테스트 결과를 출력합니다"""
        if not self.test_results:
            print("테스트 결과가 없습니다.")
            return

        summary = self.test_results.get("summary", {})

        print("\n" + "=" * 60)
        print("MCP 서버 통합 테스트 결과")
        print("=" * 60)

        # 전체 요약
        print(f"전체 상태: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"성공률: {summary.get('success_rate', 0)}%")
        print(f"총 테스트: {summary.get('total_tests', 0)}개")
        print(f"성공: {summary.get('successful_tests', 0)}개")
        print(f"실패: {summary.get('failed_tests', 0)}개")
        print(f"총 실행 시간: {summary.get('total_execution_time', 0)}초")

        print("\n" + "-" * 60)
        print("서버별 테스트 결과")
        print("-" * 60)

        # 서버별 결과
        server_results = summary.get("server_results", {})
        for server_name, results in server_results.items():
            connection_status = "✅" if results.get("connection") else "❌"
            functionality_status = "✅" if results.get("functionality") else "❌"

            print(
                f"{server_name:20} | 연결: {connection_status} | 기능: {functionality_status}"
            )

        print("\n" + "-" * 60)
        print("상세 테스트 결과")
        print("-" * 60)

        # 상세 결과
        for test_name, result in self.test_results.items():
            if test_name == "summary":
                continue

            status = "✅ 성공" if result.get("success") else "❌ 실패"
            response_time = result.get("response_time", 0)
            error = result.get("error")

            print(f"{test_name:35} | {status:10} | {response_time:6.2f}초")
            if error:
                print(f"  └─ 에러: {error}")

        print("=" * 60)

    def save_test_results(self, filename: str = "mcp_server_test_results.json"):
        """테스트 결과를 파일로 저장합니다"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            logger.info(f"테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"테스트 결과 저장 실패: {e}")


async def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP 서버 통합 테스트")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    parser.add_argument(
        "--save-results", action="store_true", help="테스트 결과를 파일로 저장"
    )
    parser.add_argument(
        "--output-file", default="mcp_server_test_results.json", help="결과 파일명"
    )

    args = parser.parse_args()

    # 테스터 인스턴스 생성
    tester = MCPServerTester(debug=args.debug)

    try:
        # 모든 테스트 실행
        results = await tester.run_all_tests()

        # 결과 출력
        tester.print_test_results()

        # 결과 저장 (옵션)
        if args.save_results:
            tester.save_test_results(args.output_file)

        # 종료 코드 결정
        summary = results.get("summary", {})
        overall_status = summary.get("overall_status", "UNKNOWN")

        if overall_status == "PASS":
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
            sys.exit(0)
        else:
            print(
                f"\n⚠️  일부 테스트가 실패했습니다. (성공률: {summary.get('success_rate', 0)}%)"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
