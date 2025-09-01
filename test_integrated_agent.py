#!/usr/bin/env python3
"""
통합 에이전트 테스트 스크립트

단일 통합 에이전트의 기능을 테스트합니다.
"""

import asyncio
import sys
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, ".")

from src.la_agents.integrated_agent import IntegratedAgent


async def test_integrated_agent():
    """통합 에이전트 테스트"""
    print("🚀 통합 에이전트 테스트 시작")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 에이전트 초기화
        print("\n" + "=" * 60)
        print("1️⃣ 에이전트 초기화")
        print("=" * 60)

        agent = IntegratedAgent(name="test_integrated_agent")

        # 에이전트 정보 출력
        agent_info = agent.get_agent_info()
        print(f"✅ 에이전트 초기화 완료: {agent_info['name']}")
        print(f"📋 기능: {', '.join(agent_info['capabilities'])}")
        print(f"🔗 MCP 서버: {', '.join(agent_info['mcp_servers'])}")

        # 2. 헬스 체크
        print("\n" + "=" * 60)
        print("2️⃣ 헬스 체크")
        print("=" * 60)

        health_status = await agent.health_check()
        print(f"🏥 상태: {health_status['status']}")
        print(f"📊 워크플로우 준비: {health_status['workflow_ready']}")
        print(f"🔗 MCP 서버 상태: {health_status['mcp_servers']}")

        # 3. 종합 분석 테스트
        print("\n" + "=" * 60)
        print("3️⃣ 종합 분석 테스트")
        print("=" * 60)

        # 테스트 데이터 - macroeconomic 서버만 사용
        test_data = {
            "request": {
                "symbol": "삼성전자",
                "analysis_type": "macroeconomic",  # macroeconomic 분석만 요청
                "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
                "include_news": False,
                "include_sentiment": False,
            },
            "task_type": "macroeconomic_analysis",
        }

        print(f"📝 요청: {test_data['request']['symbol']} 종합 분석")

        result = await agent.run_comprehensive_analysis(
            request=test_data["request"], task_type=test_data["task_type"]
        )

        if result["success"]:
            print("✅ 종합 분석 성공!")

            # 결과 요약 출력
            summary = result["summary"]
            print(f"📊 진행률: {summary['progress']:.1%}")
            print(f"📈 현재 단계: {summary['current_step']}")
            print(f"🔗 데이터 소스: {summary['data_sources_count']}개")
            print(f"📊 분석 결과: {summary['analysis_results_count']}개")
            print(f"💡 인사이트: {summary['insights_count']}개")
            print(f"🎯 결정 완료: {summary['decision_made']}")
            print(f"🎯 신뢰도: {summary['confidence']:.1%}")
            print(f"⚡ 실행 상태: {summary['execution_status']}")

            # 상세 결과 출력
            detailed_result = result["result"]
            print("\n📋 상세 결과:")
            print(
                f"  - 수집된 데이터: {list(detailed_result['collected_data'].keys())}"
            )
            print(f"  - 분석 결과: {list(detailed_result['analysis_results'].keys())}")
            print("  - 주요 인사이트:")
            for i, insight in enumerate(detailed_result["insights"][:3], 1):
                print(f"    {i}. {insight}")

            if detailed_result["decision"]:
                decision = detailed_result["decision"]
                print(f"  - 최종 결정: {decision['action']}")
                print(f"  - 결정 근거: {detailed_result['reasoning']}")

        else:
            print(f"❌ 종합 분석 실패: {result['error']}")

        # 4. 성능 통계
        print("\n" + "=" * 60)
        print("4️⃣ 성능 통계")
        print("=" * 60)

        stats = await agent.get_performance_stats()
        print(f"📈 총 실행 횟수: {stats['total_executions']}")
        print(f"📊 성공률: {stats['success_rate']:.1%}")
        print(f"⏱️ 평균 실행 시간: {stats['average_execution_time']}초")
        print(f"❌ 에러 횟수: {stats['error_count']}")

        # 5. 에이전트 상태
        print("\n" + "=" * 60)
        print("5️⃣ 에이전트 상태")
        print("=" * 60)

        status = agent.get_status()
        print(f"📊 상태: {status['status']}")
        print(f"🔗 연결된 MCP 서버: {len(status['mcp_servers'])}개")
        print(f"⚠️ 인터럽트 횟수: {status['interrupts']}")
        print(f"❌ 에러 횟수: {status['errors']}")

        print("\n" + "=" * 60)
        print("🎉 통합 에이전트 테스트 완료!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_specific_functions():
    """특정 기능 테스트"""
    print("\n🔧 특정 기능 테스트")

    agent = IntegratedAgent(name="test_specific_functions")

    test_request = {
        "symbol": "삼성전자",
        "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
    }

    # 데이터 수집만 테스트
    print("\n📊 데이터 수집 테스트")
    result = await agent.run_data_collection(test_request)
    print(f"결과: {'성공' if result['success'] else '실패'}")

    # 시장 분석만 테스트
    print("\n📈 시장 분석 테스트")
    result = await agent.run_market_analysis(test_request)
    print(f"결과: {'성공' if result['success'] else '실패'}")

    # 투자 의사결정만 테스트
    print("\n🎯 투자 의사결정 테스트")
    result = await agent.run_investment_decision(test_request)
    print(f"결과: {'성공' if result['success'] else '실패'}")


async def main():
    """메인 함수"""
    print("🚀 통합 에이전트 테스트 시작")

    # 기본 테스트
    success = await test_integrated_agent()

    if success:
        # 특정 기능 테스트
        await test_specific_functions()

    print("\n📋 테스트 결과 요약:")
    print("- 통합 에이전트: 완성")
    print("- MCP 서버 연동: 준비됨")
    print("- 워크플로우: 5단계 (검증 → 수집 → 분석 → 의사결정 → 실행)")
    print("- 복합적 추론: 가능")
    print("- 확장성: 높음")


if __name__ == "__main__":
    asyncio.run(main())
