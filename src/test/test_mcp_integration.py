"""
MCP 서버 통합 테스트
모든 MCP 서버의 기본 기능과 도구들을 테스트합니다.
"""

import os
import asyncio
import logging
import time
from typing import Dict, Any, List

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def test_macroeconomic_mcp():
    """[MCP 통합] 거시경제 MCP 서버의 기본 기능을 테스트한다"""
    try:
        from mcp_servers.macroeconomic.macroeconomic_client import MacroeconomicClient
        
        logger.info("📊 거시경제 MCP 서버 테스트 시작...")
        
        # 클라이언트 초기화
        client = MacroeconomicClient()
        logger.info(f"✅ 거시경제 클라이언트 초기화 완료: {client.name}")
        
        # 기본 도구 목록 확인
        tools = client.get_available_tools()
        logger.info(f"🔧 사용 가능한 도구: {len(tools)}개")
        
        # 간단한 데이터 처리 테스트
        test_data = {"category": "test", "limit": 5}
        result = await client.get_data_records(**test_data)
        
        assert result["success"] == True, "데이터 레코드 조회 실패"
        logger.info("✅ 거시경제 MCP 서버 테스트 성공")
        
        return {"success": True, "server": "macroeconomic", "tools_count": len(tools)}
        
    except Exception as e:
        logger.error(f"❌ 거시경제 MCP 서버 테스트 실패: {e}")
        return {"success": False, "server": "macroeconomic", "error": str(e)}

async def test_stock_analysis_mcp():
    """[MCP 통합] 주식 분석 MCP 서버의 기본 기능을 테스트한다"""
    try:
        from mcp_servers.stock_analysis.stock_analysis_client import StockAnalysisClient
        
        logger.info("📈 주식 분석 MCP 서버 테스트 시작...")
        
        # 클라이언트 초기화
        client = StockAnalysisClient()
        logger.info(f"✅ 주식 분석 클라이언트 초기화 완료: {client.name}")
        
        # 기본 도구 목록 확인
        tools = client.get_available_tools()
        logger.info(f"🔧 사용 가능한 도구: {len(tools)}개")
        
        # 간단한 분석 테스트
        test_data = {"symbol": "AAPL", "analysis_type": "basic"}
        result = await client.analyze_stock(**test_data)
        
        assert result["success"] == True, "주식 분석 실패"
        logger.info("✅ 주식 분석 MCP 서버 테스트 성공")
        
        return {"success": True, "server": "stock_analysis", "tools_count": len(tools)}
        
    except Exception as e:
        logger.error(f"❌ 주식 분석 MCP 서버 테스트 실패: {e}")
        return {"success": False, "server": "stock_analysis", "error": str(e)}

async def test_naver_news_mcp():
    """[MCP 통합] 네이버 뉴스 MCP 서버의 기본 기능을 테스트한다"""
    try:
        from mcp_servers.naver_news.naver_news_client import NaverNewsClient
        
        logger.info("📰 네이버 뉴스 MCP 서버 테스트 시작...")
        
        # 클라이언트 초기화
        client = NaverNewsClient()
        logger.info(f"✅ 네이버 뉴스 클라이언트 초기화 완료: {client.name}")
        
        # 기본 도구 목록 확인
        tools = client.get_available_tools()
        logger.info(f"🔧 사용 가능한 도구: {len(tools)}개")
        
        # 간단한 뉴스 수집 테스트
        test_data = {"query": "주식", "limit": 3}
        result = await client.collect_news(**test_data)
        
        assert result["success"] == True, "뉴스 수집 실패"
        logger.info("✅ 네이버 뉴스 MCP 서버 테스트 성공")
        
        return {"success": True, "server": "naver_news", "tools_count": len(tools)}
        
    except Exception as e:
        logger.error(f"❌ 네이버 뉴스 MCP 서버 테스트 실패: {e}")
        return {"success": False, "server": "naver_news", "error": str(e)}

async def test_tavily_search_mcp():
    """[MCP 통합] Tavily 검색 MCP 서버의 기본 기능을 테스트한다"""
    try:
        from mcp_servers.tavily_search.tavily_search_client import TavilySearchClient
        
        logger.info("🔍 Tavily 검색 MCP 서버 테스트 시작...")
        
        # 클라이언트 초기화
        client = TavilySearchClient()
        logger.info(f"✅ Tavily 검색 클라이언트 초기화 완료: {client.name}")
        
        # 기본 도구 목록 확인
        tools = client.get_available_tools()
        logger.info(f"🔧 사용 가능한 도구: {len(tools)}개")
        
        # 간단한 검색 테스트
        test_data = {"query": "AI technology", "max_results": 3}
        result = await client.search_web(**test_data)
        
        assert result["success"] == True, "웹 검색 실패"
        logger.info("✅ Tavily 검색 MCP 서버 테스트 성공")
        
        return {"success": True, "server": "tavily_search", "tools_count": len(tools)}
        
    except Exception as e:
        logger.error(f"❌ Tavily 검색 MCP 서버 테스트 실패: {e}")
        return {"success": False, "server": "tavily_search", "error": str(e)}

