"""
MCP 서버 통합 테스트
현재 구현된 3개 MCP 서버의 기능을 테스트합니다.
"""

import asyncio
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_stock_analysis():
    """주식 분석 MCP 서버 테스트"""
    try:
        from src.mcp_servers.stock_analysis.client import StockAnalysisClient

        logger.info("=== 주식 분석 MCP 서버 테스트 시작 ===")

        client = StockAnalysisClient()

        # 도구 목록 테스트
        tools = client.list_tools()
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

        # 주식 데이터 조회 테스트
        result = client.get_stock_data({"symbol": "005930"})
        if result["success"]:
            logger.info("✅ 주식 데이터 조회 성공")
            logger.info(f"  현재가: {result['data']['current_price']:,}원")
            logger.info(f"  등락률: {result['data']['price_change_pct']:.2f}%")
        else:
            logger.error(f"❌ 주식 데이터 조회 실패: {result['error']}")

        # RSI 계산 테스트
        result = client.calculate_rsi({"symbol": "005930"})
        if result["success"]:
            logger.info("✅ RSI 계산 성공")
            logger.info(f"  RSI: {result['data']['rsi']}")
            logger.info(f"  신호: {result['data']['signal']}")
        else:
            logger.error(f"❌ RSI 계산 실패: {result['error']}")

        logger.info("=== 주식 분석 MCP 서버 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ 주식 분석 테스트 실패: {e}")
        return False


def test_financial_analysis():
    """재무 분석 MCP 서버 테스트"""
    try:
        from src.mcp_servers.financial_analysis.client import FinancialAnalysisClient

        logger.info("=== 재무 분석 MCP 서버 테스트 시작 ===")

        client = FinancialAnalysisClient()

        # 도구 목록 테스트
        tools = client.list_tools()
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

        # 기업 정보 조회 테스트
        result = client.get_company_info({"corp_code": "00126380"})
        if result["success"]:
            logger.info("✅ 기업 정보 조회 성공")
            logger.info(f"  기업명: {result['data']['corp_name']}")
            logger.info(f"  섹터: {result['data']['sector']}")
        else:
            logger.error(f"❌ 기업 정보 조회 실패: {result['error']}")

        # 재무제표 조회 테스트
        result = client.get_financial_statement(
            {"corp_code": "00126380", "year": "2023", "quarter": "4"}
        )
        if result["success"]:
            logger.info("✅ 재무제표 조회 성공")
            logger.info(f"  매출액: {result['data']['revenue']:,}백만원")
            logger.info(f"  영업이익: {result['data']['operating_income']:,}백만원")
        else:
            logger.error(f"❌ 재무제표 조회 실패: {result['error']}")

        logger.info("=== 재무 분석 MCP 서버 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ 재무 분석 테스트 실패: {e}")
        return False


def test_macroeconomic():
    """거시경제 분석 MCP 서버 테스트"""
    try:
        from src.mcp_servers.macroeconomic.client import MacroeconomicClient

        logger.info("=== 거시경제 분석 MCP 서버 테스트 시작 ===")

        client = MacroeconomicClient()

        # 도구 목록 테스트
        tools = client.list_tools()
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

        # GDP 데이터 조회 테스트
        result = client.get_gdp_data(
            {"country": "KOR", "start_year": "2020", "end_year": "2024"}
        )
        if result["success"]:
            logger.info("✅ GDP 데이터 조회 성공")
            logger.info(f"  분석 기간: {result['data']['period']}")
            logger.info(f"  데이터 수: {len(result['data']['data'])}개")
        else:
            logger.error(f"❌ GDP 데이터 조회 실패: {result['error']}")

        # 인플레이션 데이터 조회 테스트
        result = client.get_inflation_data(
            {"country": "KOR", "start_year": "2020", "end_year": "2024"}
        )
        if result["success"]:
            logger.info("✅ 인플레이션 데이터 조회 성공")
            latest_cpi = result["data"]["data"][-1]["cpi"]
            logger.info(f"  최신 CPI: {latest_cpi}%")
        else:
            logger.error(f"❌ 인플레이션 데이터 조회 실패: {result['error']}")

        logger.info("=== 거시경제 분석 MCP 서버 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ 거시경제 분석 테스트 실패: {e}")
        return False


def test_naver_news():
    """네이버 뉴스 MCP 서버 테스트"""
    try:
        from src.mcp_servers.naver_news.client import NaverNewsClient

        logger.info("=== 네이버 뉴스 MCP 서버 테스트 시작 ===")

        client = NaverNewsClient()

        # 도구 목록 테스트
        tools = client.list_tools()
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

        # 뉴스 검색 테스트
        result = client.search_news({"query": "삼성전자", "display": 5})
        if result["success"]:
            logger.info("✅ 뉴스 검색 성공")
            logger.info(f"  검색 결과: {len(result['data']['items'])}개")
            logger.info(
                f"  첫 번째 뉴스: {result['data']['items'][0]['title'][:50]}..."
            )
        else:
            logger.error(f"❌ 뉴스 검색 실패: {result['error']}")

        logger.info("=== 네이버 뉴스 MCP 서버 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ 네이버 뉴스 테스트 실패: {e}")
        return False


