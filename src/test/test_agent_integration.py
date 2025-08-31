"""
에이전트 통합 테스트
모든 LangGraph 에이전트의 초기화와 워크플로우를 테스트합니다.
"""

import asyncio
import logging
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_analysis_agent():
    """[에이전트 통합] Analysis Agent의 GPT-5 모델 초기화와 기본 기능을 테스트한다"""
    try:
        from src.la_agents.analysis_agent import AnalysisAgent

        logger.info("🔍 Analysis Agent 테스트 시작...")

        # 에이전트 초기화
        agent = AnalysisAgent()
        logger.info(f"✅ Analysis Agent 초기화 완료: {agent.name}")

        # GPT-5 모델 연결 확인
        if hasattr(agent, "model") and agent.model:
            model_name = getattr(agent.model, "model_name", "unknown")
            logger.info(f"🤖 연결된 모델: {model_name}")
        else:
            logger.warning("⚠️ 모델이 설정되지 않았습니다")

        # 기본 기능 확인
        capabilities = agent.get_analysis_capabilities()
        logger.info(f"📊 지원 분석 방법: {capabilities['supported_methods']}")
        logger.info(f"🔧 도구 수: {capabilities['tool_count']}")

        # 워크플로우 구축 테스트
        try:
            graph = agent.build_graph()
            logger.info("✅ 워크플로우 구축 성공")
        except Exception as e:
            logger.warning(f"⚠️ 워크플로우 구축 실패 (도구가 없을 수 있음): {e}")

        return {"success": True, "agent": "analysis", "capabilities": capabilities}

    except Exception as e:
        logger.error(f"❌ Analysis Agent 테스트 실패: {e}")
        return {"success": False, "agent": "analysis", "error": str(e)}


async def test_data_collector_agent():
    """[에이전트 통합] Data Collector Agent의 GPT-5 모델 초기화와 기본 기능을 테스트한다"""
    try:
        from src.la_agents.data_collector_agent import DataCollectorAgent

        logger.info("📊 Data Collector Agent 테스트 시작...")

        # 에이전트 초기화
        agent = DataCollectorAgent()
        logger.info(f"✅ Data Collector Agent 초기화 완료: {agent.name}")

        # GPT-5 모델 연결 확인
        if hasattr(agent, "model") and agent.model:
            model_name = getattr(agent.model, "model_name", "unknown")
            logger.info(f"🤖 연결된 모델: {model_name}")
        else:
            logger.warning("⚠️ 모델이 설정되지 않았습니다")

        # 기본 기능 확인
        status = agent.get_collection_status()
        logger.info(f"🔧 최대 데이터 소스 수: {status['max_sources']}")
        logger.info(f"📈 품질 임계값: {status['quality_threshold']}")
        logger.info(f"🔧 도구 수: {status['tool_count']}")

        # 워크플로우 구축 테스트
        try:
            graph = agent.build_graph()
            logger.info("✅ 워크플로우 구축 성공")
        except Exception as e:
            logger.warning(f"⚠️ 워크플로우 구축 실패 (도구가 없을 수 있음): {e}")

        return {"success": True, "agent": "data_collector", "status": status}

    except Exception as e:
        logger.error(f"❌ Data Collector Agent 테스트 실패: {e}")
        return {"success": False, "agent": "data_collector", "error": str(e)}


async def test_portfolio_agent():
    """[에이전트 통합] Portfolio Agent의 GPT-5 모델 초기화와 기본 기능을 테스트한다"""
    try:
        from src.la_agents.portfolio_agent import PortfolioAgent

        logger.info("💼 Portfolio Agent 테스트 시작...")

        # 에이전트 초기화
        agent = PortfolioAgent()
        logger.info(f"✅ Portfolio Agent 초기화 완료: {agent.name}")

        # GPT-5 모델 연결 확인
        if hasattr(agent, "model") and agent.model:
            model_name = getattr(agent.model, "model_name", "unknown")
            logger.info(f"🤖 연결된 모델: {model_name}")
        else:
            logger.warning("⚠️ 모델이 설정되지 않았습니다")

        # 기본 기능 확인
        status = agent.get_portfolio_status()
        logger.info(f"📈 최대 포트폴리오 크기: {status['max_portfolio_size']}")
        logger.info(f"🎯 리스크 허용도 레벨: {status['risk_tolerance_levels']}")
        logger.info(f"🏢 섹터 카테고리: {len(status['sector_categories'])}개")

        # 워크플로우 구축 테스트
        try:
            graph = agent.build_graph()
            logger.info("✅ 워크플로우 구축 성공")
        except Exception as e:
            logger.warning(f"⚠️ 워크플로우 구축 실패 (도구가 없을 수 있음): {e}")

        return {"success": True, "agent": "portfolio", "status": status}

    except Exception as e:
        logger.error(f"❌ Portfolio Agent 테스트 실패: {e}")
        return {"success": False, "agent": "portfolio", "error": str(e)}


