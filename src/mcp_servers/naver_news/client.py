"""
네이버 뉴스 검색 클라이언트

네이버 뉴스 API를 활용한 뉴스 수집 및 감정 분석 기능을 제공합니다.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

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
            raise NewsAnalysisError(f"주식 관련 뉴스 수집 실패: {e}") from e

    async def analyze_sentiment(
        self, text: str, keywords: list = None
    ) -> Dict[str, Any]:
        """뉴스 감정 분석"""
        try:
            if not text:
                return {
                    "success": False,
                    "error": "분석할 텍스트가 비어있습니다",
                    "message": "텍스트를 입력해주세요",
                }

            # 기본 키워드와 사용자 제공 키워드 결합
            all_keywords = self.positive_keywords + self.negative_keywords
            if keywords:
                all_keywords.extend(keywords)

            # 감정 점수 계산
            positive_count = sum(
                1 for keyword in self.positive_keywords if keyword in text
            )
            negative_count = sum(
                1 for keyword in self.negative_keywords if keyword in text
            )

            # 주식 관련 키워드 확인
            stock_related = any(keyword in text for keyword in self.stock_keywords)

            # 감정 점수 계산 (0-100)
            total_keywords = positive_count + negative_count
            if total_keywords == 0:
                sentiment_score = 50  # 중립
                sentiment = "중립"
            else:
                sentiment_score = (positive_count / total_keywords) * 100
                if sentiment_score > 60:
                    sentiment = "긍정"
                elif sentiment_score < 40:
                    sentiment = "부정"
                else:
                    sentiment = "중립"

            result = {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "sentiment": sentiment,
                "sentiment_score": round(sentiment_score, 2),
                "positive_keywords_found": positive_count,
                "negative_keywords_found": negative_count,
                "stock_related": stock_related,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return {
                "success": True,
                "data": result,
                "message": f"감정 분석 완료: {sentiment} ({sentiment_score:.1f}점)",
            }

        except Exception as e:
            logger.error(f"감정 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "감정 분석에 실패했습니다",
            }

    async def extract_stock_keywords(self, text: str) -> Dict[str, Any]:
        """주식 관련 키워드 추출"""
        try:
            if not text:
                return {
                    "success": False,
                    "error": "분석할 텍스트가 비어있습니다",
                    "message": "텍스트를 입력해주세요",
                }

            # 주식 관련 키워드 찾기
            found_keywords = []
            for keyword in self.stock_keywords:
                if keyword in text:
                    found_keywords.append(keyword)

            # 키워드 카테고리별 분류
            categories = {
                "시장": ["주가", "주식", "증시", "코스피", "코스닥"],
                "거래": ["거래량", "매수", "매도", "호가"],
                "기업": ["상장", "IPO", "공모", "기업공개"],
                "분석": ["PER", "PBR", "배당", "분할", "합병"],
            }

            categorized_keywords = {}
            for category, keywords in categories.items():
                category_found = [kw for kw in keywords if kw in text]
                if category_found:
                    categorized_keywords[category] = category_found

            result = {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "total_keywords_found": len(found_keywords),
                "keywords": found_keywords,
                "categorized_keywords": categorized_keywords,
                "extraction_timestamp": datetime.now().isoformat(),
            }

            return {
                "success": True,
                "data": result,
                "message": f"주식 키워드 추출 완료: {len(found_keywords)}개 발견",
            }

        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "키워드 추출에 실패했습니다",
            }

    async def close(self):
        """클라이언트 리소스 정리"""
        await super().close()

    def get_service_stats(self) -> dict[str, Any]:
        """서비스 통계 반환"""
        return self.middleware.get_service_stats()

    async def get_server_health(self) -> Dict[str, Any]:
        """서버 헬스 상태 조회"""
        return {
            "status": "healthy",
            "service": "NaverNews",
            "timestamp": datetime.now().isoformat(),
            "message": "NaverNews MCP 서버가 정상적으로 작동 중입니다",
        }

    async def get_server_metrics(self) -> Dict[str, Any]:
        """서버 메트릭 조회"""
        return {
            "service": "NaverNews",
            "cache_entries": len(self._cache) if hasattr(self, "_cache") else 0,
            "naver_api_configured": bool(
                self.naver_client_id and self.naver_client_secret
            ),
            "max_news_per_request": self.max_news_per_request,
            "timestamp": datetime.now().isoformat(),
            "message": "NaverNews MCP 서버 메트릭 정보",
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록을 반환합니다."""
        return [
            {
                "name": "search_news_articles",
                "description": "네이버 뉴스에서 주제별 뉴스 기사를 검색하고 감정 분석을 수행합니다",
                "parameters": {
                    "query": {"type": "string", "description": "검색할 키워드"},
                    "max_results": {
                        "type": "int",
                        "description": "최대 결과 수 (기본값: 10)",
                    },
                },
            },
            {
                "name": "analyze_news_sentiment",
                "description": "뉴스 기사의 감정을 분석하여 긍정/부정/중립을 판단합니다",
                "parameters": {
                    "text": {"type": "string", "description": "분석할 텍스트"},
                    "keywords": {
                        "type": "list",
                        "description": "추가 키워드 (선택사항)",
                    },
                },
            },
            {
                "name": "extract_stock_keywords",
                "description": "텍스트에서 주식 관련 키워드를 추출합니다",
                "parameters": {
                    "text": {"type": "string", "description": "키워드를 추출할 텍스트"}
                },
            },
            {
                "name": "get_stock_news",
                "description": "주식 관련 뉴스 수집",
                "parameters": {
                    "symbol": {"type": "string", "description": "주식 심볼"},
                    "max_results": {
                        "type": "int",
                        "description": "최대 결과 수 (기본값: 5)",
                    },
                },
            },
            {
                "name": "get_server_health",
                "description": "서버 헬스 상태 조회",
                "parameters": {},
            },
            {
                "name": "get_server_metrics",
                "description": "서버 메트릭 조회",
                "parameters": {},
            },
        ]

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """도구 호출"""
        try:
            if tool_name == "search_news_articles":
                query = kwargs.get("query", "")
                max_results = kwargs.get("max_results", 10)
                return await self.search_news(query, max_results)
            elif tool_name == "analyze_news_sentiment":
                text = kwargs.get("text", "")
                keywords = kwargs.get("keywords", [])
                return await self.analyze_sentiment(text, keywords)
            elif tool_name == "extract_stock_keywords":
                text = kwargs.get("text", "")
                return await self.extract_stock_keywords(text)
            elif tool_name == "get_stock_news":
                symbol = kwargs.get("symbol", "")
                max_results = kwargs.get("max_results", 5)
                return await self.get_stock_related_news(symbol, max_results)
            elif tool_name == "get_server_health":
                return await self.get_server_health()
            elif tool_name == "get_server_metrics":
                return await self.get_server_metrics()
            else:
                return {
                    "success": False,
                    "error": f"알 수 없는 도구: {tool_name}",
                    "tool_name": tool_name,
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"도구 호출 실패: {e}",
                "tool_name": tool_name,
            }
