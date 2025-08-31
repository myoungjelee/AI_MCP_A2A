"""
데이터 분석 시스템 MCP 클라이언트 - 개발 기술 중심
복잡한 주식 분석 대신 깔끔한 코드 구조와 효율적인 데이터 분석 알고리즘을 보여줍니다.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import FinanceDataReader as fdr
import numpy as np

from src.mcp_servers.base.base_mcp_client import BaseMCPClient
from src.mcp_servers.base.middleware import MiddlewareManager


@dataclass
class AnalysisResult:
    """분석 결과 구조"""

    symbol: str
    signal: str
    score: float
    confidence: float
    indicators: Dict[str, Any]
    timestamp: datetime


class DataAnalysisError(Exception):
    """데이터 분석 에러"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class StockAnalysisClient(BaseMCPClient):
    """주식 분석 시스템 MCP 클라이언트 (개발 기술 중심)"""

    def __init__(self, name: str = "stock_analyzer"):
        super().__init__(name=name)

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager("stock_analysis")

        self.logger = logging.getLogger(f"stock_analyzer.{name}")
        self._setup_logging()

        # 설정
        self.max_retries = 3
        self.retry_delay = 1.0
        self.cache_ttl = 300  # 5분

        # 간단한 메모리 캐시
        self._cache = {}
        self._cache_timestamps = {}

        self.logger.info(f"주식 분석 클라이언트 '{name}' 초기화 완료")

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @MiddlewareManager.apply_all("재시도 로직")
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

    async def analyze_data_trends(
        self, symbol: str, period: str = "1y"
    ) -> Dict[str, Any]:
        """데이터 트렌드 분석 수행 (캐싱 + 재시도 로직)"""
        try:
            cache_key = self._get_cache_key(
                "analyze_data_trends", {"symbol": symbol, "period": period}
            )

            if self._is_cache_valid(cache_key):
                self.logger.info(f"캐시 히트: {symbol}")
                return {
                    "success": True,
                    "data": self._cache[cache_key],
                    "source": "cache",
                    "message": "캐시된 트렌드 분석 결과 조회 완료",
                }

            async def _fetch_trend_analysis():
                # 실제 데이터 분석 로직
                end_date = datetime.now()
                if period == "1y":
                    start_date = end_date - timedelta(days=365)
                elif period == "6mo":
                    start_date = end_date - timedelta(days=180)
                else:
                    start_date = end_date - timedelta(days=365)

                # FinanceDataReader로 실제 데이터 조회
                df = fdr.DataReader(symbol, start_date, end_date)

                if df.empty:
                    raise DataAnalysisError(f"데이터가 비어있습니다: {symbol}")

                # 기술적 지표 계산
                close_prices = df["Close"].values

                # RSI 계산
                rsi = self._calculate_rsi(close_prices)

                # 이동평균 계산
                ma20 = (
                    np.mean(close_prices[-20:])
                    if len(close_prices) >= 20
                    else close_prices[-1]
                )
                ma60 = (
                    np.mean(close_prices[-60:])
                    if len(close_prices) >= 60
                    else close_prices[-1]
                )

                # 트렌드 신호 결정
                current_price = close_prices[-1]
                if current_price > ma20 > ma60:
                    signal = "상승"
                    score = 0.8
                elif current_price < ma20 < ma60:
                    signal = "하락"
                    score = 0.2
                else:
                    signal = "중립"
                    score = 0.5

                return {
                    "symbol": symbol,
                    "period": period,
                    "current_price": float(current_price),
                    "ma20": float(ma20),
                    "ma60": float(ma60),
                    "rsi": float(rsi),
                    "signal": signal,
                    "score": score,
                    "confidence": 0.7,
                    "data_points": len(close_prices),
                }

            data = await self._retry_with_backoff(_fetch_trend_analysis)

            # 캐시 업데이트
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            return {
                "success": True,
                "data": data,
                "source": "fresh",
                "message": f"'{symbol}' 트렌드 분석 완료 (캐시 업데이트됨)",
            }

        except Exception as e:
            self.logger.error(f"트렌드 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "트렌드 분석에 실패했습니다",
            }

    async def calculate_statistical_indicators(self, symbol: str) -> Dict[str, Any]:
        """통계적 지표 계산 수행 (캐싱 + 재시도 로직)"""
        try:
            cache_key = self._get_cache_key(
                "calculate_statistical_indicators", {"symbol": symbol}
            )

            if self._is_cache_valid(cache_key):
                self.logger.info(f"캐시 히트: {symbol}")
                return {
                    "success": True,
                    "data": self._cache[cache_key],
                    "source": "cache",
                    "message": "캐시된 통계 지표 조회 완료",
                }

            async def _fetch_statistical_analysis():
                # 실제 통계 분석 로직
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)

                df = fdr.DataReader(symbol, start_date, end_date)

                if df.empty:
                    raise DataAnalysisError(f"데이터가 비어있습니다: {symbol}")

                # 기본 통계 계산
                close_prices = df["Close"].values
                volumes = df["Volume"].values if "Volume" in df.columns else None

                # 가격 통계
                price_mean = np.mean(close_prices)
                price_std = np.std(close_prices)
                price_min = np.min(close_prices)
                price_max = np.max(close_prices)

                # 변동성 계산
                returns = np.diff(close_prices) / close_prices[:-1]
                volatility = np.std(returns) * np.sqrt(252)  # 연간 변동성

                # 거래량 통계
                volume_stats = {}
                if volumes is not None:
                    volume_stats = {
                        "avg_volume": float(np.mean(volumes)),
                        "max_volume": float(np.max(volumes)),
                        "volume_std": float(np.std(volumes)),
                    }

                return {
                    "symbol": symbol,
                    "price_statistics": {
                        "mean": float(price_mean),
                        "std": float(price_std),
                        "min": float(price_min),
                        "max": float(price_max),
                        "volatility": float(volatility),
                    },
                    "volume_statistics": volume_stats,
                    "data_points": len(close_prices),
                    "analysis_period": "90일",
                }

            data = await self._retry_with_backoff(_fetch_statistical_analysis)

            # 캐시 업데이트
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            return {
                "success": True,
                "data": data,
                "source": "fresh",
                "message": f"'{symbol}' 통계 지표 계산 완료 (캐시 업데이트됨)",
            }

        except Exception as e:
            self.logger.error(f"통계 지표 계산 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "통계 지표 계산에 실패했습니다",
            }

    async def perform_pattern_recognition(self, symbol: str) -> Dict[str, Any]:
        """패턴 인식 수행 (캐싱 + 재시도 로직)"""
        try:
            cache_key = self._get_cache_key(
                "perform_pattern_recognition", {"symbol": symbol}
            )

            if self._is_cache_valid(cache_key):
                self.logger.info(f"캐시 히트: {symbol}")
                return {
                    "success": True,
                    "data": self._cache[cache_key],
                    "source": "cache",
                    "message": "캐시된 패턴 인식 결과 조회 완료",
                }

            async def _fetch_pattern_analysis():
                # 실제 패턴 인식 로직
                end_date = datetime.now()
                start_date = end_date - timedelta(days=120)

                df = fdr.DataReader(symbol, start_date, end_date)

                if df.empty:
                    raise DataAnalysisError(f"데이터가 비어있습니다: {symbol}")

                close_prices = df["Close"].values

                # 간단한 패턴 인식
                patterns = []

                # 상승 추세 패턴
                if len(close_prices) >= 20:
                    recent_trend = close_prices[-20:]
                    if all(
                        recent_trend[i] <= recent_trend[i + 1]
                        for i in range(len(recent_trend) - 1)
                    ):
                        patterns.append(
                            {
                                "type": "상승 추세",
                                "confidence": 0.8,
                                "description": "20일간 지속적인 상승 패턴",
                            }
                        )

                # 하락 추세 패턴
                if len(close_prices) >= 20:
                    recent_trend = close_prices[-20:]
                    if all(
                        recent_trend[i] >= recent_trend[i + 1]
                        for i in range(len(recent_trend) - 1)
                    ):
                        patterns.append(
                            {
                                "type": "하락 추세",
                                "confidence": 0.8,
                                "description": "20일간 지속적인 하락 패턴",
                            }
                        )

                # 변동성 패턴
                if len(close_prices) >= 30:
                    recent_volatility = np.std(close_prices[-30:])
                    avg_volatility = np.std(close_prices)
                    if recent_volatility > avg_volatility * 1.5:
                        patterns.append(
                            {
                                "type": "높은 변동성",
                                "confidence": 0.7,
                                "description": "최근 30일간 변동성 증가",
                            }
                        )

                return {
                    "symbol": symbol,
                    "patterns": patterns,
                    "total_patterns": len(patterns),
                    "analysis_period": "120일",
                    "data_points": len(close_prices),
                }

            data = await self._retry_with_backoff(_fetch_pattern_analysis)

            # 캐시 업데이트
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()

            return {
                "success": True,
                "data": data,
                "source": "fresh",
                "message": f"'{symbol}' 패턴 인식 완료 (캐시 업데이트됨)",
            }

        except Exception as e:
            self.logger.error(f"패턴 인식 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "패턴 인식에 실패했습니다",
            }

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록을 반환합니다."""
        return [
            {
                "name": "analyze_data_trends",
                "description": "데이터 트렌드 분석 수행 (캐싱 + 재시도 로직)",
                "parameters": {
                    "symbol": "분석할 심볼",
                    "period": "분석 기간 (1y, 6mo)",
                },
            },
            {
                "name": "calculate_statistical_indicators",
                "description": "통계적 지표 계산 수행 (캐싱 + 재시도 로직)",
                "parameters": {"symbol": "분석할 심볼"},
            },
            {
                "name": "perform_pattern_recognition",
                "description": "패턴 인식 수행 (캐싱 + 재시도 로직)",
                "parameters": {"symbol": "분석할 심볼"},
            },
        ]

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """지정된 도구를 호출합니다."""
        try:
            symbol = params.get("symbol", "005930")  # 기본값: 삼성전자

            if tool_name == "analyze_data_trends":
                period = params.get("period", "1y")
                return await self.analyze_data_trends(symbol, period)
            elif tool_name == "calculate_statistical_indicators":
                return await self.calculate_statistical_indicators(symbol)
            elif tool_name == "perform_pattern_recognition":
                return await self.perform_pattern_recognition(symbol)
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 도구: {tool_name}",
                    "message": "지원하는 도구: analyze_data_trends, calculate_statistical_indicators, perform_pattern_recognition",
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
            # 실제 연결 로직은 필요에 따라 구현
            return True
        except Exception as e:
            self.logger.error(f"MCP 서버 연결 실패: {e}")
            return False

    async def disconnect(self) -> bool:
        """MCP 서버와의 연결을 해제합니다."""
        try:
            self.logger.info("MCP 서버 연결 해제")
            # 실제 연결 해제 로직은 필요에 따라 구현
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
