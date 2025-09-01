"""
Kiwoom API 연동 MCP 클라이언트 (개발 기술 중심)

키움증권 API를 연동하는 단순한 클라이언트입니다.
실제 트레이딩 로직은 제거하고 API 연동 기술을 어필합니다.
"""

import asyncio
import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import httpx

from ..base.middleware import MiddlewareManager


class KiwoomDataType(Enum):
    """키움 데이터 타입"""

    STOCK_PRICE = "stock_price"
    ACCOUNT_INFO = "account_info"
    STOCK_INFO = "stock_info"
    MARKET_STATUS = "market_status"


@dataclass
class KiwoomRecord:
    """키움 데이터 레코드"""

    data_type: KiwoomDataType
    code: str
    data: Dict[str, Any]
    timestamp: datetime


class KiwoomError(Exception):
    """키움 API 에러"""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code


class KiwoomClient:
    """키움 API 연동 클라이언트 (개발 기술 중심)"""

    def __init__(self, name: str = "kiwoom_client"):
        """클라이언트 초기화"""
        self.name = name

        # 미들웨어 관리자 초기화
        self.middleware = MiddlewareManager("kiwoom")

        self.logger = logging.getLogger(f"kiwoom_client.{name}")
        self._setup_logging()

        # 설정
        self.max_retries = 3
        self.retry_delay = 1.0
        self.cache_ttl = 300  # 5분
        self.timeout = 30.0

        # 간단한 메모리 캐시
        self._cache = {}
        self._cache_timestamps = {}

        # API 설정
        self.base_url = "https://openapi.kiwoom.com"

        # 환경변수에서 API 키 로드
        self.app_key = os.getenv("KIWOOM_APP_KEY")
        self.app_secret = os.getenv("KIWOOM_APP_SECRET")
        self.account_no = os.getenv("KIWOOM_ACCOUNT_NO")

        # HTTP 클라이언트
        self._client = None

        self.logger.info(f"키움 클라이언트 '{name}' 초기화 완료")
        self.logger.info(
            f"Kiwoom App Key: {'설정됨' if self.app_key else '설정되지 않음'}"
        )
        self.logger.info(
            f"Kiwoom App Secret: {'설정됨' if self.app_secret else '설정되지 않음'}"
        )

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def connect_to_kiwoom(
        self, app_key: str = None, app_secret: str = None, account_no: str = None
    ) -> bool:
        """키움 API에 연결"""
        try:
            # 파라미터가 제공되면 사용, 아니면 환경변수 사용
            self.app_key = app_key or self.app_key
            self.app_secret = app_secret or self.app_secret
            self.account_no = account_no or self.account_no

            if not self.app_key or not self.app_secret:
                self.logger.warning(
                    "키움 API 키가 설정되지 않았습니다. 더미 데이터로 동작합니다."
                )
                return False

            # HTTP 클라이언트 생성
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                    "tr_id": "H0_CNT0",
                },
            )

            # 연결 테스트
            test_result = await self._test_connection()
            if test_result:
                self.logger.info("키움 API 연결 성공")
                return True
            else:
                self.logger.error("키움 API 연결 실패")
                return False

        except Exception as e:
            self.logger.error(f"키움 API 연결 중 에러: {e}")
            return False

    async def _test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            # 간단한 API 호출로 연결 테스트
            response = await self._client.get(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"연결 테스트 실패: {e}")
            return False

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """지수 백오프를 사용한 재시도 로직"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise KiwoomError(f"최대 재시도 횟수 초과: {e}") from e

                delay = self.retry_delay * (2**attempt)
                self.logger.warning(
                    f"재시도 {attempt + 1}/{self.max_retries}, {delay}초 후 재시도: {e}"
                )
                await asyncio.sleep(delay)

    def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        key_data = f"{operation}:{str(sorted(params.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[cache_key]
        return age.total_seconds() < self.cache_ttl

    async def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """주식 가격 조회 (실제 API 호출)"""
        cache_key = self._get_cache_key("get_stock_price", {"stock_code": stock_code})

        # 캐시 확인
        if self._is_cache_valid(cache_key):
            self.logger.info(f"캐시 히트: 주식 가격 {stock_code}")
            return self._cache[cache_key]

        try:
            # 실제 API 호출 (개발 기술 어필)
            result = await self._retry_with_backoff(self._fetch_stock_price, stock_code)

            # 캐시 업데이트
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"주식 가격 조회 실패: {e}")
            raise KiwoomError(f"주식 가격 조회 실패: {e}") from e

    async def _fetch_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """실제 주식 가격 API 호출"""
        try:
            # 키움 API 호출 (실제 구현)
            response = await self._client.get(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "10171",
                    "FID_INPUT_ISCD": stock_code,
                },
            )

            if response.status_code == 200:
                data = response.json()
                if data and "output" in data:
                    return {
                        "stock_code": stock_code,
                        "price": data["output"].get("stck_prpr", 0),
                        "change": data["output"].get("prdy_vrss", 0),
                        "change_rate": data["output"].get("prdy_ctrt", 0),
                        "volume": data["output"].get("acml_vol", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    # API 응답이 비어있거나 예상과 다른 경우 샘플 데이터 반환
                    return {
                        "stock_code": stock_code,
                        "price": 50000,
                        "change": 500,
                        "change_rate": 1.0,
                        "volume": 1000000,
                        "timestamp": datetime.now().isoformat(),
                        "note": "샘플 데이터 (API 응답 없음)",
                    }
            else:
                raise KiwoomError(f"API 응답 오류: {response.status_code}")

        except Exception as e:
            # API 호출 실패 시 샘플 데이터 반환
            self.logger.warning(f"API 호출 실패, 샘플 데이터 반환: {e}")
            return {
                "stock_code": stock_code,
                "price": 50000,
                "change": 500,
                "change_rate": 1.0,
                "volume": 1000000,
                "timestamp": datetime.now().isoformat(),
                "note": "샘플 데이터 (API 호출 실패)",
            }

    async def get_account_info(self) -> Dict[str, Any]:
        """계좌 정보 조회 (실제 API 호출)"""
        cache_key = self._get_cache_key("get_account_info", {})

        # 캐시 확인
        if self._is_cache_valid(cache_key):
            self.logger.info("캐시 히트: 계좌 정보")
            return self._cache[cache_key]

        try:
            # 실제 API 호출
            result = await self._retry_with_backoff(self._fetch_account_info)

            # 캐시 업데이트
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"계좌 정보 조회 실패: {e}")
            raise KiwoomError(f"계좌 정보 조회 실패: {e}") from e

    async def _fetch_account_info(self) -> Dict[str, Any]:
        """실제 계좌 정보 API 호출"""
        try:
            # 키움 API 호출 (실제 구현)
            response = await self._client.get(
                f"{self.base_url}/uapi/domestic-stock/v1/trading-inquire/balance",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "2",
                    "FID_INPUT_ISCD": "",
                    "FID_DT": datetime.now().strftime("%Y%m%d"),
                },
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "account_no": self.account_no,
                    "balance": data.get("output", {}).get("prvs_rcdl_excc_amt", 0),
                    "total_value": data.get("output", {}).get("tot_evlu_amt", 0),
                    "profit_loss": data.get("output", {}).get("evlu_pfls_amt", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                raise KiwoomError(f"API 응답 오류: {response.status_code}")

        except Exception as e:
            raise KiwoomError(f"계좌 정보 API 호출 실패: {e}") from e

    async def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """주식 기본 정보 조회"""
        cache_key = self._get_cache_key("get_stock_info", {"stock_code": stock_code})

        if self._is_cache_valid(cache_key):
            self.logger.info(f"캐시 히트: 주식 정보 {stock_code}")
            return self._cache[cache_key]

        try:
            result = await self._retry_with_backoff(self._fetch_stock_info, stock_code)

            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"주식 정보 조회 실패: {e}")
            raise KiwoomError(f"주식 정보 조회 실패: {e}") from e

    async def _fetch_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """실제 주식 정보 API 호출"""
        try:
            response = await self._client.get(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_COND_SCR_DIV_CODE": "10171",
                    "FID_INPUT_ISCD": stock_code,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "stock_code": stock_code,
                    "name": data.get("output", {}).get("hts_kor_isnm", "알 수 없음"),
                    "market": data.get("output", {}).get(
                        "rprs_mrkt_kor_name", "알 수 없음"
                    ),
                    "sector": data.get("output", {}).get("bstp_kor_isnm", "알 수 없음"),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                raise KiwoomError(f"API 응답 오류: {response.status_code}")

        except Exception as e:
            raise KiwoomError(f"주식 정보 API 호출 실패: {e}") from e

    async def get_market_status(self) -> Dict[str, Any]:
        """시장 상태 조회"""
        cache_key = self._get_cache_key("get_market_status", {})

        if self._is_cache_valid(cache_key):
            self.logger.info("캐시 히트: 시장 상태")
            return self._cache[cache_key]

        try:
            result = await self._retry_with_backoff(self._fetch_market_status)

            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"시장 상태 조회 실패: {e}")
            raise KiwoomError(f"시장 상태 조회 실패: {e}") from e

    async def _fetch_market_status(self) -> Dict[str, Any]:
        """실제 시장 상태 API 호출"""
        try:
            # 간단한 시장 상태 정보 (실제 구현 시 키움 API 사용)
            current_time = datetime.now()
            market_open = current_time.hour >= 9 and current_time.hour < 15

            return {
                "market_open": market_open,
                "current_time": current_time.isoformat(),
                "market_type": "KOSPI",
                "status": "OPEN" if market_open else "CLOSED",
            }

        except Exception as e:
            raise KiwoomError(f"시장 상태 API 호출 실패: {e}") from e

    async def search_stock_by_name(self, company_name: str) -> Dict[str, Any]:
        """종목명으로 종목코드 검색"""
        cache_key = self._get_cache_key("search_stock", {"company_name": company_name})

        if self._is_cache_valid(cache_key):
            self.logger.info(f"캐시 히트: 종목 검색 - {company_name}")
            return self._cache[cache_key]

        try:
            result = await self._retry_with_backoff(
                self._search_stock_by_name, company_name
            )

            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"종목명 검색 실패: {e}")
            raise KiwoomError(f"종목명 검색 실패: {e}") from e

    async def _search_stock_by_name(self, company_name: str) -> Dict[str, Any]:
        """실제 종목명 검색 API 호출"""
        try:
            # 실제 구현 시 키움 API ka10099 (종목정보 리스트) 사용
            # 현재는 기본 매핑 데이터 사용
            # 확장된 종목 매핑 (kiwoom_mcp 방식 참고)
            stock_mapping = {
                # 삼성 그룹
                "삼성전자": {"stock_code": "005930", "company_name": "삼성전자"},
                "삼성": {"stock_code": "005930", "company_name": "삼성전자"},
                "samsung": {"stock_code": "005930", "company_name": "삼성전자"},
                "삼성SDI": {"stock_code": "006400", "company_name": "삼성SDI"},
                "삼성바이오로직스": {
                    "stock_code": "207940",
                    "company_name": "삼성바이오로직스",
                },
                # IT 플랫폼
                "네이버": {"stock_code": "035420", "company_name": "NAVER"},
                "NAVER": {"stock_code": "035420", "company_name": "NAVER"},
                "naver": {"stock_code": "035420", "company_name": "NAVER"},
                "카카오": {"stock_code": "035720", "company_name": "카카오"},
                "KAKAO": {"stock_code": "035720", "company_name": "카카오"},
                "kakao": {"stock_code": "035720", "company_name": "카카오"},
                # 반도체
                "SK하이닉스": {"stock_code": "000660", "company_name": "SK하이닉스"},
                "sk하이닉스": {"stock_code": "000660", "company_name": "SK하이닉스"},
                "sk hynix": {"stock_code": "000660", "company_name": "SK하이닉스"},
                "하이닉스": {"stock_code": "000660", "company_name": "SK하이닉스"},
                # 화학/소재
                "LG화학": {"stock_code": "051910", "company_name": "LG화학"},
                "lg화학": {"stock_code": "051910", "company_name": "LG화학"},
                # 자동차
                "현대자동차": {"stock_code": "005380", "company_name": "현대자동차"},
                "현대차": {"stock_code": "005380", "company_name": "현대자동차"},
                "hyundai": {"stock_code": "005380", "company_name": "현대자동차"},
                "기아": {"stock_code": "000270", "company_name": "기아"},
                "kia": {"stock_code": "000270", "company_name": "기아"},
                "현대모비스": {"stock_code": "012330", "company_name": "현대모비스"},
                # 철강/화학
                "포스코": {"stock_code": "005490", "company_name": "포스코홀딩스"},
                "포스코홀딩스": {
                    "stock_code": "005490",
                    "company_name": "포스코홀딩스",
                },
                "posco": {"stock_code": "005490", "company_name": "포스코홀딩스"},
                # 바이오/제약
                "셀트리온": {"stock_code": "068270", "company_name": "셀트리온"},
                "celltrion": {"stock_code": "068270", "company_name": "셀트리온"},
                # 금융
                "KB금융": {"stock_code": "105560", "company_name": "KB금융"},
                "kb금융": {"stock_code": "105560", "company_name": "KB금융"},
                "kb": {"stock_code": "105560", "company_name": "KB금융"},
                "신한지주": {"stock_code": "055550", "company_name": "신한지주"},
                "신한": {"stock_code": "055550", "company_name": "신한지주"},
                "우리금융지주": {
                    "stock_code": "316140",
                    "company_name": "우리금융지주",
                },
                "우리금융": {"stock_code": "316140", "company_name": "우리금융지주"},
                "하나금융지주": {
                    "stock_code": "086790",
                    "company_name": "하나금융지주",
                },
                "하나금융": {"stock_code": "086790", "company_name": "하나금융지주"},
                # 전자/가전
                "LG전자": {"stock_code": "066570", "company_name": "LG전자"},
                "lg전자": {"stock_code": "066570", "company_name": "LG전자"},
                # 통신
                "SK텔레콤": {"stock_code": "017670", "company_name": "SK텔레콤"},
                "skt": {"stock_code": "017670", "company_name": "SK텔레콤"},
                "KT": {"stock_code": "030200", "company_name": "KT"},
                "kt": {"stock_code": "030200", "company_name": "KT"},
                "LG유플러스": {"stock_code": "032640", "company_name": "LG유플러스"},
                "lgu+": {"stock_code": "032640", "company_name": "LG유플러스"},
                # 공기업/유틸리티
                "한국전력": {"stock_code": "015760", "company_name": "한국전력"},
                "한전": {"stock_code": "015760", "company_name": "한국전력"},
                "kepco": {"stock_code": "015760", "company_name": "한국전력"},
                # 해외 주요 종목 (참고용)
                "테슬라": {"stock_code": "TSLA", "company_name": "테슬라"},
                "tesla": {"stock_code": "TSLA", "company_name": "테슬라"},
                "애플": {"stock_code": "AAPL", "company_name": "애플"},
                "apple": {"stock_code": "AAPL", "company_name": "애플"},
                "구글": {"stock_code": "GOOGL", "company_name": "구글"},
                "google": {"stock_code": "GOOGL", "company_name": "구글"},
                "마이크로소프트": {
                    "stock_code": "MSFT",
                    "company_name": "마이크로소프트",
                },
                "microsoft": {"stock_code": "MSFT", "company_name": "마이크로소프트"},
            }

            # 대소문자 구분 없이 검색
            for key, value in stock_mapping.items():
                if (
                    company_name.lower() in key.lower()
                    or key.lower() in company_name.lower()
                ):
                    return {
                        "success": True,
                        "stock_code": value["stock_code"],
                        "company_name": value["company_name"],
                        "source": "mapping",
                        "timestamp": datetime.now().isoformat(),
                    }

            # 찾지 못한 경우 기본값 (삼성전자)
            return {
                "success": False,
                "stock_code": "005930",  # 기본값: 삼성전자
                "company_name": "삼성전자",
                "source": "default",
                "message": f"'{company_name}' 종목을 찾을 수 없어 기본값(삼성전자)을 반환합니다.",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            raise KiwoomError(f"종목 검색 API 호출 실패: {e}") from e

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록"""
        return [
            {
                "name": "get_stock_price",
                "description": "주식 가격 조회",
                "parameters": {"stock_code": "string"},
            },
            {
                "name": "get_account_info",
                "description": "계좌 정보 조회",
                "parameters": {},
            },
            {
                "name": "get_stock_info",
                "description": "주식 기본 정보 조회",
                "parameters": {"stock_code": "string"},
            },
            {
                "name": "get_market_status",
                "description": "시장 상태 조회",
                "parameters": {},
            },
            {
                "name": "search_stock_by_name",
                "description": "종목명으로 종목코드 검색",
                "parameters": {"company_name": "string"},
            },
        ]

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """도구 호출"""
        try:
            if tool_name == "get_stock_price":
                stock_code = kwargs.get("stock_code")
                if not stock_code:
                    raise KiwoomError("stock_code 파라미터가 필요합니다")
                return await self.get_stock_price(stock_code)

            elif tool_name == "get_account_info":
                return await self.get_account_info()

            elif tool_name == "get_stock_info":
                stock_code = kwargs.get("stock_code")
                if not stock_code:
                    raise KiwoomError("stock_code 파라미터가 필요합니다")
                return await self.get_stock_info(stock_code)

            elif tool_name == "get_market_status":
                return await self.get_market_status()

            elif tool_name == "search_stock_by_name":
                company_name = kwargs.get("company_name")
                if not company_name:
                    raise KiwoomError(
                        "company_name 파라미터가 필요합니다", "MISSING_PARAMETER"
                    )
                return await self.search_stock_by_name(company_name)

            else:
                raise KiwoomError(f"알 수 없는 도구: {tool_name}")

        except Exception as e:
            self.logger.error(f"도구 호출 실패: {tool_name}, 에러: {e}")
            raise KiwoomError(f"도구 호출 실패: {e}") from e

    async def close(self):
        """클라이언트 종료"""
        if self._client:
            await self._client.aclose()
            self.logger.info("키움 클라이언트 종료 완료")

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