async def test_kiwoom_mcp():
    """[MCP 통합] 키움 API MCP 서버의 기본 기능을 테스트한다"""
    try:
        from mcp_servers.kiwoom.kiwoom_client import KiwoomClient
        
        logger.info("🏦 키움 API MCP 서버 테스트 시작...")
        
        # 클라이언트 초기화
        client = KiwoomClient()
        logger.info(f"✅ 키움 API 클라이언트 초기화 완료: {client.name}")
        
        # 기본 도구 목록 확인
        tools = client.get_available_tools()
        logger.info(f"🔧 사용 가능한 도구: {len(tools)}개")
        
        # 연결 상태 확인 (실제 거래는 하지 않음)
        status = client.get_connection_status()
        logger.info(f"📡 연결 상태: {status}")
        
        logger.info("✅ 키움 API MCP 서버 테스트 성공")
        
        return {"success": True, "server": "kiwoom", "tools_count": len(tools)}
        
    except Exception as e:
        logger.error(f"❌ 키움 API MCP 서버 테스트 실패: {e}")
        return {"success": False, "server": "kiwoom", "error": str(e)}

async def test_financial_analysis_mcp():
    """[MCP 통합] 재무 분석 MCP 서버의 기본 기능을 테스트한다"""
    try:
        from mcp_servers.financial_analysis.financial_analysis_client import FinancialAnalysisClient
        
        logger.info("💰 재무 분석 MCP 서버 테스트 시작...")
        
        # 클라이언트 초기화
        client = FinancialAnalysisClient()
        logger.info(f"✅ 재무 분석 클라이언트 초기화 완료: {client.name}")
        
        # 기본 도구 목록 확인
        tools = client.get_available_tools()
        logger.info(f"🔧 사용 가능한 도구: {len(tools)}개")
        
        # 간단한 재무 분석 테스트
        test_data = {"symbol": "AAPL", "analysis_type": "ratios"}
        result = await client.analyze_financials(**test_data)
        
        assert result["success"] == True, "재무 분석 실패"
        logger.info("✅ 재무 분석 MCP 서버 테스트 성공")
        
        return {"success": True, "server": "financial_analysis", "tools_count": len(tools)}
        
    except Exception as e:
        logger.error(f"❌ 재무 분석 MCP 서버 테스트 실패: {e}")
        return {"success": False, "server": "financial_analysis", "error": str(e)}

async def run_mcp_integration_tests():
    """[MCP 통합] 모든 MCP 서버 통합 테스트를 실행한다"""
    logger.info("🚀 MCP 서버 통합 테스트 시작")
    
    # 각 MCP 서버 테스트 실행
    test_functions = [
        test_macroeconomic_mcp,
        test_stock_analysis_mcp,
        test_naver_news_mcp,
        test_tavily_search_mcp,
        test_kiwoom_mcp,
        test_financial_analysis_mcp
    ]
    
    test_results = []
    start_time = time.time()
    
    for test_func in test_functions:
        try:
            result = await test_func()
            test_results.append(result)
        except Exception as e:
            logger.error(f"❌ {test_func.__name__} 실행 중 오류: {e}")
            test_results.append({
                "success": False,
                "server": test_func.__name__.replace("test_", "").replace("_mcp", ""),
                "error": str(e)
            })
    
    execution_time = time.time() - start_time
    
    # 결과 요약
    successful_tests = [r for r in test_results if r["success"]]
    failed_tests = [r for r in test_results if not r["success"]]
    
    logger.info(f"\n📋 MCP 통합 테스트 결과 요약:")
    logger.info(f"⏱️ 총 실행 시간: {execution_time:.2f}초")
    logger.info(f"✅ 성공: {len(successful_tests)}개")
    logger.info(f"❌ 실패: {len(failed_tests)}개")
    
    if successful_tests:
        logger.info("\n✅ 성공한 MCP 서버들:")
        for test in successful_tests:
            logger.info(f"  - {test['server']}: {test['tools_count']}개 도구")
    
    if failed_tests:
        logger.error("\n❌ 실패한 MCP 서버들:")
        for test in failed_tests:
            logger.error(f"  - {test['server']}: {test['error']}")
    
    return {
        "success": len(failed_tests) == 0,
        "total_servers": len(test_results),
        "successful_servers": len(successful_tests),
        "failed_servers": len(failed_tests),
        "execution_time": execution_time,
        "results": test_results
    }

if __name__ == "__main__":
    # MCP 통합 테스트 실행
    result = asyncio.run(run_mcp_integration_tests())
    
    if result["success"]:
        print(f"\n🎉 모든 MCP 서버 테스트가 성공했습니다!")
    else:
        print(f"\n⚠️ {result['failed_servers']}개 MCP 서버 테스트가 실패했습니다.")
    
    print(f"📊 총 {result['total_servers']}개 MCP 서버 중 {result['successful_servers']}개 성공")
    print(f"⏱️ 총 실행 시간: {result['execution_time']:.2f}초")