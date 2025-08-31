#!/usr/bin/env python3
"""
모든 에이전트를 한번에 테스트하는 통합 스크립트
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_all_agents.log"),
    ],
)
logger = logging.getLogger(__name__)


async def test_supervisor_agent():
    """Supervisor Agent 테스트"""
    logger.info("👑 Supervisor Agent 테스트 시작...")

    try:
        from src.la_agents.supervisor_agent import SupervisorAgent

        agent = SupervisorAgent()
        workflow = agent.build_graph()

        # 더미 데이터로 테스트
        test_input = {
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

        result = await workflow.ainvoke(test_input)

        if result:
            logger.info("✅ Supervisor Agent 테스트 성공!")
            return True
        else:
            logger.error("❌ Supervisor Agent 테스트 실패!")
            return False

    except Exception as e:
        logger.error(f"💥 Supervisor Agent 테스트 실패: {e}")
        return False


async def test_analysis_agent():
    """Analysis Agent 테스트"""
    logger.info("🔍 Analysis Agent 테스트 시작...")

    try:
        from src.la_agents.analysis_agent import AnalysisAgent

        agent = AnalysisAgent()
        workflow = agent.build_graph()

        # 더미 데이터로 테스트
        test_input = {
            "symbols": ["삼성전자", "SK하이닉스"],
            "price_data": {
                "삼성전자": {"current": 70000, "change": 2.5},
                "SK하이닉스": {"current": 120000, "change": -1.2},
            },
            "analysis_type": "comprehensive",
        }

        result = await workflow.ainvoke(test_input)

        if result:
            logger.info("✅ Analysis Agent 테스트 성공!")
            return True
        else:
            logger.error("❌ Analysis Agent 테스트 실패!")
            return False

    except Exception as e:
        logger.error(f"💥 Analysis Agent 테스트 실패: {e}")
        return False


async def test_data_collector_agent():
    """Data Collector Agent 테스트"""
    logger.info("📊 Data Collector Agent 테스트 시작...")

    try:
        from src.la_agents.data_collector_agent import DataCollectorAgent

        agent = DataCollectorAgent()
        workflow = agent.build_graph()

        # 더미 데이터로 테스트
        test_input = {
            "symbols": ["삼성전자", "SK하이닉스", "LG에너지솔루션"],
            "data_types": ["price", "news", "financial", "technical"],
            "time_range": "1M",
            "update_frequency": "daily",
        }

        result = await workflow.ainvoke(test_input)

        if result:
            logger.info("✅ Data Collector Agent 테스트 성공!")
            return True
        else:
            logger.error("❌ Data Collector Agent 테스트 실패!")
            return False

    except Exception as e:
        logger.error(f"💥 Data Collector Agent 테스트 실패: {e}")
        return False


async def test_portfolio_agent():
    """Portfolio Agent 테스트"""
    logger.info("💼 Portfolio Agent 테스트 시작...")

    try:
        from src.la_agents.portfolio_agent import PortfolioAgent

        agent = PortfolioAgent()
        workflow = agent.build_graph()

        # 더미 데이터로 테스트
        test_input = {
            "analysis_results": {
                "삼성전자": {
                    "score": 0.85,
                    "risk": "medium",
                    "growth_potential": "high",
                    "sector": "technology",
                },
                "SK하이닉스": {
                    "score": 0.78,
                    "risk": "high",
                    "growth_potential": "medium",
                    "sector": "technology",
                },
                "LG에너지솔루션": {
                    "score": 0.92,
                    "risk": "low",
                    "growth_potential": "very_high",
                    "sector": "energy",
                },
            },
            "risk_tolerance": "moderate",
            "target_return": 0.15,
            "investment_horizon": "5Y",
            "portfolio_size": 100000000,
        }

        result = await workflow.ainvoke(test_input)

        if result:
            logger.info("✅ Portfolio Agent 테스트 성공!")
            return True
        else:
            logger.error("❌ Portfolio Agent 테스트 실패!")
            return False

    except Exception as e:
        logger.error(f"💥 Portfolio Agent 테스트 실패: {e}")
        return False


async def test_all_agents():
    """모든 에이전트 테스트"""
    logger.info("🚀 모든 에이전트 테스트 시작")
    logger.info("=" * 60)

    start_time = time.time()
    results = {}

    # 각 에이전트 테스트 실행
    agents_to_test = [
        ("Supervisor", test_supervisor_agent),
        ("Analysis", test_analysis_agent),
        ("Data Collector", test_data_collector_agent),
        ("Portfolio", test_portfolio_agent),
    ]

    for agent_name, test_func in agents_to_test:
        logger.info(f"\n🔧 {agent_name} Agent 테스트 중...")
        try:
            success = await test_func()
            results[agent_name] = success
            if success:
                logger.info(f"✅ {agent_name} Agent 테스트 성공!")
            else:
                logger.error(f"❌ {agent_name} Agent 테스트 실패!")
        except Exception as e:
            logger.error(f"💥 {agent_name} Agent 테스트 중 오류: {e}")
            results[agent_name] = False

    execution_time = time.time() - start_time

    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("📊 모든 에이전트 테스트 결과 요약")
    logger.info("=" * 60)

    successful_agents = [name for name, success in results.items() if success]
    failed_agents = [name for name, success in results.items() if not success]

    logger.info(f"⏱️ 총 실행 시간: {execution_time:.2f}초")
    logger.info(f"✅ 성공: {len(successful_agents)}개")
    logger.info(f"❌ 실패: {len(failed_agents)}개")

    if successful_agents:
        logger.info("\n✅ 성공한 에이전트들:")
        for name in successful_agents:
            logger.info(f"  - {name} Agent")

    if failed_agents:
        logger.error("\n❌ 실패한 에이전트들:")
        for name in failed_agents:
            logger.error(f"  - {name} Agent")

    # 전체 성공 여부
    overall_success = len(failed_agents) == 0

    if overall_success:
        logger.info("\n🎉 모든 에이전트 테스트가 성공했습니다!")
        logger.info("🚀 AI MCP A2A 프로젝트의 모든 에이전트가 정상적으로 작동합니다!")
    else:
        logger.error("\n⚠️ 일부 에이전트 테스트가 실패했습니다.")
        logger.info("🔧 문제를 해결한 후 다시 테스트해주세요.")

    return overall_success


async def main():
    """메인 함수"""
    # 환경 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        logger.info("💡 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return False

    logger.info("✅ 환경 설정 확인 완료")

    # 모든 에이전트 테스트 실행
    success = await test_all_agents()

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)
