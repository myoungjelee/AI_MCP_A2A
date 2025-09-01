#!/usr/bin/env python3
"""
수정된 통합 에이전트 최종 테스트
"""

import asyncio
import logging

import aiohttp

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_final_integrated_agent():
    """최종 통합 에이전트 테스트"""

    # 테스트 데이터
    test_data = {
        "request": {
            "symbol": "삼성전자",
            "analysis_type": "comprehensive",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "include_news": True,
            "include_sentiment": True,
        },
        "task_type": "comprehensive_analysis",
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. 헬스 체크
            logger.info("🔍 1. 헬스 체크...")
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"✅ 헬스 체크 성공: {health_data['status']}")
                    logger.info(f"📊 워크플로우 준비: {health_data['workflow_ready']}")
                    logger.info(f"🔗 MCP 서버 상태: {health_data['mcp_servers']}")
                else:
                    logger.error(f"❌ 헬스 체크 실패: {response.status}")
                    return

            # 2. 분석 요청
            logger.info("\n🔍 2. 종합 분석 요청...")
            async with session.post(
                "http://localhost:8000/analyze",
                json=test_data,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ 분석 요청 성공!")
                    logger.info(f"📈 성공 여부: {result.get('success', False)}")

                    if result.get("success"):
                        summary = result.get("summary", {})
                        logger.info(
                            f"📊 처리 단계: {summary.get('current_step', 'N/A')}"
                        )
                        logger.info(f"📈 진행률: {summary.get('progress', 0):.1%}")
                        logger.info(
                            f"🔍 데이터 소스 수: {summary.get('data_sources_count', 0)}"
                        )
                        logger.info(
                            f"📋 분석 결과 수: {summary.get('analysis_results_count', 0)}"
                        )
                        logger.info(
                            f"💡 인사이트 수: {summary.get('insights_count', 0)}"
                        )
                        logger.info(
                            f"⚡ 의사결정 완료: {summary.get('decision_made', False)}"
                        )
                        logger.info(f"❌ 에러 수: {summary.get('error_count', 0)}")
                    else:
                        logger.error(
                            f"❌ 분석 실패: {result.get('error', 'Unknown error')}"
                        )

                else:
                    logger.error(f"❌ 분석 요청 실패: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error details: {error_text}")

    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")


if __name__ == "__main__":
    asyncio.run(test_final_integrated_agent())
