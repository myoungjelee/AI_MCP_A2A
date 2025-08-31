"""
AI MCP A2A 프로젝트 하이브리드 통합 테스트 실행 스크립트
개발 단계별로 다른 테스트 레벨을 제공합니다.
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 현재 디렉토리도 Python 경로에 추가
current_dir = Path.cwd()
sys.path.insert(0, str(current_dir))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_environment():
    """환경 설정 및 검증"""
    # .env 파일 로드 시도
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("✅ .env 파일 로드 완료")
    except ImportError:
        logger.warning("⚠️ python-dotenv가 설치되지 않음, 환경변수 직접 확인")

    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        logger.info("💡 환경변수 설정 방법:")
        logger.info("   Windows: set OPENAI_API_KEY=your_api_key_here")
        logger.info("   Linux/Mac: export OPENAI_API_KEY=your_api_key_here")
        logger.info("   또는 .env 파일에 OPENAI_API_KEY=your_api_key_here 추가")
        return False

    logger.info("✅ OPENAI_API_KEY 확인됨")
    return True


async def run_unit_tests():
    """빠른 단위 테스트 실행 (개발 중 사용)"""
    logger.info("🚀 빠른 단위 테스트 시작 (1-2초)")

    test_results = []
    start_time = time.time()

    try:
        # 1. MCP 클라이언트 생성 테스트
        logger.info("🔧 MCP 클라이언트 생성 테스트...")

        from src.mcp_servers.macroeconomic import MacroeconomicClient
        from src.mcp_servers.naver_news import NaverNewsClient
        from src.mcp_servers.stock_analysis import StockAnalysisClient

        # 클라이언트 생성 테스트
        macro_client = MacroeconomicClient()
        stock_client = StockAnalysisClient()
        news_client = NaverNewsClient()

        test_results.append(
            {
                "test": "MCP 클라이언트 생성",
                "success": True,
                "details": f"생성된 클라이언트: {len([macro_client, stock_client, news_client])}개",
            }
        )

        # 2. 에이전트 초기화 테스트
        logger.info("�� 에이전트 초기화 테스트...")

        from src.la_agents.analysis_agent import AnalysisAgent
        from src.la_agents.data_collector_agent import DataCollectorAgent
        from src.la_agents.portfolio_agent import PortfolioAgent
        from src.la_agents.supervisor_agent import SupervisorAgent

        # 에이전트 생성 테스트
        analysis_agent = AnalysisAgent()
        data_agent = DataCollectorAgent()
        portfolio_agent = PortfolioAgent()
        supervisor_agent = SupervisorAgent()

        test_results.append(
            {
                "test": "에이전트 초기화",
                "success": True,
                "details": f"초기화된 에이전트: {len([analysis_agent, data_agent, portfolio_agent, supervisor_agent])}개",
            }
        )

        # 3. 모델 연결 상태 확인
        logger.info("🤖 GPT-5 모델 연결 상태 확인...")

        agents_with_models = []
        for agent, name in [
            (analysis_agent, "Analysis"),
            (data_agent, "DataCollector"),
            (portfolio_agent, "Portfolio"),
            (supervisor_agent, "Supervisor"),
        ]:
            if hasattr(agent, "model") and agent.model:
                agents_with_models.append(name)

        test_results.append(
            {
                "test": "GPT-5 모델 연결",
                "success": len(agents_with_models) == 4,
                "details": f"모델 연결된 에이전트: {agents_with_models}",
            }
        )

        # 4. 워크플로우 구축 테스트
        logger.info("🔄 워크플로우 구축 테스트...")

        try:
            supervisor_graph = supervisor_agent.build_graph()
            test_results.append(
                {
                    "test": "워크플로우 구축",
                    "success": True,
                    "details": "Supervisor 워크플로우 구축 성공",
                }
            )
        except Exception as e:
            test_results.append(
                {
                    "test": "워크플로우 구축",
                    "success": False,
                    "details": f"워크플로우 구축 실패: {e}",
                }
            )

        execution_time = time.time() - start_time

        # 결과 요약
        successful_tests = [r for r in test_results if r["success"]]
        failed_tests = [r for r in test_results if not r["success"]]

        logger.info("\n📋 단위 테스트 결과 요약:")
        logger.info(f"⏱️ 실행 시간: {execution_time:.2f}초")
        logger.info(f"✅ 성공: {len(successful_tests)}개")
        logger.info(f"❌ 실패: {len(failed_tests)}개")

        if successful_tests:
            logger.info("\n✅ 성공한 테스트들:")
            for test in successful_tests:
                logger.info(f"  - {test['test']}: {test['details']}")

        if failed_tests:
            logger.error("\n❌ 실패한 테스트들:")
            for test in failed_tests:
                logger.error(f"  - {test['test']}: {test['details']}")

        return {
            "success": len(failed_tests) == 0,
            "total_tests": len(test_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "execution_time": execution_time,
            "results": test_results,
        }

    except Exception as e:
        logger.error(f"❌ 단위 테스트 실행 중 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time": time.time() - start_time,
        }


async def run_integration_tests():
    """실제 통합 테스트 실행 (배포 전 사용)"""
    logger.info("🚀 실제 통합 테스트 시작 (30초-2분)")

    # 실제 MCP 서버와 에이전트 간 통신 테스트
    # 이 부분은 실제 서버가 실행되어야 하므로
    # 현재는 기본적인 연결 테스트만 수행

    test_results = []
    start_time = time.time()

    try:
        # 1. OpenAI API 연결 테스트
        logger.info("🔌 OpenAI API 연결 테스트...")

        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model="gpt-5", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # 간단한 테스트 메시지 전송
        try:
            response = await model.ainvoke(
                "Hello, this is a test message. Please respond with 'Test successful'."
            )
            if "Test successful" in response.content:
                test_results.append(
                    {
                        "test": "OpenAI API 연결",
                        "success": True,
                        "details": "GPT-5 모델과 정상 통신",
                    }
                )
            else:
                test_results.append(
                    {
                        "test": "OpenAI API 연결",
                        "success": False,
                        "details": f"예상 응답과 다름: {response.content}",
                    }
                )
        except Exception as e:
            test_results.append(
                {
                    "test": "OpenAI API 연결",
                    "success": False,
                    "details": f"API 호출 실패: {e}",
                }
            )

            # 2. 에이전트 워크플로우 실행 테스트
        logger.info("🔄 에이전트 워크플로우 실행 테스트...")

        try:
            from src.la_agents.supervisor_agent import SupervisorAgent

            supervisor = SupervisorAgent()

            # 간단한 테스트 워크플로우 실행 (워크플로우 구축만 테스트)
            try:
                graph = supervisor.build_graph()
                logger.info("✅ 워크플로우 구축 성공")

                # 간단한 상태 테스트
                status = supervisor.get_workflow_status()
                logger.info(f"📊 워크플로우 상태: {status}")

                result = {
                    "success": True,
                    "message": "워크플로우 구축 및 상태 확인 성공",
                }

                # 3. 실제 스키마 기반 워크플로우 실행 테스트
                logger.info("🔄 실제 스키마 기반 워크플로우 실행 테스트...")

                try:
                    # SupervisorState 스키마에 맞는 실제 입력 데이터
                    input_state = {
                        "messages": [
                            {
                                "role": "user",
                                "content": "삼성전자와 SK하이닉스의 투자 분석을 진행해주세요.",
                            }
                        ],
                        "supervision_status": "monitoring",
                        "active_agents": [],
                        "system_health": "healthy",
                        "workflow_status": "initialized",
                        "current_step": "start",
                        "total_steps": 4,
                        "agent_states": {},
                        "final_result": None,
                        "alerts": [],
                        "warnings": [],
                        "error_log": [],
                        "execution_time": 0.0,
                    }

                    logger.info(
                        f"📝 입력 상태: {len(input_state['messages'])}개 메시지, {input_state['total_steps']}개 단계"
                    )

                    # 실제 워크플로우 실행
                    start_time = time.time()
                    workflow_result = await graph.ainvoke(input_state)
                    execution_time = time.time() - start_time

                    logger.info(f"⏱️ 워크플로우 실행 시간: {execution_time:.2f}초")
                    logger.info(
                        f"🔄 최종 단계: {workflow_result.get('current_step', 'unknown')}"
                    )
                    logger.info(
                        f"📊 워크플로우 상태: {workflow_result.get('workflow_status', 'unknown')}"
                    )
                    logger.info(
                        f"🏥 시스템 상태: {workflow_result.get('system_health', 'unknown')}"
                    )

                    # 에이전트 상태 확인
                    agent_states = workflow_result.get("agent_states", {})
                    logger.info(
                        f"🤖 활성 에이전트: {workflow_result.get('active_agents', [])}"
                    )
                    logger.info(f"📋 에이전트 상태 수: {len(agent_states)}")

                    # 최종 결과 확인
                    final_result = workflow_result.get("final_result", {})
                    if final_result:
                        logger.info(
                            f"🎯 최종 결과 성공: {final_result.get('success', False)}"
                        )
                        if final_result.get("success"):
                            overall_assessment = final_result.get(
                                "overall_assessment", {}
                            )
                            logger.info(
                                f"📈 종합 점수: {overall_assessment.get('overall_score', 0):.2f}"
                            )
                            logger.info(
                                f"🏆 등급: {overall_assessment.get('grade', 'N/A')}"
                            )

                    # 에러 로그 확인
                    error_log = workflow_result.get("error_log", [])
                    if error_log:
                        logger.warning(f"⚠️ 에러 로그 {len(error_log)}개 발견")
                        for i, error in enumerate(error_log[:3]):  # 최대 3개만 표시
                            logger.warning(f"  {i+1}. {error}")

                    schema_test_result = {
                        "test": "실제 스키마 워크플로우",
                        "success": True,
                        "details": f"워크플로우 실행 성공 - {execution_time:.2f}초",
                        "execution_time": execution_time,
                        "final_step": workflow_result.get("current_step"),
                        "workflow_status": workflow_result.get("workflow_status"),
                        "system_health": workflow_result.get("system_health"),
                        "agent_states_count": len(agent_states),
                        "has_final_result": bool(final_result),
                        "error_count": len(error_log),
                    }

                    test_results.append(schema_test_result)

                except Exception as e:
                    schema_test_result = {
                        "test": "실제 스키마 워크플로우",
                        "success": False,
                        "details": f"워크플로우 실행 실패: {e}",
                    }
                    test_results.append(schema_test_result)

            except Exception as e:
                result = {"success": False, "error": str(e)}

            if result.get("success"):
                test_results.append(
                    {
                        "test": "에이전트 워크플로우",
                        "success": True,
                        "details": "테스트 워크플로우 실행 성공",
                    }
                )
            else:
                test_results.append(
                    {
                        "test": "에이전트 워크플로우",
                        "success": False,
                        "details": f"워크플로우 실행 실패: {result.get('error', 'Unknown error')}",
                    }
                )

        except Exception as e:
            test_results.append(
                {
                    "test": "에이전트 워크플로우",
                    "success": False,
                    "details": f"워크플로우 실행 중 오류: {e}",
                }
            )

        execution_time = time.time() - start_time

        # 결과 요약
        successful_tests = [r for r in test_results if r["success"]]
        failed_tests = [r for r in test_results if not r["success"]]

        logger.info("\n📋 통합 테스트 결과 요약:")
        logger.info(f"⏱️ 실행 시간: {execution_time:.2f}초")
        logger.info(f"✅ 성공: {len(successful_tests)}개")
        logger.info(f"❌ 실패: {len(failed_tests)}개")

        if successful_tests:
            logger.info("\n✅ 성공한 테스트들:")
            for test in successful_tests:
                logger.info(f"  - {test['test']}: {test['details']}")

        if failed_tests:
            logger.error("\n❌ 실패한 테스트들:")
            for test in failed_tests:
                logger.error(f"  - {test['test']}: {test['details']}")

        return {
            "success": len(failed_tests) == 0,
            "total_tests": len(test_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "execution_time": execution_time,
            "results": test_results,
        }

    except Exception as e:
        logger.error(f"❌ 통합 테스트 실행 중 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time": time.time() - start_time,
        }


async def run_full_tests():
    """전체 테스트 실행 (CI/CD에서 사용)"""
    logger.info("🚀 전체 테스트 시작 (단위 + 통합)")

    # 1. 단위 테스트 실행
    logger.info("\n" + "=" * 60)
    logger.info("📋 1단계: 단위 테스트")
    logger.info("=" * 60)
    unit_result = await run_unit_tests()

    # 2. 통합 테스트 실행
    logger.info("\n" + "=" * 60)
    logger.info("📋 2단계: 통합 테스트")
    logger.info("=" * 60)
    integration_result = await run_integration_tests()

    # 최종 결과 요약
    total_time = unit_result.get("execution_time", 0) + integration_result.get(
        "execution_time", 0
    )

    logger.info("\n" + "=" * 60)
    logger.info("📊 최종 테스트 결과 요약")
    logger.info("=" * 60)

    # 단위 테스트 결과
    if unit_result.get("success"):
        logger.info(
            f"✅ 단위 테스트: 성공 ({unit_result.get('successful_tests', 0)}/{unit_result.get('total_tests', 0)})"
        )
    else:
        logger.error(
            f"❌ 단위 테스트: 실패 ({unit_result.get('failed_tests', 0)}개 실패)"
        )

    # 통합 테스트 결과
    if integration_result.get("success"):
        logger.info(
            f"✅ 통합 테스트: 성공 ({integration_result.get('successful_tests', 0)}/{integration_result.get('total_tests', 0)})"
        )
    else:
        logger.error(
            f"❌ 통합 테스트: 실패 ({integration_result.get('failed_tests', 0)}개 실패)"
        )

    # 전체 성공 여부
    overall_success = unit_result.get("success", False) and integration_result.get(
        "success", False
    )

    logger.info("\n📈 전체 결과:")
    logger.info(f"   총 실행 시간: {total_time:.2f}초")
    logger.info(
        f"   단위 테스트: {unit_result.get('successful_tests', 0)}/{unit_result.get('total_tests', 0)} 성공"
    )
    logger.info(
        f"   통합 테스트: {integration_result.get('successful_tests', 0)}/{integration_result.get('total_tests', 0)} 성공"
    )
    logger.info(f"   전체 성공: {'✅' if overall_success else '❌'}")

    if overall_success:
        logger.info("\n🎉 모든 테스트가 성공했습니다!")
        logger.info("🚀 AI MCP A2A 프로젝트가 정상적으로 작동합니다!")
    else:
        logger.error("\n⚠️ 일부 테스트가 실패했습니다.")
        logger.info("🔧 문제를 해결한 후 다시 테스트해주세요.")

    return overall_success


def main():
    """메인 함수 - 명령행 인수에 따라 테스트 실행"""
    parser = argparse.ArgumentParser(description="AI MCP A2A 프로젝트 테스트 실행기")
    parser.add_argument(
        "--mode",
        choices=["unit", "integration", "full"],
        default="full",
        help="테스트 모드 선택 (기본값: full)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="빠른 단위 테스트만 실행 (--mode unit과 동일)",
    )

    args = parser.parse_args()

    # 환경 설정 확인
    if not setup_environment():
        logger.error("❌ 환경 설정 실패. 테스트를 중단합니다.")
        sys.exit(1)

    # 테스트 모드 결정
    if args.fast or args.mode == "unit":
        test_mode = "unit"
        test_func = run_unit_tests
        mode_description = "빠른 단위 테스트"
    elif args.mode == "integration":
        test_mode = "integration"
        test_func = run_integration_tests
        mode_description = "실제 통합 테스트"
    else:
        test_mode = "full"
        test_func = run_full_tests
        mode_description = "전체 테스트 (단위 + 통합)"

    logger.info(f"🚀 {mode_description} 모드로 테스트를 시작합니다...")

    try:
        # 테스트 실행
        success = asyncio.run(test_func())

        if success:
            logger.info(f"\n🎉 {mode_description} 완료!")
            sys.exit(0)
        else:
            logger.error(f"\n⚠️ {mode_description} 실패!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 예상치 못한 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
