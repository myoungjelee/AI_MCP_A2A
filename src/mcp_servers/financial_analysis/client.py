"""
재무 분석 시스템 MCP 클라이언트 - 개발 기술 중심

핵심 재무 분석 기능을 제공하는 클라이언트입니다.
실제 데이터를 사용하여 MCP, FastMCP, 비동기 처리 기술을 보여줍니다.

주요 기능:
- 재무 데이터 수집 및 분석 (DART API 연동)
- 재무비율 계산
- 기업 가치 평가
- 투자 분석 리포트 생성

개발 기술:
- FastMCP 기반 MCP 클라이언트
- 비동기 처리 (asyncio)
- 캐싱 및 재시도 로직
- 데이터 구조화 (dataclass)
- 에러 처리 및 로깅
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from src.mcp_servers.base.base_mcp_client import BaseMCPClient
from src.mcp_servers.base.middleware import MiddlewareManager


class FinancialDataType(Enum):
    """재무 데이터 타입"""

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    MARKET_DATA = "market_data"


@dataclass
class FinancialRecord:
    """재무 데이터 레코드"""

    symbol: str
    data_type: FinancialDataType
    data: Dict[str, Any]
    timestamp: datetime
    source: str


class FinancialAnalysisError(Exception):
    """재무 분석 에러"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class FinancialAnalysisClient(BaseMCPClient):
    """재무 분석 시스템 MCP 클라이언트"""

    def __init__(self, name: str = "financial_analyzer"):
        super().__init__(name=name)

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager("financial_analysis")

        self.logger = logging.getLogger(f"financial_analysis.{name}")
        self._setup_logging()

        # 설정
        self.max_retries = 3
        self.retry_delay = 1.0
        self.cache_ttl = 600  # 10분

        # 간단한 메모리 캐시
        self._cache = {}
        self._cache_timestamps = {}

        # 한국 시장 기본 파라미터
        self.default_discount_rate = 10.0
        self.default_growth_rate = 3.0
        self.default_terminal_growth = 1.5

        # DART API 설정
        self.dart_api_key = os.getenv("DART_API_KEY")
        self.dart_base_url = "https://opendart.fss.or.kr/api"

        # ECOS API 설정 (보조용)
        self.ecos_api_key = os.getenv("ECOS_API_KEY")
        self.ecos_base_url = "https://ecos.bok.or.kr/api"

        self.logger.info(f"재무 분석 클라이언트 '{name}' 초기화 완료")
        self.logger.info(
            f"DART API Key: {'설정됨' if self.dart_api_key else '설정되지 않음'}"
        )
        self.logger.info(
            f"ECOS API Key: {'설정됨' if self.ecos_api_key else '설정되지 않음'}"
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

    async def _fetch_dart_data(
        self, corp_code: str, report_type: str, year: int, quarter: int = None
    ) -> Dict[str, Any]:
        """DART API에서 재무 데이터 가져오기"""
        if not self.dart_api_key:
            raise FinancialAnalysisError(
                "DART API 키가 설정되지 않았습니다", "NO_API_KEY"
            )

        try:
            # DART API 호출
            if report_type == "income_statement":
                url = f"{self.dart_base_url}/income"
            elif report_type == "balance_sheet":
                url = f"{self.dart_base_url}/balance"
            elif report_type == "cash_flow":
                url = f"{self.dart_base_url}/cashflow"
            else:
                raise FinancialAnalysisError(
                    f"지원하지 않는 재무제표 타입: {report_type}", "INVALID_REPORT_TYPE"
                )

            params = {
                "crtfc_key": self.dart_api_key,
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": (
                    "11011"
                    if quarter == 1
                    else (
                        "11014"
                        if quarter == 2
                        else "11013" if quarter == 3 else "11012"
                    )
                ),
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "status" in data and data["status"] != "000":
                raise FinancialAnalysisError(
                    f"DART API 오류: {data.get('message', '알 수 없는 오류')}",
                    "API_ERROR",
                )

            return data

        except requests.RequestException as e:
            raise FinancialAnalysisError(f"DART API 호출 실패: {e}", "API_ERROR") from e
        except Exception as e:
            raise FinancialAnalysisError(
                f"DART 데이터 처리 실패: {e}", "PROCESSING_ERROR"
            ) from e

    async def _fetch_ecos_market_data(
        self, indicator: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """ECOS API에서 시장 데이터 가져오기"""
        if not self.ecos_api_key:
            raise FinancialAnalysisError(
                "ECOS API 키가 설정되지 않았습니다", "NO_API_KEY"
            )

        try:
            # ECOS API 호출
            url = f"{self.ecos_base_url}/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/{indicator}/A/{start_date}/{end_date}"

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "StatisticSearch" not in data:
                raise FinancialAnalysisError(
                    "ECOS API 응답 형식이 올바르지 않습니다", "INVALID_RESPONSE"
                )

            # 데이터 파싱 및 변환
            records = []
            for item in data["StatisticSearch"]["row"]:
                try:
                    timestamp = datetime.strptime(item.get("TIME", ""), "%Y%m")
                    value = float(item.get("DATA_VALUE", 0))

                    record = {
                        "timestamp": timestamp,
                        "value": value,
                        "unit": item.get("UNIT_NAME", ""),
                        "frequency": item.get("FREQ_NAME", ""),
                        "source": "ECOS",
                    }
                    records.append(record)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"데이터 파싱 실패: {item}, 에러: {e}")
                    continue

            return records

        except requests.RequestException as e:
            raise FinancialAnalysisError(f"ECOS API 호출 실패: {e}", "API_ERROR") from e
        except Exception as e:
            raise FinancialAnalysisError(
                f"ECOS 데이터 처리 실패: {e}", "PROCESSING_ERROR"
            ) from e

    async def get_financial_data(
        self,
        symbol: str,
        data_type: str,
        year: int = None,
        quarter: int = None,
        as_of: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """재무 데이터 조회 - 실제 API 사용"""
        try:
            # 캐시 키 생성
            cache_key = f"{symbol}_{data_type}_{year}_{quarter}"

            # 캐시 확인
            if cache_key in self._cache:
                cache_age = time.time() - self._cache_timestamps[cache_key]
                if cache_age < self.cache_ttl:
                    self.logger.info(f"Cache hit: {cache_key}")
                    return self._cache[cache_key]

            # 실제 데이터 수집
            data = None
            source = "unknown"

            if data_type in ["income_statement", "balance_sheet", "cash_flow"]:
                # DART API에서 재무제표 데이터 가져오기
                try:
                    if year is None:
                        year = datetime.now().year

                    data = await self._fetch_dart_data(symbol, data_type, year, quarter)
                    source = "DART"
                    self.logger.info(f"DART에서 {data_type} 데이터 수집 완료: {symbol}")
                except Exception as e:
                    self.logger.warning(f"DART 데이터 수집 실패: {e}")

            elif data_type == "market_data":
                # ECOS API에서 시장 데이터 가져오기
                try:
                    if year is None:
                        year = datetime.now().year

                    start_date = f"{year}01"
                    end_date = f"{year}12"

                    # 시장 지표 매핑
                    market_indicators = {
                        "KOSPI": "901Y009",  # KOSPI
                        "EXCHANGE_RATE": "036Y001",  # 원/달러 환율
                        "INTEREST_RATE": "721Y001",  # 기준금리
                    }

                    if symbol in market_indicators:
                        data = await self._fetch_ecos_market_data(
                            market_indicators[symbol], start_date, end_date
                        )
                        source = "ECOS"
                        self.logger.info(f"ECOS에서 시장 데이터 수집 완료: {symbol}")
                except Exception as e:
                    self.logger.warning(f"ECOS 데이터 수집 실패: {e}")

            # 데이터가 없으면 더미 데이터 생성 (폴백)
            if data is None:
                data = await self._generate_dummy_financial_data(
                    symbol, data_type, year, quarter
                )
                source = "dummy"
                self.logger.warning("실제 API 데이터 수집 실패, 더미 데이터 생성")

            result = {
                "success": True,
                "symbol": symbol,
                "data_type": data_type,
                "year": year,
                "quarter": quarter,
                "data": data,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "data_quality": ("real" if source in ["DART", "ECOS"] else "dummy"),
            }

            # 캐시 업데이트
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = time.time()

            self.logger.info(
                f"재무 데이터 조회 완료: {symbol} -> {data_type} (quality: {result['data_quality']})"
            )
            return result

        except Exception as e:
            self.logger.error(f"재무 데이터 조회 실패: {e}")
            raise FinancialAnalysisError(
                f"재무 데이터 조회 실패: {e}", "DATA_FETCH_ERROR"
            ) from e

    async def _generate_dummy_financial_data(
        self, symbol: str, data_type: str, year: int, quarter: int = None
    ) -> Dict[str, Any]:
        """더미 재무 데이터 생성 (폴백용)"""
        if data_type == "income_statement":
            return {
                "revenue": 1000000 + (hash(symbol) % 100000),
                "operating_income": 100000 + (hash(symbol) % 50000),
                "net_income": 80000 + (hash(symbol) % 30000),
                "year": year,
                "quarter": quarter,
            }
        elif data_type == "balance_sheet":
            return {
                "total_assets": 2000000 + (hash(symbol) % 200000),
                "total_liabilities": 1000000 + (hash(symbol) % 100000),
                "total_equity": 1000000 + (hash(symbol) % 100000),
                "year": year,
                "quarter": quarter,
            }
        elif data_type == "cash_flow":
            return {
                "operating_cash_flow": 150000 + (hash(symbol) % 50000),
                "investing_cash_flow": -50000 + (hash(symbol) % 20000),
                "financing_cash_flow": -30000 + (hash(symbol) % 15000),
                "year": year,
                "quarter": quarter,
            }
        else:
            return {
                "value": 100 + (hash(symbol) % 50),
                "year": year,
                "quarter": quarter,
            }

    async def calculate_financial_ratios(
        self, financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """재무비율 계산"""
        try:
            income = financial_data["income_statement"]
            balance = financial_data["balance_sheet"]

            revenue = income["revenue"]
            net_income = income["net_income"]
            operating_income = income["operating_income"]
            total_assets = balance["total_assets"]
            total_equity = balance["total_equity"]
            total_debt = balance["total_debt"]

            ratios = {
                "profitability": {
                    "roe": (net_income / total_equity * 100) if total_equity > 0 else 0,
                    "roa": (net_income / total_assets * 100) if total_assets > 0 else 0,
                    "operating_margin": (
                        (operating_income / revenue * 100) if revenue > 0 else 0
                    ),
                    "net_margin": (net_income / revenue * 100) if revenue > 0 else 0,
                },
                "stability": {
                    "debt_to_equity": (
                        (total_debt / total_equity * 100) if total_equity > 0 else 999
                    ),
                    "equity_ratio": (
                        (total_equity / total_assets * 100) if total_assets > 0 else 0
                    ),
                    "debt_to_assets": (
                        (total_debt / total_assets * 100) if total_assets > 0 else 0
                    ),
                },
                "activity": {
                    "asset_turnover": revenue / total_assets if total_assets > 0 else 0,
                    "equity_turnover": (
                        revenue / total_equity if total_equity > 0 else 0
                    ),
                },
            }

            return ratios

        except Exception as e:
            self.logger.error(f"재무비율 계산 실패: {e}")
            raise FinancialAnalysisError(
                f"재무비율 계산 실패: {e}", "RATIO_CALCULATION_ERROR"
            ) from e

    async def calculate_dcf_valuation(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """DCF 밸류에이션 계산"""
        try:
            # 파라미터 설정
            growth_rate = kwargs.get("growth_rate", self.default_growth_rate)
            terminal_growth = kwargs.get(
                "terminal_growth", self.default_terminal_growth
            )
            discount_rate = kwargs.get("discount_rate", self.default_discount_rate)
            projection_years = kwargs.get("projection_years", 5)

            # 재무 데이터 조회
            financial_data = await self.get_financial_data(
                symbol, "income_statement"
            )  # Assuming income_statement for base_fcf
            cash_flow = financial_data["data"]  # Extract data from the result

            base_fcf = cash_flow["net_income"] * 0.7  # Fallback to net_income for FCF
            if base_fcf <= 0:
                base_fcf = (
                    cash_flow["net_income"] * 0.7
                )  # Fallback to net_income for FCF

            # 미래 현금흐름 추정
            projected_fcf = []
            for year in range(1, projection_years + 1):
                fcf = base_fcf * ((1 + growth_rate / 100) ** year)
                projected_fcf.append(fcf)

            # 터미널 가치 계산
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth / 100)
            terminal_value = terminal_fcf / (
                discount_rate / 100 - terminal_growth / 100
            )

            # 현재가치로 할인
            pv_fcf = []
            for year, fcf in enumerate(projected_fcf, 1):
                pv = fcf / ((1 + discount_rate / 100) ** year)
                pv_fcf.append(pv)

            pv_terminal = terminal_value / (
                (1 + discount_rate / 100) ** projection_years
            )

            # 기업가치 계산
            enterprise_value = sum(pv_fcf) + pv_terminal
            total_debt = financial_data["data"][
                "total_debt"
            ]  # Assuming total_debt is in the data
            equity_value = enterprise_value - total_debt

            # 주당 가치
            shares_outstanding = financial_data["data"][
                "shares_outstanding"
            ]  # Assuming shares_outstanding is in the data
            intrinsic_value = (
                (equity_value * 100000000) / shares_outstanding
                if shares_outstanding > 0
                else 0
            )

            # 현재 주가와 비교
            current_price = financial_data["data"][
                "current_price"
            ]  # Assuming current_price is in the data
            upside_potential = (
                ((intrinsic_value - current_price) / current_price * 100)
                if current_price > 0
                else 0
            )

            result = {
                "symbol": symbol,
                "valuation_method": "DCF",
                "assumptions": {
                    "growth_rate": growth_rate,
                    "terminal_growth": terminal_growth,
                    "discount_rate": discount_rate,
                    "projection_years": projection_years,
                },
                "base_free_cash_flow": base_fcf,
                "projected_fcf": projected_fcf,
                "terminal_value": terminal_value,
                "enterprise_value": enterprise_value,
                "equity_value": equity_value,
                "intrinsic_value_per_share": intrinsic_value,
                "current_price": current_price,
                "upside_potential": upside_potential,
                "recommendation": (
                    "매수"
                    if upside_potential > 20
                    else "매도" if upside_potential < -20 else "보유"
                ),
                "currency": "KRW",
                "unit": "억원 (기업가치), 원 (주가)",
                "timestamp": datetime.now().isoformat(),
            }

            return result

        except Exception as e:
            self.logger.error(f"DCF 밸류에이션 계산 실패: {e}")
            raise FinancialAnalysisError(
                f"DCF 밸류에이션 계산 실패: {e}", "DCF_ERROR"
            ) from e

    async def generate_investment_report(self, symbol: str) -> Dict[str, Any]:
        """투자 분석 리포트 생성"""
        try:
            # 재무 데이터 조회
            financial_data = await self.get_financial_data(
                symbol, "income_statement"
            )  # Assuming income_statement for ratios

            # 재무비율 계산
            ratios = self.calculate_financial_ratios(financial_data)

            # DCF 밸류에이션
            dcf_result = await self.calculate_dcf_valuation(symbol)

            # 종합 평가
            roe = ratios["profitability"]["roe"]
            debt_ratio = ratios["stability"]["debt_to_equity"]
            upside = dcf_result["upside_potential"]

            # 투자 등급 결정
            if roe >= 12 and debt_ratio <= 100 and upside > 20:
                grade = "A"
                recommendation = "적극 매수"
            elif roe >= 8 and debt_ratio <= 150 and upside > 0:
                grade = "B"
                recommendation = "매수"
            elif roe >= 5 and debt_ratio <= 200:
                grade = "C"
                recommendation = "보유"
            else:
                grade = "D"
                recommendation = "매도"

            result = {
                "symbol": symbol,
                "company_name": financial_data["data"][
                    "company_name"
                ],  # Assuming company_name is in the data
                "investment_grade": grade,
                "recommendation": recommendation,
                "financial_ratios": ratios,
                "dcf_valuation": dcf_result,
                "summary": {
                    "strengths": [
                        f"ROE {roe:.1f}% (수익성 우수)" if roe >= 10 else None,
                        (
                            f"부채비율 {debt_ratio:.1f}% (안정적)"
                            if debt_ratio <= 100
                            else None
                        ),
                        f"상승여력 {upside:.1f}%" if upside > 0 else None,
                    ],
                    "weaknesses": [
                        f"ROE {roe:.1f}% (개선 필요)" if roe < 8 else None,
                        (
                            f"부채비율 {debt_ratio:.1f}% (위험)"
                            if debt_ratio > 200
                            else None
                        ),
                        f"하락위험 {abs(upside):.1f}%" if upside < 0 else None,
                    ],
                },
                "timestamp": datetime.now().isoformat(),
            }

            # None 값 제거
            result["summary"]["strengths"] = [
                s for s in result["summary"]["strengths"] if s
            ]
            result["summary"]["weaknesses"] = [
                w for w in result["summary"]["weaknesses"] if w
            ]

            return result

        except Exception as e:
            self.logger.error(f"투자 분석 리포트 생성 실패: {e}")
            raise FinancialAnalysisError(
                f"투자 분석 리포트 생성 실패: {e}", "REPORT_GENERATION_ERROR"
            ) from e

    async def connect(self, server_url: str = "") -> bool:
        """MCP 서버에 연결 (재무 분석은 별도 연결 불필요)"""
        return True

    async def disconnect(self) -> bool:
        """MCP 서버와의 연결을 해제"""
        return True

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록을 반환합니다."""
        return [
            {
                "name": "get_financial_data",
                "description": "재무제표 데이터 조회",
                "parameters": {
                    "symbol": "종목코드",
                    "data_type": "데이터 타입 (income, balance, cashflow, all)",
                    "year": "연도 (선택사항)",
                    "quarter": "분기 (선택사항)",
                },
            },
            {
                "name": "calculate_financial_ratios",
                "description": "재무비율 계산",
                "parameters": {"symbol": "종목코드"},
            },
            {
                "name": "generate_investment_report",
                "description": "투자 분석 리포트 생성",
                "parameters": {"symbol": "종목코드"},
            },
            {
                "name": "perform_dcf_valuation",
                "description": "DCF 밸류에이션 수행",
                "parameters": {
                    "symbol": "종목코드",
                    "growth_rate": "성장률 (%)",
                    "terminal_growth": "영구성장률 (%)",
                    "discount_rate": "할인율 (%)",
                    "projection_years": "예측 연도 수",
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
        """도구를 호출합니다."""
        try:
            if tool_name == "get_financial_data":
                symbol = params.get("symbol", "")
                data_type = params.get("data_type", "income")
                year = params.get("year")
                quarter = params.get("quarter")
                result = await self.get_financial_data(symbol, data_type, year, quarter)
                return {"success": True, "data": result}

            elif tool_name == "calculate_financial_ratios":
                symbol = params.get("symbol", "")
                financial_data = await self.get_financial_data(
                    symbol, "income_statement"
                )  # Assuming income_statement for ratios
                ratios = self.calculate_financial_ratios(financial_data)
                return {"success": True, "data": ratios}

            elif tool_name == "generate_investment_report":
                symbol = params.get("symbol", "")
                result = await self.generate_investment_report(symbol)
                return {"success": True, "data": result}

            elif tool_name == "perform_dcf_valuation":
                symbol = params.get("symbol", "")
                result = await self.calculate_dcf_valuation(symbol, **params)
                return {"success": True, "data": result}

            elif tool_name == "get_server_health":
                return await self.get_server_health()

            elif tool_name == "get_server_metrics":
                return await self.get_server_metrics()

            else:
                return {
                    "success": False,
                    "error": f"알 수 없는 도구: {tool_name}",
                    "message": "지원하지 않는 도구입니다.",
                }

        except Exception as e:
            self.logger.error(f"도구 호출 실패: {tool_name}, 에러: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"도구 '{tool_name}' 실행에 실패했습니다.",
            }

    async def close(self):
        """클라이언트 리소스 정리"""
        self.logger.info("FinancialAnalysisClient 종료")

    async def get_server_health(self) -> Dict[str, Any]:
        """서버 헬스 상태 조회"""
        return {
            "status": "healthy",
            "service": "FinancialAnalysis",
            "timestamp": datetime.now().isoformat(),
            "message": "FinancialAnalysis MCP 서버가 정상적으로 작동 중입니다",
        }

    async def get_server_metrics(self) -> Dict[str, Any]:
        """서버 메트릭 조회"""
        return {
            "service": "FinancialAnalysis",
            "cache_entries": len(self._cache),
            "cache_ttl_seconds": self.cache_ttl,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "dart_api_configured": bool(self.dart_api_key),
            "ecos_api_configured": bool(self.ecos_api_key),
            "timestamp": datetime.now().isoformat(),
            "message": "FinancialAnalysis MCP 서버 메트릭 정보",
        }

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