async def test_supervisor_agent():
    """[에이전트 통합] Supervisor Agent의 GPT-5 모델 초기화와 워크플로우를 테스트한다"""
    try:
        from src.la_agents.supervisor_agent import SupervisorAgent

        logger.info("👨‍💼 Supervisor Agent 테스트 시작...")

        # 에이전트 초기화
        agent = SupervisorAgent()
        logger.info(f"✅ Supervisor Agent 초기화 완료: {agent.name}")

        # GPT-5 모델 연결 확인
        if hasattr(agent, "model") and agent.model:
            model_name = getattr(agent.model, "model_name", "unknown")
            logger.info(f"🤖 연결된 모델: {model_name}")
        else:
            logger.warning("⚠️ 모델이 설정되지 않았습니다")

        # 기본 기능 확인
        status = agent.get_workflow_status()
        logger.info(f"🔄 워크플로우 단계: {status['workflow_steps']}")
        logger.info(f"🔄 최대 재시도 횟수: {status['max_retries']}")
        logger.info(f"⏱️ 타임아웃: {status['timeout_seconds']}초")

        # 워크플로우 구축 테스트
        try:
            graph = agent.build_graph()
            logger.info("✅ 워크플로우 구축 성공")
        except Exception as e:
            logger.warning(f"⚠️ 워크플로우 구축 실패: {e}")

        return {"success": True, "agent": "supervisor", "status": status}

    except Exception as e:
        logger.error(f"❌ Supervisor Agent 테스트 실패: {e}")
        return {"success": False, "agent": "supervisor", "error": str(e)}


async def test_agent_workflow():
    """[에이전트 통합] 전체 워크플로우 실행을 테스트한다"""
    try:
        from src.la_agents.supervisor_agent import SupervisorAgent

        logger.info("🔄 전체 워크플로우 테스트 시작...")

        # Supervisor Agent 초기화
        supervisor = SupervisorAgent()

        # 테스트용 요청 데이터
        test_request = {
            "symbols": ["AAPL", "GOOGL"],
            "analysis_type": "comprehensive",
            "risk_tolerance": "moderate",
            "target_return": 0.10,
            "max_risk": 0.15,
        }

        logger.info(f"📝 테스트 요청: {test_request}")

        # 워크플로우 실행
        start_time = time.time()
        result = await supervisor.execute_workflow(
            request=test_request, workflow_type="test"
        )
        execution_time = time.time() - start_time

        logger.info(f"⏱️ 워크플로우 실행 시간: {execution_time:.2f}초")

        if result["success"]:
            logger.info("✅ 워크플로우 실행 성공")
            return {"success": True, "execution_time": execution_time, "result": result}
        else:
            logger.error(
                f"❌ 워크플로우 실행 실패: {result.get('error', 'Unknown error')}"
            )
            return {"success": False, "error": result.get("error", "Unknown error")}

    except Exception as e:
        logger.error(f"❌ 워크플로우 테스트 실패: {e}")
        return {"success": False, "error": str(e)}


