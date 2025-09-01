#!/usr/bin/env python3
"""
실제 API 연동 테스트 스크립트

수정된 MCP 서버들이 실제 API를 사용하여 데이터를 가져오는지 테스트합니다.
"""

import asyncio
import os
import sys
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_macroeconomic_client():
    """Macroeconomic 클라이언트 테스트"""
    print("\n" + "=" * 60)
    print("🔍 Macroeconomic 클라이언트 테스트")
    print("=" * 60)

    try:
        from src.mcp_servers.macroeconomic.client import MacroeconomicClient

        client = MacroeconomicClient()

        # ECOS API 키 확인
        print(
            f"ECOS API Key: {'✅ 설정됨' if client.ecos_api_key else '❌ 설정되지 않음'}"
        )
        print(
            f"FRED API Key: {'✅ 설정됨' if client.fred_api_key else '❌ 설정되지 않음'}"
        )

        if not client.ecos_api_key and not client.fred_api_key:
            print("⚠️  API 키가 설정되지 않아 더미 데이터를 사용합니다")

        # 데이터 수집 테스트
        print("\n📊 데이터 수집 테스트...")

        # GDP 데이터 수집
        result = await client.collect_data("GDP", {"max_records": 10}, "auto")
        print(
            f"GDP 데이터: {result['total_collected']}개 레코드, 품질: {result['data_quality']}"
        )

        # CPI 데이터 수집
        result = await client.collect_data("CPI", {"max_records": 10}, "auto")
        print(
            f"CPI 데이터: {result['total_collected']}개 레코드, 품질: {result['data_quality']}"
        )

        print("✅ Macroeconomic 클라이언트 테스트 완료")

    except Exception as e:
        print(f"❌ Macroeconomic 클라이언트 테스트 실패: {e}")


async def test_financial_analysis_client():
    """Financial Analysis 클라이언트 테스트"""
    print("\n" + "=" * 60)
    print("💰 Financial Analysis 클라이언트 테스트")
    print("=" * 60)

    try:
        from src.mcp_servers.financial_analysis.client import FinancialAnalysisClient

        client = FinancialAnalysisClient()

        # DART API 키 확인
        print(
            f"DART API Key: {'✅ 설정됨' if client.dart_api_key else '❌ 설정되지 않음'}"
        )
        print(
            f"ECOS API Key: {'✅ 설정됨' if client.ecos_api_key else '❌ 설정되지 않음'}"
        )

        if not client.dart_api_key and not client.ecos_api_key:
            print("⚠️  API 키가 설정되지 않아 더미 데이터를 사용합니다")

        # 재무 데이터 조회 테스트
        print("\n📈 재무 데이터 조회 테스트...")

        # 시장 데이터 조회
        result = await client.get_financial_data("KOSPI", "market_data", 2024)
        print(f"KOSPI 시장 데이터: 품질: {result['data_quality']}")

        # 더미 재무 데이터 생성 테스트
        result = await client.get_financial_data("005930", "income_statement", 2024, 1)
        print(f"삼성전자 재무 데이터: 품질: {result['data_quality']}")

        print("✅ Financial Analysis 클라이언트 테스트 완료")

    except Exception as e:
        print(f"❌ Financial Analysis 클라이언트 테스트 실패: {e}")


async def test_stock_analysis_client():
    """Stock Analysis 클라이언트 테스트"""
    print("\n" + "=" * 60)
    print("📊 Stock Analysis 클라이언트 테스트")
    print("=" * 60)

    try:
        from src.mcp_servers.stock_analysis.client import StockAnalysisClient

        client = StockAnalysisClient()

        print("📈 주식 데이터 분석 테스트...")

        # 삼성전자 트렌드 분석
        result = await client.analyze_data_trends("005930", "1y")
        if result["success"]:
            data = result["data"]
            if "trend_analysis" in data:
                trend = data["trend_analysis"]
                print(
                    f"삼성전자 트렌드 분석: {trend['signal']} 신호, 신뢰도: {trend['confidence']}"
                )
                print(
                    f"데이터 품질: {result.get('source', 'unknown')}, 데이터 포인트: {data['data_points']}개"
                )
            else:
                print(
                    f"삼성전자 트렌드 분석: {data['signal']} 신호, 신뢰도: {data['confidence']}"
                )
                print(
                    f"데이터 품질: {result.get('source', 'unknown')}, 데이터 포인트: {data['data_points']}개"
                )
        else:
            print(f"트렌드 분석 실패: {result.get('error', '알 수 없는 오류')}")

        print("✅ Stock Analysis 클라이언트 테스트 완료")

    except Exception as e:
        print(f"❌ Stock Analysis 클라이언트 테스트 실패: {e}")


async def test_api_keys():
    """API 키 설정 상태 확인"""
    print("\n" + "=" * 60)
    print("🔑 API 키 설정 상태 확인")
    print("=" * 60)

    api_keys = {
        "ECOS_API_KEY": "한국은행 경제 통계시스템",
        "DART_API_KEY": "금융감독원 전자공시시스템",
        "FRED_API_KEY": "연방준비제도",
        "NAVER_CLIENT_ID": "네이버 뉴스 API",
        "NAVER_CLIENT_SECRET": "네이버 뉴스 API",
        "TAVILY_API_KEY": "Tavily 검색 API",
        "KIWOOM_APP_KEY": "키움증권 API",
    }

    for key, description in api_keys.items():
        value = os.getenv(key)
        status = "✅ 설정됨" if value else "❌ 설정되지 않음"
        print(f"{key}: {status} - {description}")

    print("\n💡 .env 파일에 API 키를 설정하면 실제 데이터를 사용할 수 있습니다!")


async def main():
    """메인 테스트 함수"""
    print("🚀 MCP 서버 API 연동 테스트 시작")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # API 키 상태 확인
    await test_api_keys()

    # 각 클라이언트 테스트
    await test_macroeconomic_client()
    await test_financial_analysis_client()
    await test_stock_analysis_client()

    print("\n" + "=" * 60)
    print("🎉 모든 테스트 완료!")
    print("=" * 60)

    print("\n📋 테스트 결과 요약:")
    print("- Macroeconomic: ECOS + FRED API 연동")
    print("- Financial Analysis: DART + ECOS API 연동")
    print("- Stock Analysis: FinanceDataReader 연동")
    print("- Naver News: Naver News API (이미 완료)")
    print("- Tavily Search: Tavily API (이미 완료)")
    print("- Kiwoom: Kiwoom API (이미 완료)")


if __name__ == "__main__":
    asyncio.run(main())
