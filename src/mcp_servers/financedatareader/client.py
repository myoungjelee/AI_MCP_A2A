"""
FinanceDataReader 기반 한국 주식 데이터 MCP 클라이언트

- Kiwoom 의존성을 제거하고 FinanceDataReader(FDR)로 대체
- 인증, OAuth, httpx 기반 호출 제거
- 일/지수/리스트/검색 등 FDR이 제공하는 범위만 구현
- 실시간(호가/체결), 계좌 정보, 외국인 매매 동향 등은 FDR에서 제공되지 않으므로 NOT_SUPPORTED 처리

설계 원칙(가독성/유지보수성/확장성):
- 명확한 함수명과 타입힌트
- 얇은 어댑터 계층: FDR → 프로젝트 표준 응답 스키마로 변환
- 캐시(TTL) 내장으로 불필요한 원격 호출 감소
- 실패는 구조화된 에러로 반환(서버 레이어에서 일관 응답 포맷 생성)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import FinanceDataReader as fdr
import pandas as pd

# (옵션) 미들웨어 의존성: 기존 프로젝트 구조 유지용
try:
    from ..base.middleware import MiddlewareManager  # type: ignore
except Exception:  # 단독 실행 시에도 동작하도록 가드

    class MiddlewareManager:  # minimal stub
        def __init__(self, name: str): ...
        def apply_all(self, *_args, **_kwargs):
            def _wrap(fn):
                return fn

            return _wrap


# ========= 공통 예외 =========


class DataSourceError(Exception):
    """외부 데이터 소스(FDR) 호출/파싱 실패"""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.error_code = error_code


# ========= 헬퍼 =========


def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """'YYYYMMDD' 또는 'YYYY-MM-DD' 둘 다 허용 → 'YYYY-MM-DD'로 정규화"""
    if not date_str:
        return None
    s = str(date_str).strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s  # assume already ISO-like


def _compute_change_and_rate(df: pd.DataFrame) -> Tuple[float, float]:
    """마지막 2개 종가로 변동액/변동률 계산. 데이터가 1개면 변동 0 처리."""
    if len(df) >= 2:
        last = float(df.iloc[-1]["Close"])
        prev = float(df.iloc[-2]["Close"])
        change = last - prev
        rate = (change / prev) * 100 if prev != 0 else 0.0
        return change, rate
    elif len(df) == 1:
        return 0.0, 0.0
    else:
        raise DataSourceError("데이터가 비어 있습니다", "NO_DATA")


# ========= 클라이언트 =========


@dataclass
class CacheEntry:
    value: Any
    created_at: datetime


class FinanceDataReaderClient:
    """FinanceDataReader 기반 한국 주식 데이터 MCP 클라이언트"""

    def __init__(self, name: str = "fdr_client") -> None:
        self.name = name
        self.logger = logging.getLogger(f"fdr_client.{name}")
        self._setup_logging()

        # 미들웨어(프로젝트 표준 유지)
        self.middleware = MiddlewareManager("fdr")

        # 간단 캐시
        self._cache: dict[str, CacheEntry] = {}
        self.cache_ttl_sec: int = 300  # 5분

    # ----- infra -----

    def _setup_logging(self) -> None:
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

    def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        key_items = ",".join(f"{k}={params[k]}" for k in sorted(params.keys()))
        return f"{operation}:{key_items}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry:
            return None
        age = (datetime.now() - entry.created_at).total_seconds()
        if age <= self.cache_ttl_sec:
            return entry.value
        self._cache.pop(key, None)
        return None

    def _save_cache(self, key: str, value: Any) -> None:
        self._cache[key] = CacheEntry(value=value, created_at=datetime.now())

    # ----- 도구 목록 / 디스패처 (호환성 유지) -----

    async def list_tools(self) -> List[Dict[str, Any]]:
        return [
            # 1) 종목/차트/검색 (지원)
            {
                "name": "get_stock_basic_info",
                "description": "일일 종가 기반 기본정보(변동률 포함)",
                "parameters": {"stock_code": "string"},
            },
            {
                "name": "get_stock_info",
                "description": "상장정보(이름, 섹터 등). FDR StockListing 기반.",
                "parameters": {"stock_code": "string"},
            },
            {
                "name": "get_stock_list",
                "description": "종목 리스트(KRX/KOSPI/KOSDAQ)",
                "parameters": {"market_type": "string (ALL|KOSPI|KOSDAQ)"},
            },
            {
                "name": "get_daily_chart",
                "description": "일봉 OHLCV (YYYYMMDD/ISO 범위)",
                "parameters": {
                    "stock_code": "string",
                    "start_date": "string?",
                    "end_date": "string?",
                },
            },
            {
                "name": "search_stock_by_name",
                "description": "종목명 부분검색",
                "parameters": {"query": "string", "limit": "int?"},
            },
            # 2) 지수/시장 상태 (지원)
            {
                "name": "get_market_overview",
                "description": "KOSPI/ KOSDAQ 지수 요약",
                "parameters": {},
            },
            {
                "name": "get_market_status",
                "description": "간단한 장 상태(09:00~15:30)",
                "parameters": {},
            },
            # 3) 미지원 (명시)
            {
                "name": "get_minute_chart",
                "description": "분봉: FDR 미지원",
                "parameters": {
                    "stock_code": "string",
                    "interval": "int",
                    "count": "int",
                },
            },
            {
                "name": "get_stock_orderbook",
                "description": "호가: FDR 미지원",
                "parameters": {"stock_code": "string"},
            },
            {
                "name": "get_stock_execution_info",
                "description": "체결: FDR 미지원",
                "parameters": {"stock_code": "string"},
            },
            {
                "name": "get_price_change_ranking",
                "description": "등락률 순위: FDR 기본 미제공",
                "parameters": {
                    "ranking_type": "string",
                    "market_type": "string",
                    "count": "int",
                },
            },
            {
                "name": "get_volume_top_ranking",
                "description": "거래량 순위: FDR 기본 미제공",
                "parameters": {"market_type": "string", "count": "int"},
            },
            {
                "name": "get_foreign_trading_trend",
                "description": "외국인 동향: FDR 미지원",
                "parameters": {"stock_code": "string"},
            },
            # 4) 서버 관리 도구 (지원)
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
        # 지원되는 도구
        if tool_name == "get_stock_basic_info":
            return await self.get_stock_basic_info(kwargs.get("stock_code"))
        if tool_name == "get_stock_info":
            return await self.get_stock_info(kwargs.get("stock_code"))
        if tool_name == "get_stock_list":
            return await self.get_stock_list(kwargs.get("market_type", "ALL"))
        if tool_name == "get_daily_chart":
            return await self.get_daily_chart(
                kwargs.get("stock_code"),
                kwargs.get("start_date"),
                kwargs.get("end_date"),
            )
        if tool_name == "search_stock_by_name":
            return await self.search_stock_by_name(
                kwargs.get("query"), kwargs.get("limit")
            )

        if tool_name == "get_market_overview":
            return await self.get_market_overview()
        if tool_name == "get_market_status":
            return await self.get_market_status()

        # 서버 관리 도구
        if tool_name == "get_server_health":
            return await self.get_server_health()
        if tool_name == "get_server_metrics":
            return await self.get_server_metrics()

        # 명시적으로 미지원
        if tool_name in {
            "get_minute_chart",
            "get_stock_orderbook",
            "get_stock_execution_info",
            "get_price_change_ranking",
            "get_volume_top_ranking",
            "get_foreign_trading_trend",
        }:
            return self._not_supported(
                tool_name, "FinanceDataReader does not provide this."
            )

        return self._error("UNKNOWN_TOOL", f"Unknown tool: {tool_name}")

    # ----- 구현(지원) -----

    async def get_stock_basic_info(self, stock_code: Optional[str]) -> Dict[str, Any]:
        if not stock_code:
            return self._error("INVALID_PARAM", "stock_code is required.")
        try:
            key = self._get_cache_key("basic_info", {"code": stock_code})
            cached = self._get_from_cache(key)
            if cached:
                return cached

            df = fdr.DataReader(stock_code)
            if df.empty:
                return self._error("NO_DATA", f"No data for {stock_code}.")

            change, rate = _compute_change_and_rate(df)
            last = df.iloc[-1]

            result = {
                "stock_code": stock_code,
                "date": str(last.name.date()),
                "open": float(last["Open"]),
                "high": float(last["High"]),
                "low": float(last["Low"]),
                "close": float(last["Close"]),
                "volume": int(last["Volume"]) if not pd.isna(last["Volume"]) else None,
                "change": float(change),
                "change_rate": float(rate),
                "timestamp": datetime.now().isoformat(),
                "note": "Based on last daily close (not realtime).",
            }
            self._save_cache(key, result)
            return result
        except Exception as e:
            self.logger.exception("get_stock_basic_info failed")
            return self._error("FDR_ERROR", str(e))

    async def get_stock_info(self, stock_code: Optional[str]) -> Dict[str, Any]:
        if not stock_code:
            return self._error("INVALID_PARAM", "stock_code is required.")
        try:
            key = self._get_cache_key("stock_info", {"code": stock_code})
            cached = self._get_from_cache(key)
            if cached:
                return cached

            # KRX 전체에서 코드 매칭
            listing = fdr.StockListing("KRX")
            row = listing[listing["Symbol"] == stock_code]
            if row.empty:
                return self._error(
                    "NOT_FOUND", f"{stock_code} not found in KRX listing."
                )

            r0 = row.iloc[0]
            result = {
                "stock_code": stock_code,
                "name": r0.get("Name"),
                "market": r0.get("Market"),
                "sector": r0.get("Sector"),
                "industry": r0.get("Industry"),
                "listing_date": (
                    str(r0.get("ListingDate")) if "ListingDate" in row.columns else None
                ),
                "foreign_rate": (
                    float(r0.get("ForeignRate"))
                    if "ForeignRate" in row.columns and pd.notna(r0.get("ForeignRate"))
                    else None
                ),
                "shares": (
                    int(r0.get("Shares"))
                    if "Shares" in row.columns and pd.notna(r0.get("Shares"))
                    else None
                ),
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache(key, result)
            return result
        except Exception as e:
            self.logger.exception("get_stock_info failed")
            return self._error("FDR_ERROR", str(e))

    async def get_stock_list(self, market_type: str = "ALL") -> Dict[str, Any]:
        try:
            key = self._get_cache_key("stock_list", {"market": market_type})
            cached = self._get_from_cache(key)
            if cached:
                return cached

            if market_type == "KOSPI":
                listing = fdr.StockListing("KOSPI")
            elif market_type == "KOSDAQ":
                listing = fdr.StockListing("KOSDAQ")
            else:
                listing = fdr.StockListing("KRX")  # ALL

            items = [
                {
                    "code": str(row.get("Symbol")),
                    "name": row.get("Name"),
                    "market": row.get("Market"),
                }
                for _, row in listing.iterrows()
            ]

            result = {
                "market_type": market_type,
                "total_count": len(items),
                "stocks": items,
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache(key, result)
            return result
        except Exception as e:
            self.logger.exception("get_stock_list failed")
            return self._error("FDR_ERROR", str(e))

    async def get_daily_chart(
        self,
        stock_code: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Dict[str, Any]:
        if not stock_code:
            return self._error("INVALID_PARAM", "stock_code is required.")
        try:
            start_iso = _parse_date(start_date)
            end_iso = _parse_date(end_date)
            key = self._get_cache_key(
                "daily_chart", {"code": stock_code, "start": start_iso, "end": end_iso}
            )
            cached = self._get_from_cache(key)
            if cached:
                return cached

            df = fdr.DataReader(stock_code, start_iso, end_iso)
            if df.empty:
                return self._error("NO_DATA", f"No data for {stock_code} in range.")

            data = []
            for _, row in df.reset_index().iterrows():
                data.append(
                    {
                        "date": (
                            str(row["Date"].date())
                            if "Date" in row
                            else (
                                str(row["index"].date())
                                if "index" in row
                                else str(row.name)
                            )
                        ),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": (
                            int(row["Volume"])
                            if "Volume" in row and pd.notna(row["Volume"])
                            else None
                        ),
                    }
                )

            result = {
                "stock_code": stock_code,
                "start_date": start_iso,
                "end_date": end_iso,
                "total_count": len(data),
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache(key, result)
            return result
        except Exception as e:
            self.logger.exception("get_daily_chart failed")
            return self._error("FDR_ERROR", str(e))

    async def search_stock_by_name(
        self, query: Optional[str], limit: Optional[int] = None
    ) -> Dict[str, Any]:
        if not query:
            return self._error("INVALID_PARAM", "query is required.")
        try:
            key = self._get_cache_key("search_stock", {"q": query, "limit": limit or 0})
            cached = self._get_from_cache(key)
            if cached:
                return cached

            listing = fdr.StockListing("KRX")
            sub = listing[
                listing["Name"].str.contains(query, case=False, na=False)
                | listing["Symbol"]
                .astype(str)
                .str.contains(query, case=False, na=False)
            ]
            if limit:
                sub = sub.head(int(limit))

            results = [
                {"code": str(r["Symbol"]), "name": r["Name"], "market": r.get("Market")}
                for _, r in sub.iterrows()
            ]
            result = {
                "query": query,
                "count": len(results),
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache(key, result)
            return result
        except Exception as e:
            self.logger.exception("search_stock_by_name failed")
            return self._error("FDR_ERROR", str(e))

    async def get_market_overview(self) -> Dict[str, Any]:
        """KOSPI(KS11), KOSDAQ(KQ11) 지수 마지막 2개로 등락 계산"""
        try:
            key = self._get_cache_key("market_overview", {})
            cached = self._get_from_cache(key)
            if cached:
                return cached

            kospi = fdr.DataReader("KS11").tail(2)
            kq = fdr.DataReader("KQ11").tail(2)

            def _index_summary(df: pd.DataFrame) -> Dict[str, Any]:
                if df.empty:
                    return {"value": None, "change": None, "change_rate": None}
                change, rate = _compute_change_and_rate(df)
                last = df.iloc[-1]
                return {
                    "value": float(last["Close"]),
                    "change": float(change),
                    "change_rate": float(rate),
                    "date": str(last.name.date()),
                }

            result = {
                "market_status": (await self.get_market_status()).get("status"),
                "indices": {
                    "KOSPI": _index_summary(kospi),
                    "KOSDAQ": _index_summary(kq),
                },
                "timestamp": datetime.now().isoformat(),
            }
            self._save_cache(key, result)
            return result
        except Exception as e:
            self.logger.exception("get_market_overview failed")
            return self._error("FDR_ERROR", str(e))

    async def get_market_status(self) -> Dict[str, Any]:
        now = datetime.now()
        is_weekday = now.weekday() < 5  # 0=Mon
        # 한국 거래소 기본 정규장 09:00 ~ 15:30
        open_ = now.replace(hour=9, minute=0, second=0, microsecond=0)
        close_ = now.replace(hour=15, minute=30, second=0, microsecond=0)
        open_now = is_weekday and (open_ <= now <= close_)
        return {
            "market_open": open_now,
            "current_time": now.isoformat(),
            "market_type": "KRX",
            "status": "OPEN" if open_now else "CLOSED",
        }

    async def get_server_health(self) -> Dict[str, Any]:
        """서버 헬스 상태 조회"""
        return {
            "status": "healthy",
            "service": "FinanceDataReader",
            "timestamp": datetime.now().isoformat(),
            "message": "FinanceDataReader MCP 서버가 정상적으로 작동 중입니다",
        }

    async def get_server_metrics(self) -> Dict[str, Any]:
        """서버 메트릭 조회"""
        return {
            "service": "FinanceDataReader",
            "cache_entries": len(self._cache),
            "cache_ttl_seconds": self.cache_ttl_sec,
            "timestamp": datetime.now().isoformat(),
            "message": "FinanceDataReader MCP 서버 메트릭 정보",
        }

    # ----- 미지원/에러 공통 -----

    def _not_supported(self, operation: str, reason: str) -> Dict[str, Any]:
        return {
            "success": False,
            "operation": operation,
            "error_code": "NOT_SUPPORTED",
            "message": reason,
            "timestamp": datetime.now().isoformat(),
        }

    def _error(self, code: str, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error_code": code,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
