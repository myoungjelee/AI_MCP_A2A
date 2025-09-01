"""
데이터 처리 시스템 MCP 클라이언트 - 개발 기술 중심

실제 데이터를 사용하여 데이터 수집, 배치 처리, 트렌드 분석 기능을 제공합니다.
개발 기술: 비동기 처리, 캐싱, 재시도 로직, 선형 회귀 알고리즘
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

from ..base.base_mcp_client import BaseMCPClient
from ..base.middleware import MiddlewareManager

logger = logging.getLogger(__name__)


@dataclass
class DataRecord:
    """데이터 레코드 구조"""

    id: str
    timestamp: datetime
    value: float
    category: str
    source: str
    metadata: Dict[str, Any]


class DataProcessingError(Exception):
    """데이터 처리 에러"""

    def __init__(
        self, message: str, error_code: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class MacroeconomicClient(BaseMCPClient):
    """거시경제 데이터 처리 시스템 클라이언트"""

    def __init__(self, name: str = "macroeconomic"):
        super().__init__(name)

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager("macroeconomic")

        # 캐시 설정
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 300  # 5분

        # 처리 설정
        self.max_batch_size = 1000
        self.default_timeout = 30.0
        self.max_retries = 3

        # API 키 설정
        self.ecos_api_key = os.getenv("ECOS_API_KEY")
        self.fred_api_key = os.getenv("FRED_API_KEY")

        # API 엔드포인트
        self.ecos_base_url = "https://ecos.bok.or.kr/api"
        self.fred_base_url = "https://api.stlouisfed.org/fred/series/observations"

        # 기본 데이터 카테고리 (실제 경제 지표)
        self.default_categories = [
            "GDP",  # 국내총생산
            "CPI",  # 소비자물가지수
            "INTEREST_RATE",  # 금리
            "EXCHANGE_RATE",  # 환율
            "UNEMPLOYMENT",  # 실업률
            "INFLATION",  # 인플레이션
            "TRADE_BALANCE",  # 무역수지
            "FOREIGN_RESERVE",  # 외환보유액
        ]

        logger.info(f"MacroeconomicClient initialized: {name}")
        logger.info(
            f"ECOS API Key: {'설정됨' if self.ecos_api_key else '설정되지 않음'}"
        )
        logger.info(
            f"FRED API Key: {'설정됨' if self.fred_api_key else '설정되지 않음'}"
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

        elapsed = time.time() - self._cache_timestamps[cache_key]
        return elapsed < self._cache_ttl

    async def collect_data(
        self, category: str, params: Dict[str, Any] = None, source: str = "auto"
    ) -> Dict[str, Any]:
        """데이터 수집 - 실제 API 사용"""
        try:
            # params가 None이면 기본값 설정
            if params is None:
                params = {}

            max_records = params.get("max_records", 100)
            start_date = params.get("start_date", "2023-01-01")
            end_date = params.get("end_date", datetime.now().strftime("%Y-%m-%d"))

            cache_key = self._get_cache_key(
                "collect_data",
                {"category": category, "params": params, "source": source},
            )

            # 캐시 확인
            if self._is_cache_valid(cache_key):
                logger.info(f"Cache hit: {cache_key}")
                return self._cache[cache_key]

            # 실제 데이터 수집
            records = []

            if source == "auto" or source == "ecos":
                # ECOS 데이터 시도
                try:
                    if category in ["GDP", "CPI", "INTEREST_RATE", "EXCHANGE_RATE"]:
                        ecos_records = await self._fetch_ecos_data(
                            category, start_date, end_date
                        )
                        records.extend(ecos_records)
                        logger.info(f"ECOS에서 {len(ecos_records)}개 데이터 수집 완료")
                except Exception as e:
                    logger.warning(f"ECOS 데이터 수집 실패: {e}")

            if source == "auto" or source == "fred":
                # FRED 데이터 시도
                try:
                    if category in ["UNEMPLOYMENT", "INFLATION", "TRADE_BALANCE"]:
                        # FRED 시리즈 ID 매핑
                        fred_mapping = {
                            "UNEMPLOYMENT": "UNRATE",  # 실업률
                            "INFLATION": "CPIAUCSL",  # CPI
                            "TRADE_BALANCE": "BOPGSTB",  # 무역수지
                        }

                        if category in fred_mapping:
                            fred_records = await self._fetch_fred_data(
                                fred_mapping[category], start_date, end_date
                            )
                            records.extend(fred_records)
                            logger.info(
                                f"FRED에서 {len(fred_records)}개 데이터 수집 완료"
                            )
                except Exception as e:
                    logger.warning(f"FRED 데이터 수집 실패: {e}")

            # 데이터가 없으면 더미 데이터 생성 (폴백)
            if not records:
                logger.warning("실제 API 데이터 수집 실패, 더미 데이터 생성")
                records = await self._generate_dummy_data(category, max_records, source)

            # 최대 개수 제한
            records = records[:max_records]

            result = {
                "success": True,
                "total_collected": len(records),
                "category": category,
                "source": source,
                "records": [
                    {
                        "id": record["id"],
                        "timestamp": record["timestamp"].isoformat(),
                        "value": record["value"],
                        "category": record["category"],
                        "source": record["source"],
                        "metadata": record["metadata"],
                    }
                    for record in records
                ],
                "collection_timestamp": datetime.now().isoformat(),
                "data_quality": (
                    "real"
                    if records and records[0].get("source") in ["ECOS", "FRED"]
                    else "dummy"
                ),
            }

            # 캐시 업데이트
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = time.time()

            logger.info(
                f"Data collected successfully: {category} -> {len(records)} records (quality: {result['data_quality']})"
            )
            return result

        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            raise DataProcessingError(
                f"데이터 수집 실패: {e}", "COLLECTION_ERROR"
            ) from e

    async def _fetch_ecos_data(
        self, indicator: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """ECOS API에서 경제 데이터 가져오기"""
        if not self.ecos_api_key:
            raise DataProcessingError("ECOS API 키가 설정되지 않았습니다", "NO_API_KEY")

        try:
            # 지표 코드 매핑
            indicator_mapping = {
                "GDP": "200Y001",  # 국내총생산
                "CPI": "901Y009",  # 소비자물가지수
                "INTEREST_RATE": "721Y001",  # 기준금리
                "EXCHANGE_RATE": "036Y001",  # 원/달러 환율
                "KOSPI": "901Y013",  # KOSPI 지수
                "UNEMPLOYMENT": "901Y014",  # 실업률
            }

            # 실제 지표 코드 가져오기
            actual_indicator = indicator_mapping.get(indicator, indicator)

            # 날짜 형식 결정 (연도만 있으면 연간, 월이 있으면 월간)
            if len(start_date) == 4:  # YYYY 형식
                cycle = "A"  # 연간
            else:  # YYYYMM 형식
                cycle = "M"  # 월간

            # ECOS API 호출
            url = f"{self.ecos_base_url}/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/{actual_indicator}/{cycle}/{start_date}/{end_date}"

            response = requests.get(url, timeout=self.default_timeout)
            response.raise_for_status()

            data = response.json()

            if "StatisticSearch" not in data:
                raise DataProcessingError(
                    "ECOS API 응답 형식이 올바르지 않습니다", "INVALID_RESPONSE"
                )

            # 데이터 파싱 및 변환
            records = []
            for item in data["StatisticSearch"]["row"]:
                try:
                    # 시간 형식 파싱
                    time_str = item.get("TIME", "")
                    if len(time_str) == 4:  # YYYY
                        timestamp = datetime.strptime(time_str, "%Y")
                    elif len(time_str) == 6:  # YYYYMM
                        timestamp = datetime.strptime(time_str, "%Y%m")
                    else:
                        continue

                    value = float(item.get("DATA_VALUE", 0))

                    record = {
                        "id": f"{indicator}_{item.get('TIME', '')}",
                        "timestamp": timestamp,
                        "value": value,
                        "category": indicator,
                        "source": "ECOS",
                        "metadata": {
                            "unit": item.get("UNIT_NAME", ""),
                            "frequency": "연간" if cycle == "A" else "월간",
                            "data_type": "official",
                            "stat_name": item.get("STAT_NAME", ""),
                            "item_name": item.get("ITEM_NAME1", ""),
                        },
                    }
                    records.append(record)
                except (ValueError, TypeError) as e:
                    logger.warning(f"데이터 파싱 실패: {item}, 에러: {e}")
                    continue

            return records

        except requests.RequestException as e:
            raise DataProcessingError(f"ECOS API 호출 실패: {e}", "API_ERROR") from e
        except Exception as e:
            raise DataProcessingError(
                f"ECOS 데이터 처리 실패: {e}", "PROCESSING_ERROR"
            ) from e

    async def _fetch_fred_data(
        self, series_id: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """FRED API에서 경제 데이터 가져오기"""
        if not self.fred_api_key:
            raise DataProcessingError("FRED API 키가 설정되지 않았습니다", "NO_API_KEY")

        try:
            # FRED API 호출
            params = {
                "series_id": series_id,
                "api_key": self.fred_api_key,
                "file_type": "json",
                "observation_start": start_date,
                "observation_end": end_date,
            }

            response = requests.get(
                self.fred_base_url, params=params, timeout=self.default_timeout
            )
            response.raise_for_status()

            data = response.json()

            if "observations" not in data:
                raise DataProcessingError(
                    "FRED API 응답 형식이 올바르지 않습니다", "INVALID_RESPONSE"
                )

            # 데이터 파싱 및 변환
            records = []
            for item in data["observations"]:
                try:
                    timestamp = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                    value = float(item.get("value", 0))

                    record = {
                        "id": f"{series_id}_{item.get('date', '')}",
                        "timestamp": timestamp,
                        "value": value,
                        "category": series_id,
                        "source": "FRED",
                        "metadata": {
                            "unit": "원본 단위",
                            "frequency": "일별",
                            "data_type": "official",
                        },
                    }
                    records.append(record)
                except (ValueError, TypeError) as e:
                    logger.warning(f"데이터 파싱 실패: {item}, 에러: {e}")
                    continue

            return records

        except requests.RequestException as e:
            raise DataProcessingError(f"FRED API 호출 실패: {e}", "API_ERROR") from e
        except Exception as e:
            raise DataProcessingError(
                f"FRED 데이터 처리 실패: {e}", "PROCESSING_ERROR"
            ) from e

    async def _generate_dummy_data(
        self, category: str, max_records: int, source: str
    ) -> List[Dict[str, Any]]:
        """더미 데이터 생성 (폴백용)"""
        records = []
        for i in range(min(max_records, 50)):
            record = {
                "id": f"{category}_{i+1}",
                "timestamp": datetime.now() - timedelta(hours=i),
                "value": 100.0 + (i * 0.5) + (hash(category) % 10),
                "category": category,
                "source": source,
                "metadata": {
                    "quality_score": 0.9 - (i * 0.01),
                    "confidence": 0.95 - (i * 0.005),
                    "version": "1.0",
                    "data_type": "dummy",
                },
            }
            records.append(record)
        return records

    async def process_data_batch(
        self, data_records: List[Dict[str, Any]], operation: str = "validate"
    ) -> Dict[str, Any]:
        """배치 데이터 처리"""
        try:
            if not data_records:
                return {"success": False, "error": "처리할 데이터가 없습니다"}

            # 배치 크기 최적화
            batch_size = min(100, len(data_records))
            processed_count = 0
            errors = []
            results = []

            start_time = time.time()

            # 배치 단위로 처리
            for i in range(0, len(data_records), batch_size):
                batch = data_records[i : i + batch_size]

                try:
                    if operation == "validate":
                        # 데이터 검증
                        batch_results = await self._validate_batch(batch)
                    elif operation == "transform":
                        # 데이터 변환
                        batch_results = await self._transform_batch(batch)
                    elif operation == "aggregate":
                        # 데이터 집계
                        batch_results = await self._aggregate_batch(batch)
                    else:
                        raise DataProcessingError(
                            f"지원하지 않는 작업: {operation}", "UNSUPPORTED_OPERATION"
                        )

                    results.extend(batch_results)
                    processed_count += len(batch)

                except Exception as batch_error:
                    errors.append(f"배치 {i//batch_size + 1}: {str(batch_error)}")
                    continue

            processing_time = time.time() - start_time

            result = {
                "success": len(errors) == 0,
                "operation": operation,
                "total_records": len(data_records),
                "processed_count": processed_count,
                "batch_size": batch_size,
                "processing_time": round(processing_time, 3),
                "results": results,
                "errors": errors,
                "processing_timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Batch processing completed: {operation} -> {processed_count}/{len(data_records)} records"
            )
            return result

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise DataProcessingError(f"배치 처리 실패: {e}", "PROCESSING_ERROR") from e

    async def analyze_data_trends(
        self, data_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """데이터 트렌드 분석 (선형 회귀 알고리즘)"""
        try:
            if not data_records:
                return {"success": False, "error": "분석할 데이터가 없습니다"}

            # 시간순 정렬
            sorted_records = sorted(data_records, key=lambda x: x.get("timestamp", ""))

            # 수치 데이터 추출
            values = []
            timestamps = []

            for record in sorted_records:
                try:
                    value = float(record.get("value", 0))
                    timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                    values.append(value)
                    timestamps.append(timestamp)
                except (ValueError, TypeError):
                    continue

            if len(values) < 2:
                return {
                    "success": False,
                    "error": "트렌드 분석을 위한 충분한 데이터가 없습니다",
                }

            # 선형 회귀를 사용한 트렌드 분석
            trend_analysis = self._calculate_linear_regression(values, timestamps)

            # 통계 계산
            statistics = self._calculate_statistics(values)

            result = {
                "success": True,
                "trend_analysis": trend_analysis,
                "statistics": statistics,
                "data_summary": {
                    "total_records": len(data_records),
                    "valid_records": len(values),
                    "time_range": {
                        "start": timestamps[0].isoformat(),
                        "end": timestamps[-1].isoformat(),
                    },
                },
                "analysis_timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Trend analysis completed: {len(values)} data points analyzed")
            return result

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            raise DataProcessingError(f"트렌드 분석 실패: {e}", "ANALYSIS_ERROR") from e

    def _calculate_linear_regression(
        self, values: List[float], timestamps: List[datetime]
    ) -> Dict[str, Any]:
        """선형 회귀 계산"""
        n = len(values)
        x = list(range(n))
        y = values

        # 평균 계산
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # 기울기와 절편 계산
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator != 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean

            # 트렌드 방향 결정
            if slope > 0.01:
                trend_direction = "상승"
                trend_strength = "강함" if abs(slope) > 0.1 else "약함"
            elif slope < -0.01:
                trend_direction = "하락"
                trend_strength = "강함" if abs(slope) > 0.1 else "약함"
            else:
                trend_direction = "안정"
                trend_strength = "약함"

            # 예측값 계산
            next_x = n
            predicted_value = slope * next_x + intercept

            return {
                "slope": round(slope, 4),
                "intercept": round(intercept, 4),
                "trend_direction": trend_direction,
                "trend_strength": trend_strength,
                "r_squared": self._calculate_r_squared(x, y, slope, intercept),
                "predicted_next_value": round(predicted_value, 2),
                "confidence": "높음" if abs(slope) > 0.05 else "보통",
            }
        else:
            return {
                "slope": 0,
                "intercept": y_mean,
                "trend_direction": "안정",
                "trend_strength": "약함",
                "r_squared": 0,
                "predicted_next_value": y_mean,
                "confidence": "낮음",
            }

    def _calculate_r_squared(
        self, x: List[int], y: List[float], slope: float, intercept: float
    ) -> float:
        """R-squared (결정계수) 계산"""
        y_pred = [slope * xi + intercept for xi in x]
        y_mean = sum(y) / len(y)

        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(len(y)))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(len(y)))

        if ss_tot != 0:
            return round(1 - (ss_res / ss_tot), 4)
        return 0

    def _calculate_statistics(self, values: List[float]) -> Dict[str, Any]:
        """기본 통계 계산"""
        if not values:
            return {}

        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = variance**0.5

        return {
            "count": n,
            "mean": round(mean, 4),
            "median": round(sorted(values)[n // 2], 4),
            "std_deviation": round(std_dev, 4),
            "variance": round(variance, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "range": round(max(values) - min(values), 4),
        }

    async def _validate_batch(
        self, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """배치 데이터 검증"""
        validated_records = []

        for record in batch:
            try:
                # 기본 검증
                if not record.get("id"):
                    continue

                value = record.get("value")
                if value is None or not isinstance(value, (int, float)):
                    continue

                # 검증 통과
                validated_records.append(
                    {**record, "validation_status": "passed", "validation_score": 1.0}
                )

            except Exception:
                continue

        return validated_records

    async def _transform_batch(
        self, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """배치 데이터 변환"""
        transformed_records = []

        for record in batch:
            try:
                # 기본 변환
                value = record.get("value", 0)
                transformed_value = value * 1.1  # 10% 증가

                transformed_records.append(
                    {
                        **record,
                        "original_value": value,
                        "transformed_value": round(transformed_value, 4),
                        "transformation_factor": 1.1,
                    }
                )

            except Exception:
                continue

        return transformed_records

    async def _aggregate_batch(
        self, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """배치 데이터 집계"""
        if not batch:
            return []

        try:
            values = [
                record.get("value", 0)
                for record in batch
                if isinstance(record.get("value"), (int, float))
            ]

            if not values:
                return []

            # 집계 통계
            total = sum(values)
            count = len(values)
            average = total / count
            min_val = min(values)
            max_val = max(values)

            return [
                {
                    "aggregation_type": "batch_summary",
                    "batch_size": count,
                    "total": round(total, 4),
                    "average": round(average, 4),
                    "min": round(min_val, 4),
                    "max": round(max_val, 4),
                    "timestamp": datetime.now().isoformat(),
                }
            ]

        except Exception:
            return []

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록"""
        return [
            {
                "name": "collect_data",
                "description": "데이터 수집 - 카테고리별로 데이터를 수집합니다",
                "parameters": {
                    "category": "데이터 카테고리",
                    "max_records": "최대 수집 레코드 수",
                    "source": "데이터 소스 (auto, ecos, fred)",
                },
            },
            {
                "name": "process_data_batch",
                "description": "배치 데이터 처리 - 대용량 데이터를 효율적으로 처리합니다",
                "parameters": {
                    "data_records": "처리할 데이터 레코드 리스트",
                    "operation": "처리 작업 (validate/transform/aggregate)",
                },
            },
            {
                "name": "analyze_data_trends",
                "description": "데이터 트렌드 분석 - 선형 회귀를 사용한 트렌드 분석",
                "parameters": {"data_records": "분석할 데이터 레코드 리스트"},
            },
        ]

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """도구 호출"""
        try:
            if tool_name == "collect_data":
                return await self.collect_data(**kwargs)
            elif tool_name == "process_data_batch":
                return await self.process_data_batch(**kwargs)
            elif tool_name == "analyze_data_trends":
                return await self.analyze_data_trends(**kwargs)
            else:
                raise DataProcessingError(
                    f"지원하지 않는 도구: {tool_name}", "UNSUPPORTED_TOOL"
                )

        except Exception as e:
            logger.error(f"Tool call failed: {tool_name} - {e}")
            return {"success": False, "error": str(e), "tool_name": tool_name}

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
            result = await self.call_tool(tool_name, **params)
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
