"""
네이버 뉴스 검색 클라이언트

네이버 뉴스 API를 활용한 뉴스 수집 및 감정 분석 기능을 제공합니다.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv

from ..base.base_mcp_client import BaseHTTPClient
from ..base.middleware import MiddlewareManager

# .env 파일에서 환경변수 로드
load_dotenv()

logger = logging.getLogger(__name__)


class NewsAnalysisError(Exception):
    """뉴스 분석 에러"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class NewsClient(BaseHTTPClient):
    """
    네이버 뉴스 클라이언트

    주요 기능:
    - 네이버 뉴스 검색 및 수집
    - 뉴스 텍스트 전처리 및 정제
    - 감정 분석 (긍정/부정/중립)
    - 주식 관련 키워드 추출
    - 시장 임팩트 분석
    """

    def __init__(self):
        """네이버 뉴스 클라이언트 초기화"""
        # 네이버 API 키 설정 (필수)
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")

        # API 키 필수 체크
        if not self.naver_client_id or not self.naver_client_secret:
            raise NewsAnalysisError(
                "네이버 API 키가 필요합니다. 환경변수 NAVER_CLIENT_ID와 "
                "NAVER_CLIENT_SECRET을 설정하세요.",
                "MISSING_API_KEY",
            )

        # BaseHTTPClient 초기화 (네이버 API Rate Limit 고려)
        super().__init__(
            base_url="https://openapi.naver.com",
            timeout=30.0,
            requests_per_second=2,  # 네이버 API 제한 (초당 2회로 보수적 설정)
            requests_per_hour=1000,  # 시간당 1,000건으로 보수적 설정
        )

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager("naver_news")

        # 뉴스 수집 설정
        self.max_news_per_request = 30

        # 감정 분석 키워드
        self.positive_keywords = [
            "상승",
            "증가",
            "호조",
            "개선",
            "성장",
            "확대",
            "긍정",
            "우수",
            "강세",
            "상향",
            "매수",
            "추천",
            "목표가상향",
            "실적개선",
            "수익증가",
            "신고가",
            "돌파",
        ]

        self.negative_keywords = [
            "하락",
            "감소",
            "부진",
            "악화",
            "위기",
            "축소",
            "부정",
            "우려",
            "약세",
            "하향",
            "매도",
            "하향조정",
            "실적부진",
            "손실",
            "신저가",
            "급락",
            "폭락",
        ]

        # 주식 관련 키워드
        self.stock_keywords = [
            "주가",
            "주식",
            "증시",
            "코스피",
            "코스닥",
            "상장",
            "거래량",
            "시가총액",
            "PER",
            "PBR",
            "배당",
            "분할",
            "합병",
            "IPO",
            "공모",
            "기업공개",
        ]

        logger.info(
            f"NewsClient initialized: "
            f"naver_api={'*' * 10 if self.naver_client_id else 'None'}"
        )

    # === 뉴스 수집 메서드들 ===

    async def search_news(
        self,
        query: str,
        display: int = 20,
        start: int = 1,
        sort: str = "date",  # "date" or "sim"
    ) -> list[dict[str, Any]]:
        """네이버 뉴스 검색

        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (1~100, 기본값 10)
            start: 검색 시작 위치 (1~1000, 기본값 1)
            sort: 정렬 옵션 ("date": 날짜순, "sim": 유사도순)

        Returns:
            뉴스 검색 결과 리스트
        """
        try:
            # 네이버 API 헤더
            headers = {
                "X-Naver-Client-Id": self.naver_client_id,
                "X-Naver-Client-Secret": self.naver_client_secret,
            }

            # API 파라미터
            params = {
                "query": query,
                "display": max(display, self.max_news_per_request),
                "start": start,
                "sort": sort,
            }

            # API 호출
            result = await self.get("/v1/search/news", params=params, headers=headers)

            # 에러 체크
            if "errorCode" in result:
                raise NewsAnalysisError(
                    f"네이버 API 에러: {result.get('errorMessage')}",
                    result.get("errorCode"),
                )

            items = result.get("items", [])
            logger.info(f"네이버 뉴스 검색 완료: {query} -> {len(items)}건")

            return items

        except NewsAnalysisError:
            raise
        except Exception as e:
            logger.error(f"News search error: {e}")
            raise NewsAnalysisError(f"News search failed: {e}", "SEARCH_ERROR") from e

    async def get_stock_related_news(
        self, stock_symbol: str, max_results: int = 5
    ) -> Dict[str, Any]:
        """주식 관련 뉴스 수집"""
        try:
            # 캐시 키 생성
            cache_key = self._get_cache_key(
                "stock_news", {"symbol": stock_symbol, "max": max_results}
            )

            # 캐시 확인
            if self._is_cache_valid(cache_key):
                logger.info(f"캐시 히트: 주식 뉴스 {stock_symbol}")
                return self._cache[cache_key]

            # 실제 주식 관련 뉴스 수집
            logger.info(f"주식 관련 뉴스 수집: {stock_symbol}")

            # 주식 심볼로 뉴스 검색
            query = f"{stock_symbol} 주식"
            news_result = await self.search_news(query, max_results)

            # 주식 관련 뉴스로 필터링
            stock_news = []
            for news in news_result.get(
                "items", []
            ):  # Changed from news_result.get("news_items", [])
                if any(
                    keyword in news["title"].lower()
                    for keyword in ["주식", "주가", "투자", "증시"]
                ):
                    stock_news.append(news)

            result = {
                "stock_symbol": stock_symbol,
                "total_news": len(stock_news),
                "news_items": stock_news,
                "query": query,
                "timestamp": datetime.now().isoformat(),
            }

            # 캐시에 저장
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            return result

        except Exception as e:
            logger.error(f"주식 관련 뉴스 수집 실패: {e}")
            raise NewsAnalysisError(f"주식 관련 뉴스 수집 실패: {e}")

    async def close(self):
        """클라이언트 리소스 정리"""
        await super().close()

    def get_service_stats(self) -> dict[str, Any]:
        """서비스 통계 반환"""
        return self.middleware.get_service_stats()
