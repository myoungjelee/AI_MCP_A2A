#!/usr/bin/env python3
"""
DataCollector Agent - A2A 프로토콜 기반 데이터 수집 에이전트

멀티소스 데이터 수집 및 통합을 담당합니다.
MCP 서버들과 연동하여 시장 데이터, 뉴스, 검색 결과를 수집하고 품질을 검증합니다.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from src.base import BaseAgent


class DataCollectorAgent(BaseAgent):
    """데이터 수집 A2A 에이전트입니다."""

    def __init__(self, name: str = "data_collector_agent"):
        super().__init__(name=name)
        self.logger = logging.getLogger(f"data_collector.{name}")
        self._setup_logging()

        # MCP 서버 연결 상태
        self.mcp_connections = {}

        # 데이터 품질 메트릭
        self.data_quality_scores = {}

        self.logger.info(f"DataCollector Agent '{name}' 초기화 완료")

    def _setup_logging(self):
        """로깅을 설정합니다."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        시장 데이터를 수집합니다.

        Args:
            symbol: 주식 심볼 (예: "005930")

        Returns:
            수집된 시장 데이터
        """
        try:
            self.logger.info(f"시장 데이터 수집 시작: {symbol}")

            # Mock 시장 데이터 수집 (실제로는 MCP 서버 호출)
            market_data = {
                "symbol": symbol,
                "name": "삼성전자" if symbol == "005930" else f"종목{symbol}",
                "current_price": 75000,
                "change": 1500,
                "change_pct": 2.04,
                "volume": 15000000,
                "market_cap": 45000000000000,
                "timestamp": datetime.now().isoformat(),
                "source": "mock_market_data",
            }

            self.logger.info(f"시장 데이터 수집 완료: {symbol}")
            return {
                "success": True,
                "data": market_data,
                "message": f"시장 데이터 수집 완료: {symbol}",
            }

        except Exception as e:
            self.logger.error(f"시장 데이터 수집 실패: {symbol}, 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"시장 데이터 수집 실패: {symbol}",
            }

    async def collect_news_data(
        self, query: str, max_results: int = 10
    ) -> Dict[str, Any]:
        """
        뉴스 데이터를 수집합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수

        Returns:
            수집된 뉴스 데이터
        """
        try:
            self.logger.info(f"뉴스 데이터 수집 시작: {query}")

            # Mock 뉴스 데이터 수집
            news_data = {
                "query": query,
                "total_results": max_results,
                "items": [
                    {
                        "title": f"{query} 관련 뉴스 제목 {i+1}",
                        "summary": f"{query}에 대한 뉴스 요약 내용 {i+1}입니다.",
                        "source": "Mock News",
                        "published_at": datetime.now().isoformat(),
                        "sentiment": "positive" if i % 2 == 0 else "neutral",
                    }
                    for i in range(max_results)
                ],
                "timestamp": datetime.now().isoformat(),
                "source": "mock_news_data",
            }

            self.logger.info(f"뉴스 데이터 수집 완료: {query}")
            return {
                "success": True,
                "data": news_data,
                "message": f"뉴스 데이터 수집 완료: {query}",
            }

        except Exception as e:
            self.logger.error(f"뉴스 데이터 수집 실패: {query}, 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"뉴스 데이터 수집 실패: {query}",
            }

    async def collect_search_data(
        self, query: str, max_results: int = 5
    ) -> Dict[str, Any]:
        """
        웹 검색 데이터를 수집합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수

        Returns:
            수집된 검색 데이터
        """
        try:
            self.logger.info(f"검색 데이터 수집 시작: {query}")

            # Mock 검색 데이터 수집
            search_data = {
                "query": query,
                "total_results": max_results,
                "results": [
                    {
                        "title": f"{query} 관련 검색 결과 {i+1}",
                        "url": f"https://example.com/result{i+1}",
                        "snippet": f"{query}에 대한 검색 결과 스니펫 {i+1}입니다.",
                        "source": "Mock Search",
                        "relevance_score": 0.9 - (i * 0.1),
                    }
                    for i in range(max_results)
                ],
                "timestamp": datetime.now().isoformat(),
                "source": "mock_search_data",
            }

            self.logger.info(f"검색 데이터 수집 완료: {query}")
            return {
                "success": True,
                "data": search_data,
                "message": f"검색 데이터 수집 완료: {query}",
            }

        except Exception as e:
            self.logger.error(f"검색 데이터 수집 실패: {query}, 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"검색 데이터 수집 실패: {query}",
            }

    async def collect_comprehensive_data(
        self, symbol: str, query: str = None
    ) -> Dict[str, Any]:
        """
        종합 데이터를 수집합니다.

        Args:
            symbol: 주식 심볼
            query: 추가 검색 쿼리 (기본값: symbol 기반)

        Returns:
            통합된 데이터
        """
        try:
            self.logger.info(f"종합 데이터 수집 시작: {symbol}")

            if query is None:
                query = f"{symbol} 주식"

            # 병렬로 데이터 수집
            tasks = [
                self.collect_market_data(symbol),
                self.collect_news_data(query),
                self.collect_search_data(query),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 통합
            comprehensive_data = {
                "symbol": symbol,
                "query": query,
                "collection_timestamp": datetime.now().isoformat(),
                "data_sources": {
                    "market_data": (
                        results[0]
                        if not isinstance(results[0], Exception)
                        else {"success": False, "error": str(results[0])}
                    ),
                    "news_data": (
                        results[1]
                        if not isinstance(results[1], Exception)
                        else {"success": False, "error": str(results[1])}
                    ),
                    "search_data": (
                        results[2]
                        if not isinstance(results[2], Exception)
                        else {"success": False, "error": str(results[2])}
                    ),
                },
                "quality_score": self._calculate_quality_score(results),
            }

            self.logger.info(f"종합 데이터 수집 완료: {symbol}")
            return {
                "success": True,
                "data": comprehensive_data,
                "message": f"종합 데이터 수집 완료: {symbol}",
            }

        except Exception as e:
            self.logger.error(f"종합 데이터 수집 실패: {symbol}, 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"종합 데이터 수집 실패: {symbol}",
            }

    def _calculate_quality_score(self, results: List[Any]) -> float:
        """
        데이터 품질 점수를 계산합니다.

        Args:
            results: 수집 결과 리스트

        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        try:
            success_count = sum(
                1
                for result in results
                if isinstance(result, dict) and result.get("success", False)
            )
            total_count = len(results)

            if total_count == 0:
                return 0.0

            quality_score = success_count / total_count
            self.logger.info(
                f"데이터 품질 점수: {quality_score:.2f} ({success_count}/{total_count})"
            )

            return quality_score

        except Exception as e:
            self.logger.error(f"품질 점수 계산 실패: {e}")
            return 0.0

    async def get_agent_status(self) -> Dict[str, Any]:
        """
        에이전트 상태를 반환합니다.

        Returns:
            에이전트 상태 정보
        """
        return {
            "agent_type": "data_collector",
            "status": "active",
            "name": self.name,
            "capabilities": [
                "market_data_collection",
                "news_data_collection",
                "search_data_collection",
                "comprehensive_data_integration",
                "data_quality_assessment",
            ],
            "mcp_connections": list(self.mcp_connections.keys()),
            "last_activity": datetime.now().isoformat(),
        }

    async def process_a2a_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        A2A 프로토콜 요청을 처리합니다.

        Args:
            request: A2A 요청 데이터

        Returns:
            A2A 응답 데이터
        """
        try:
            self.logger.info(f"A2A 요청 처리 시작: {request.get('type', 'unknown')}")

            request_type = request.get("type", "")

            if request_type == "collect_market_data":
                symbol = request.get("symbol", "005930")
                result = await self.collect_market_data(symbol)

            elif request_type == "collect_news_data":
                query = request.get("query", "주식 시장")
                max_results = request.get("max_results", 10)
                result = await self.collect_news_data(query, max_results)

            elif request_type == "collect_search_data":
                query = request.get("query", "주식 시장")
                max_results = request.get("max_results", 5)
                result = await self.collect_search_data(query, max_results)

            elif request_type == "collect_comprehensive_data":
                symbol = request.get("symbol", "005930")
                query = request.get("query")
                result = await self.collect_comprehensive_data(symbol, query)

            elif request_type == "get_status":
                result = await self.get_agent_status()

            else:
                result = {
                    "success": False,
                    "error": f"지원하지 않는 요청 타입: {request_type}",
                    "message": "지원하는 요청 타입을 확인해주세요.",
                }

            # A2A 응답 형식으로 변환
            a2a_response = {
                "agent_type": "data_collector",
                "status": "completed" if result.get("success", False) else "failed",
                "request_id": request.get("request_id", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }

            self.logger.info(f"A2A 요청 처리 완료: {request_type}")
            return a2a_response

        except Exception as e:
            self.logger.error(f"A2A 요청 처리 실패: {e}")
            return {
                "agent_type": "data_collector",
                "status": "failed",
                "request_id": request.get("request_id", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "message": "A2A 요청 처리 중 오류가 발생했습니다.",
            }
