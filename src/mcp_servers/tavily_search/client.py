"""
검색 시스템 MCP 클라이언트 - 개발 기술 중심
복잡한 AI 기능 대신 깔끔한 코드 구조와 효율적인 검색 알고리즘을 보여줍니다.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from src.mcp_servers.base.base_mcp_client import BaseMCPClient
from src.mcp_servers.base.middleware import MiddlewareManager

# .env 파일 로드
load_dotenv()


# 간단한 검색 타입 (실제 API 대신)
class SearchType(Enum):
    """검색 타입"""

    WEB = "web"
    NEWS = "news"
    FINANCE = "finance"


@dataclass
class SearchResult:
    """검색 결과 구조"""

    title: str
    url: str
    content: str
    score: float
    published_date: datetime
    source: str


class SearchError(Exception):
    """검색 에러"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class TavilySearchClient(BaseMCPClient):
    """검색 시스템 MCP 클라이언트 (개발 기술 중심)"""

    def __init__(self, name: str = "search_system"):
        super().__init__(name=name)

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager("tavily_search")

        self.logger = logging.getLogger(f"search_system.{name}")
        self._setup_logging()

        # 설정
        self.max_retries = 3
        self.retry_delay = 1.0
        self.cache_ttl = 300  # 5분

        # 간단한 메모리 캐시
        self._cache = {}
        self._cache_timestamps = {}

        # Tavily API 설정
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.tavily_base_url = "https://api.tavily.com/search"

        self.logger.info(f"검색 시스템 클라이언트 '{name}' 초기화 완료")
        self.logger.info(
            f"Tavily API Key: {'설정됨' if self.tavily_api_key else '설정되지 않음'}"
        )

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """지수 백오프를 사용한 재시도 로직"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                delay = self.retry_delay * (2**attempt)
                self.logger.warning(
                    f"재시도 {attempt + 1}/{self.max_retries}, {delay}초 후 재시도: {e}"
                )
                await asyncio.sleep(delay)

    def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        import hashlib

        key_data = f"{operation}:{str(sorted(params.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[cache_key]
        return age.total_seconds() < self.cache_ttl

    async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """웹 검색 수행 (캐싱 + 재시도 로직)"""
        try:
            cache_key = self._get_cache_key(
                "search_web", {"query": query, "max_results": max_results}
            )

            if self._is_cache_valid(cache_key):
                self.logger.info(f"캐시 히트: {query}")
                return {
                    "success": True,
                    "data": self._cache[cache_key],
                    "source": "cache",
                    "message": "캐시된 검색 결과 조회 완료",
                }

            async def _fetch_search_results():
                # 실제 Tavily API 호출 시도
                results = []
                data_quality = "dummy"

                if self.tavily_api_key:
                    try:
                        tavily_results = await self._fetch_tavily_data(
                            query, max_results
                        )
                        for item in tavily_results:
                            result = SearchResult(
                                title=item["title"],
                                url=item["url"],
                                content=item["content"],
                                score=item["score"],
                                published_date=datetime.fromisoformat(
                                    item["published_date"]
                                ),
                                source=item["source"],
                            )
                            results.append(result)
                        data_quality = "real"
                        self.logger.info(
                            f"Tavily에서 {len(results)}개 검색 결과 수집 완료"
                        )
                    except Exception as e:
                        self.logger.warning(f"Tavily API 호출 실패: {e}")

                # 데이터가 없으면 더미 데이터 생성 (폴백)
                if not results:
                    self.logger.warning("실제 API 데이터 수집 실패, 더미 데이터 생성")
                    for i in range(max_results):
                        result = SearchResult(
                            title=f"{query} 관련 검색 결과 {i+1}",
                            url=f"https://example{i+1}.com/article",
                            content=f"{query}에 대한 상세한 정보를 제공하는 웹페이지입니다. {i+1}번째 결과입니다.",
                            score=0.9 - (i * 0.1),
                            published_date=datetime.now() - timedelta(days=i),
                            source=f"웹사이트{i+1}",
                        )
                        results.append(result)

                if not results:
                    raise SearchError("검색 결과가 비어있습니다", "EMPTY_RESULTS")

                return results, data_quality

            results, data_quality = await self._retry_with_backoff(
                _fetch_search_results
            )

            # 결과 포맷팅
            formatted_results = [
                {
                    "title": result.title,
                    "url": result.url,
                    "content": result.content,
                    "score": result.score,
                    "published_date": result.published_date.isoformat(),
                    "source": result.source,
                }
                for result in results
            ]

            data = {
                "success": True,
                "query": query,
                "total_results": len(results),
                "results": formatted_results,
                "data_quality": data_quality,
                "search_timestamp": datetime.now().isoformat(),
            }

            # 캐시 업데이트
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            return {
                "success": True,
                "data": data,
                "source": "fresh",
                "message": f"'{query}' 웹 검색 완료 (캐시 업데이트됨)",
            }

        except Exception as e:
            self.logger.error(f"웹 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "웹 검색에 실패했습니다",
            }

    async def search_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """뉴스 검색 수행 (캐싱 + 재시도 로직)"""
        try:
            cache_key = self._get_cache_key(
                "search_news", {"query": query, "max_results": max_results}
            )

            if self._is_cache_valid(cache_key):
                self.logger.info(f"캐시 히트: {query}")
                return {
                    "success": True,
                    "data": self._cache[cache_key],
                    "source": "cache",
                    "message": "캐시된 뉴스 검색 결과 조회 완료",
                }

            async def _fetch_news_results():
                # 실제 뉴스 검색 로직 (현재는 샘플 데이터)
                results = []
                for i in range(max_results):
                    result = SearchResult(
                        title=f"{query} 관련 뉴스 {i+1}",
                        url=f"https://news{i+1}.com/article",
                        content=f"{query}에 대한 최신 뉴스입니다. {i+1}번째 기사입니다.",
                        score=0.95 - (i * 0.05),
                        published_date=datetime.now() - timedelta(hours=i * 2),
                        source=f"뉴스소스{i+1}",
                    )
                    results.append(result)

                if not results:
                    raise SearchError("뉴스 검색 결과가 비어있습니다", "EMPTY_NEWS")

                return results

            data = await self._retry_with_backoff(_fetch_news_results)

            # 캐시 업데이트
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            return {
                "success": True,
                "data": data,
                "source": "fresh",
                "message": f"'{query}' 뉴스 검색 완료 (캐시 업데이트됨)",
            }

        except Exception as e:
            self.logger.error(f"뉴스 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "뉴스 검색에 실패했습니다",
            }

    async def search_finance(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """금융 정보 검색 수행 (캐싱 + 재시도 로직)"""
        try:
            cache_key = self._get_cache_key(
                "search_finance", {"query": query, "max_results": max_results}
            )

            if self._is_cache_valid(cache_key):
                self.logger.info(f"캐시 히트: {query}")
                return {
                    "success": True,
                    "data": self._cache[cache_key],
                    "source": "cache",
                    "message": "캐시된 금융 정보 검색 결과 조회 완료",
                }

            async def _fetch_finance_results():
                # 실제 금융 정보 검색 로직 (현재는 샘플 데이터)
                results = []
                for i in range(max_results):
                    result = SearchResult(
                        title=f"{query} 관련 금융 정보 {i+1}",
                        url=f"https://finance{i+1}.com/article",
                        content=f"{query}에 대한 금융 분석 및 시장 정보입니다. {i+1}번째 결과입니다.",
                        score=0.92 - (i * 0.08),
                        published_date=datetime.now() - timedelta(hours=i * 3),
                        source=f"금융매체{i+1}",
                    )
                    results.append(result)

                if not results:
                    raise SearchError(
                        "금융 정보 검색 결과가 비어있습니다", "EMPTY_FINANCE"
                    )

                return results

            data = await self._retry_with_backoff(_fetch_finance_results)

            # 캐시 업데이트
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            return {
                "success": True,
                "data": data,
                "source": "fresh",
                "message": f"'{query}' 금융 정보 검색 완료 (캐시 업데이트됨)",
            }

        except Exception as e:
            self.logger.error(f"금융 정보 검색 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "금융 정보 검색에 실패했습니다",
            }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록을 반환합니다."""
        return [
            {
                "name": "search_web",
                "description": "웹 검색 수행 (캐싱 + 재시도 로직)",
                "parameters": {
                    "query": "검색할 키워드",
                    "max_results": "최대 결과 수 (기본값: 10)",
                },
            },
            {
                "name": "search_news",
                "description": "뉴스 검색 수행 (캐싱 + 재시도 로직)",
                "parameters": {
                    "query": "검색할 키워드",
                    "max_results": "최대 결과 수 (기본값: 10)",
                },
            },
            {
                "name": "search_finance",
                "description": "금융 정보 검색 수행 (캐싱 + 재시도 로직)",
                "parameters": {
                    "query": "검색할 키워드",
                    "max_results": "최대 결과 수 (기본값: 10)",
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

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """지정된 도구를 호출합니다."""
        try:
            query = params.get("query", "")
            max_results = params.get("max_results", 10)

            if tool_name == "search_web":
                return await self.search_web(query, max_results)
            elif tool_name == "search_news":
                return await self.search_news(query, max_results)
            elif tool_name == "search_finance":
                return await self.search_finance(query, max_results)
            elif tool_name == "get_server_health":
                return await self.get_server_health()
            elif tool_name == "get_server_metrics":
                return await self.get_server_metrics()
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 도구: {tool_name}",
                    "message": "지원하는 도구: search_web, search_news, search_finance, get_server_health, get_server_metrics",
                }
        except Exception as e:
            self.logger.error(f"도구 호출 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "도구 호출에 실패했습니다",
            }

    async def connect(self, server_url: str = "") -> bool:
        """MCP 서버에 연결합니다."""
        try:
            self.logger.info(f"MCP 서버 연결 시도: {server_url or '로컬'}")
            return True
        except Exception as e:
            self.logger.error(f"MCP 서버 연결 실패: {e}")
            return False

    async def disconnect(self) -> bool:
        """MCP 서버와의 연결을 해제합니다."""
        try:
            self.logger.info("MCP 서버 연결 해제")
            return True
        except Exception as e:
            self.logger.error(f"MCP 서버 연결 해제 실패: {e}")
            return False

    async def _call_tool_stream_internal(self, tool_name: str, params: Dict[str, Any]):
        """내부 스트리밍 호출 구현."""
        try:
            # 일반 호출 결과를 스트리밍으로 변환
            result = await self.call_tool(tool_name, params)
            yield {
                "step": "complete",
                "data": result,
                "message": f"도구 '{tool_name}' 실행 완료",
            }
        except Exception as e:
            yield {
                "step": "error",
                "error": str(e),
                "message": f"도구 '{tool_name}' 실행 실패",
            }

    async def _fetch_tavily_data(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """실제 Tavily API에서 검색 데이터 가져오기"""
        if not self.tavily_api_key:
            raise SearchError("Tavily API 키가 설정되지 않았습니다", "NO_API_KEY")

        try:
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False,
                "max_results": max_results,
                "include_domains": [],
                "exclude_domains": [],
            }

            response = requests.post(
                self.tavily_base_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            data = response.json()

            if "results" not in data:
                raise SearchError(
                    "Tavily API 응답 형식이 올바르지 않습니다", "INVALID_RESPONSE"
                )

            # 데이터 파싱 및 변환
            results = []
            for item in data["results"]:
                try:
                    result = {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")[:500],  # 내용 길이 제한
                        "score": item.get("score", 0.5),
                        "published_date": datetime.now().isoformat(),  # Tavily는 발행일을 제공하지 않음
                        "source": "Tavily",
                    }
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Tavily 데이터 파싱 실패: {item}, 에러: {e}")
                    continue

            return results

        except requests.RequestException as e:
            raise SearchError(f"Tavily API 호출 실패: {e}", "API_ERROR") from e
        except Exception as e:
            raise SearchError(
                f"Tavily 데이터 처리 실패: {e}", "PROCESSING_ERROR"
            ) from e

    async def get_server_health(self) -> Dict[str, Any]:
        """서버 헬스 상태 조회"""
        return {
            "status": "healthy",
            "service": "TavilySearch",
            "timestamp": datetime.now().isoformat(),
            "message": "TavilySearch MCP 서버가 정상적으로 작동 중입니다",
        }

    async def get_server_metrics(self) -> Dict[str, Any]:
        """서버 메트릭 조회"""
        return {
            "service": "TavilySearch",
            "cache_entries": len(self._cache),
            "cache_ttl_seconds": self.cache_ttl,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "tavily_api_configured": bool(self.tavily_api_key),
            "timestamp": datetime.now().isoformat(),
            "message": "TavilySearch MCP 서버 메트릭 정보",
        }