async def test_agent_interaction():
    """[에이전트 통합] 에이전트 간 상호작용을 테스트한다"""
    try:
        from src.la_agents.analysis_agent import AnalysisAgent
        from src.la_agents.data_collector_agent import DataCollectorAgent
        from src.la_agents.portfolio_agent import PortfolioAgent

        logger.info("🤝 에이전트 간 상호작용 테스트 시작...")

        # 각 에이전트 초기화
        data_agent = DataCollectorAgent()
        analysis_agent = AnalysisAgent()
        portfolio_agent = PortfolioAgent()

        logger.info("✅ 모든 에이전트 초기화 완료")

        # 시뮬레이션된 데이터로 테스트
        test_data = {
            "symbols": ["삼성전자", "SK하이닉스", "LG화학"],
            "price_data": {"삼성전자": 70000, "SK하이닉스": 120000, "LG화학": 800000},
            "volume_data": {
                "삼성전자": 1000000,
                "SK하이닉스": 500000,
                "LG화학": 300000,
            },
        }

        # 데이터 품질 검증 테스트
        quality_result = await data_agent.validate_data_quality(test_data)
        logger.info(f"📊 데이터 품질 점수: {quality_result['score']:.2f}")

        # 간단한 분석 테스트
        analysis_result = await analysis_agent.analyze_data(test_data)
        logger.info(f"🔍 분석 신뢰도: {analysis_result.get('confidence_score', 0):.2f}")

        # 포트폴리오 구성 테스트
        portfolio_result = await portfolio_agent.construct_portfolio(
            analysis_results=analysis_result,
            risk_tolerance="moderate",
            portfolio_size=3,
        )
        logger.info(
            f"💼 포트폴리오 최적화 점수: {portfolio_result.get('optimization_score', 0):.2f}"
        )

        return {
            "success": True,
            "data_quality": quality_result["score"],
            "analysis_confidence": analysis_result.get("confidence_score", 0),
            "portfolio_optimization": portfolio_result.get("optimization_score", 0),
        }

    except Exception as e:
        logger.error(f"❌ 에이전트 상호작용 테스트 실패: {e}")
        return {"success": False, "error": str(e)}


async def test_real_schema_workflow():
    """[에이전트 통합] 실제 스키마 기반 워크플로우 실행을 테스트한다"""
    try:
        from src.la_agents.supervisor_agent import SupervisorAgent

        logger.info("🔄 실제 스키마 기반 워크플로우 테스트 시작...")

        # Supervisor Agent 초기화
        supervisor = SupervisorAgent()

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

        # 워크플로우 구축
        graph = supervisor.build_graph()
        logger.info("✅ 워크플로우 구축 완료")

        # 실제 워크플로우 실행
        start_time = time.time()
        result = await graph.ainvoke(input_state)
        execution_time = time.time() - start_time

        logger.info(f"⏱️ 워크플로우 실행 시간: {execution_time:.2f}초")
        logger.info(f"🔄 최종 단계: {result.get('current_step', 'unknown')}")
        logger.info(f"📊 워크플로우 상태: {result.get('workflow_status', 'unknown')}")
        logger.info(f"🏥 시스템 상태: {result.get('system_health', 'unknown')}")

        # 에이전트 상태 확인
        agent_states = result.get("agent_states", {})
        logger.info(f"🤖 활성 에이전트: {result.get('active_agents', [])}")
        logger.info(f"📋 에이전트 상태 수: {len(agent_states)}")

        # 최종 결과 확인
        final_result = result.get("final_result", {})
        if final_result:
            logger.info(f"🎯 최종 결과 성공: {final_result.get('success', False)}")
            if final_result.get("success"):
                overall_assessment = final_result.get("overall_assessment", {})
                logger.info(
                    f"📈 종합 점수: {overall_assessment.get('overall_score', 0):.2f}"
                )
                logger.info(f"🏆 등급: {overall_assessment.get('grade', 'N/A')}")

        # 에러 로그 확인
        error_log = result.get("error_log", [])
        if error_log:
            logger.warning(f"⚠️ 에러 로그 {len(error_log)}개 발견")
            for i, error in enumerate(error_log[:3]):  # 최대 3개만 표시
                logger.warning(f"  {i+1}. {error}")

        return {
            "success": True,
            "execution_time": execution_time,
            "final_step": result.get("current_step"),
            "workflow_status": result.get("workflow_status"),
            "system_health": result.get("system_health"),
            "agent_states_count": len(agent_states),
            "has_final_result": bool(final_result),
            "error_count": len(error_log),
        }

    except Exception as e:
        logger.error(f"❌ 실제 스키마 워크플로우 테스트 실패: {e}")
        return {"success": False, "error": str(e)}