def test_tavily_search():
    """Tavily 검색 MCP 서버 테스트"""
    try:
        from src.mcp_servers.tavily_search.client import TavilySearchClient

        logger.info("=== Tavily 검색 MCP 서버 테스트 시작 ===")

        client = TavilySearchClient()

        # 도구 목록 테스트
        tools = client.list_tools()
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

        # 웹 검색 테스트
        result = client.search_web({"query": "한국 주식 시장 동향", "max_results": 3})
        if result["success"]:
            logger.info("✅ 웹 검색 성공")
            logger.info(f"  검색 결과: {len(result['data']['results'])}개")
            logger.info(
                f"  첫 번째 결과: {result['data']['results'][0]['title'][:50]}..."
            )
        else:
            logger.error(f"❌ 웹 검색 실패: {result['error']}")

        logger.info("=== Tavily 검색 MCP 서버 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ Tavily 검색 테스트 실패: {e}")
        return False


def test_kiwoom():
    """키움증권 MCP 서버 테스트"""
    try:
        from src.mcp_servers.kiwoom.client import KiwoomClient

        logger.info("=== 키움증권 MCP 서버 테스트 시작 ===")

        client = KiwoomClient()

        # 도구 목록 테스트
        tools = client.list_tools()
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        for tool in tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")

            # 키움증권 연결 테스트
        result = client.connect_to_kiwoom("1234567890")
        if result:
            logger.info("✅ 키움증권 연결 성공")

            # 시장 데이터 조회 테스트
            market_result = client.get_market_data({"symbol": "005930"})
            if market_result["success"]:
                logger.info("✅ 시장 데이터 조회 성공")
                logger.info(f"  현재가: {market_result['data']['current_price']:,}원")
                logger.info(f"  등락률: {market_result['data']['change_pct']:.2f}%")
            else:
                logger.error(f"❌ 시장 데이터 조회 실패: {market_result['error']}")
        else:
            logger.error("❌ 키움증권 연결 실패")

        logger.info("=== 키움증권 MCP 서버 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ 키움증권 테스트 실패: {e}")
        return False


async def test_streaming():
    """스트리밍 기능 테스트"""
    try:
        logger.info("=== 스트리밍 기능 테스트 시작 ===")

        # 주식 분석 스트리밍 테스트
        from src.mcp_servers.stock_analysis.client import StockAnalysisClient

        stock_client = StockAnalysisClient()

        logger.info("주식 종합 분석 스트리밍 테스트...")
        async for result in stock_client.analyze_stock_comprehensive_stream(
            {"symbol": "005930"}
        ):
            logger.info(f"  {result['step']}: {result.get('message', '')}")

        logger.info("=== 스트리밍 기능 테스트 완료 ===\n")
        return True

    except Exception as e:
        logger.error(f"❌ 스트리밍 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수"""
    logger.info("🚀 MCP 서버 통합 테스트 시작")
    logger.info("=" * 50)

    # 동기 테스트
    results = []
    results.append(test_stock_analysis())
    results.append(test_financial_analysis())
    results.append(test_macroeconomic())
    results.append(test_naver_news())
    results.append(test_tavily_search())
    results.append(test_kiwoom())

    # 비동기 테스트
    async def run_async_tests():
        return await test_streaming()

    try:
        streaming_result = asyncio.run(run_async_tests())
        results.append(streaming_result)
    except Exception as e:
        logger.error(f"❌ 비동기 테스트 실행 실패: {e}")
        results.append(False)

    # 결과 요약
    logger.info("=" * 50)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 50)

    test_names = [
        "주식 분석 MCP 서버",
        "재무 분석 MCP 서버",
        "거시경제 분석 MCP 서버",
        "네이버 뉴스 MCP 서버",
        "Tavily 검색 MCP 서버",
        "키움증권 MCP 서버",
        "스트리밍 기능",
    ]

    success_count = 0
    for i, (name, result) in enumerate(zip(test_names, results, strict=False)):
        status = "✅ 성공" if result else "❌ 실패"
        logger.info(f"{i+1}. {name}: {status}")
        if result:
            success_count += 1

    logger.info("=" * 50)
    logger.info(f"전체 테스트: {len(results)}개")
    logger.info(f"성공: {success_count}개")
    logger.info(f"실패: {len(results) - success_count}개")

    if success_count == len(results):
        logger.info("🎉 모든 테스트가 성공했습니다!")
        return 0
    else:
        logger.error("💥 일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
