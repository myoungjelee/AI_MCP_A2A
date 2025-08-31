#!/usr/bin/env python3
"""
Portfolio Agent 개별 테스트 스크립트
"""

import asyncio
import logging
import os
import sys
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
        logging.FileHandler("test_portfolio_agent.log"),
    ],
)
logger = logging.getLogger(__name__)


async def test_portfolio_agent():
    """Portfolio Agent 테스트"""
    logger.info("💼 Portfolio Agent 테스트 시작...")

    try:
        # Portfolio Agent 임포트
        from src.la_agents.portfolio_agent import PortfolioAgent

        # 에이전트 생성
        logger.info("📦 Portfolio Agent 인스턴스 생성...")
        portfolio_agent = PortfolioAgent()
        logger.info("✅ Portfolio Agent 생성 완료")

        # 워크플로우 구축
        logger.info("🏗️ 워크플로우 구축...")
        workflow = portfolio_agent.build_graph()
        logger.info("✅ 워크플로우 구축 완료")

        # 더미 데이터로 테스트
        logger.info("🧪 더미 데이터로 워크플로우 테스트...")
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

        logger.info(
            f"📊 테스트 입력: {len(test_input['analysis_results'])}개 종목 분석"
        )

        # 워크플로우 실행
        start_time = asyncio.get_event_loop().time()
        result = await workflow.ainvoke(test_input)
        execution_time = asyncio.get_event_loop().time() - start_time

        logger.info(f"⏱️ 실행 시간: {execution_time:.2f}초")
        logger.info(f"📋 결과 상태: {result.get('status', 'unknown')}")

        # 결과 검증
        if result:
            logger.info("✅ 워크플로우 실행 성공!")
            logger.info(f"📊 결과 키: {list(result.keys())}")

            # 주요 결과 확인
            if "portfolio_allocation" in result:
                portfolio_allocation = result["portfolio_allocation"]
                logger.info(f"💼 포트폴리오 배분: {len(portfolio_allocation)}개 종목")

            if "risk_metrics" in result:
                risk_metrics = result["risk_metrics"]
                logger.info(f"⚠️ 리스크 지표: {risk_metrics}")

            if "expected_return" in result:
                expected_return = result["expected_return"]
                logger.info(f"📈 예상 수익률: {expected_return}")

            if "rebalancing_recommendations" in result:
                rebalancing = result["rebalancing_recommendations"]
                logger.info(f"🔄 리밸런싱 추천: {len(rebalancing)}개")

            return True
        else:
            logger.error("❌ 워크플로우 실행 실패")
            return False

    except Exception as e:
        logger.error(f"💥 Portfolio Agent 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    logger.info("🚀 Portfolio Agent 개별 테스트 시작")
    logger.info("=" * 50)

    # 환경 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        logger.info("💡 .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return False

    logger.info("✅ 환경 설정 확인 완료")

    # 테스트 실행
    success = await test_portfolio_agent()

    if success:
        logger.info("🎉 Portfolio Agent 테스트 성공!")
        return True
    else:
        logger.error("⚠️ Portfolio Agent 테스트 실패!")
        return False


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