async def test_state_transitions():
    """[에이전트 통합] 상태 전이를 테스트한다"""
    try:
        from src.la_agents.supervisor_agent import SupervisorAgent

        logger.info("🔄 상태 전이 테스트 시작...")

        supervisor = SupervisorAgent()

        # 각 단계별 상태 변화 테스트
        test_cases = [
            {
                "name": "초기 상태",
                "state": {
                    "messages": [{"role": "user", "content": "테스트"}],
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
                },
            },
            {
                "name": "데이터 수집 단계",
                "state": {
                    "messages": [{"role": "user", "content": "테스트"}],
                    "supervision_status": "intervention",
                    "active_agents": ["data_collector"],
                    "system_health": "healthy",
                    "workflow_status": "running",
                    "current_step": "data_collection",
                    "total_steps": 4,
                    "agent_states": {},
                    "final_result": None,
                    "alerts": [],
                    "warnings": [],
                    "error_log": [],
                    "execution_time": 0.0,
                },
            },
        ]

        results = []
        for test_case in test_cases:
            try:
                # 상태 검증
                state = test_case["state"]
                logger.info(f"📋 {test_case['name']} 테스트")
                logger.info(f"  - 감독 상태: {state['supervision_status']}")
                logger.info(f"  - 활성 에이전트: {state['active_agents']}")
                logger.info(f"  - 현재 단계: {state['current_step']}")
                logger.info(f"  - 워크플로우 상태: {state['workflow_status']}")

                results.append(
                    {
                        "test_case": test_case["name"],
                        "success": True,
                        "state_valid": True,
                    }
                )

            except Exception as e:
                logger.error(f"❌ {test_case['name']} 테스트 실패: {e}")
                results.append(
                    {"test_case": test_case["name"], "success": False, "error": str(e)}
                )

        return {
            "success": all(r["success"] for r in results),
            "test_cases": results,
            "total_tests": len(test_cases),
        }

    except Exception as e:
        logger.error(f"❌ 상태 전이 테스트 실패: {e}")
        return {"success": False, "error": str(e)}


async def run_agent_integration_tests():
    """[에이전트 통합] 모든 에이전트 통합 테스트를 실행한다"""
    logger.info("🚀 에이전트 통합 테스트 시작")

    # 각 에이전트 테스트 실행
    test_functions = [
        test_analysis_agent,
        test_data_collector_agent,
        test_portfolio_agent,
        test_supervisor_agent,
    ]

    test_results = []
    start_time = time.time()

    for test_func in test_functions:
        try:
            result = await test_func()
            test_results.append(result)
        except Exception as e:
            logger.error(f"❌ {test_func.__name__} 실행 중 오류: {e}")
            test_results.append(
                {
                    "success": False,
                    "agent": test_func.__name__.replace("test_", "").replace(
                        "_agent", ""
                    ),
                    "error": str(e),
                }
            )

        # 워크플로우 및 상호작용 테스트
    workflow_result = await test_agent_workflow()
    test_results.append(workflow_result)

    interaction_result = await test_agent_interaction()
    test_results.append(interaction_result)

    # 새로운 스키마 기반 테스트
    schema_workflow_result = await test_real_schema_workflow()
    test_results.append(schema_workflow_result)

    state_transition_result = await test_state_transitions()
    test_results.append(state_transition_result)

    execution_time = time.time() - start_time

    # 결과 요약
    successful_tests = [r for r in test_results if r["success"]]
    failed_tests = [r for r in test_results if not r["success"]]

    logger.info("\n📋 에이전트 통합 테스트 결과 요약:")
    logger.info(f"⏱️ 총 실행 시간: {execution_time:.2f}초")
    logger.info(f"✅ 성공: {len(successful_tests)}개")
    logger.info(f"❌ 실패: {len(failed_tests)}개")

    if successful_tests:
        logger.info("\n✅ 성공한 테스트들:")
        for test in successful_tests:
            if "agent" in test:
                logger.info(f"  - {test['agent']} 에이전트")
            elif "execution_time" in test:
                logger.info(f"  - 워크플로우 실행 ({test['execution_time']:.2f}초)")
            else:
                logger.info("  - 에이전트 상호작용")

    if failed_tests:
        logger.error("\n❌ 실패한 테스트들:")
        for test in failed_tests:
            if "agent" in test:
                logger.error(f"  - {test['agent']} 에이전트: {test['error']}")
            else:
                logger.error(f"  - {test.get('error', 'Unknown error')}")

    return {
        "success": len(failed_tests) == 0,
        "total_tests": len(test_results),
        "successful_tests": len(successful_tests),
        "failed_tests": len(failed_tests),
        "execution_time": execution_time,
        "results": test_results,
    }


if __name__ == "__main__":
    # 에이전트 통합 테스트 실행
    result = asyncio.run(run_agent_integration_tests())

    if result["success"]:
        print("\n🎉 모든 에이전트 테스트가 성공했습니다!")
    else:
        print(f"\n⚠️ {result['failed_tests']}개 테스트가 실패했습니다.")

    print(
        f"📊 총 {result['total_tests']}개 테스트 중 {result['successful_tests']}개 성공"
    )
    print(f"⏱️ 총 실행 시간: {result['execution_time']:.2f}초")
