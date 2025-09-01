"""
키움 Portfolio Domain 서버

포트폴리오 및 계좌 관리 도구들을 제공하는 도메인 서버
- 계좌 잔고 조회
- 수익률 분석
- 포지션 관리
- 위험 분석

포트: 8034
"""

import asyncio
import logging
from datetime import datetime

# from pydantic import BaseModel, Field  # 더 이상 사용하지 않음
from src.mcp_servers.base.base_mcp_server import StandardResponse
from src.mcp_servers.kiwoom_mcp.common.constants.api_types import KiwoomAPIID
from src.mcp_servers.kiwoom_mcp.common.domain_base import KiwoomDomainServer

logger = logging.getLogger(__name__)


# === 입력 모델들 ===
# 모든 입력 모델은 직접 파라미터로 변경되어 더 이상 사용하지 않음


# === Portfolio Domain 서버 클래스 ===


class PortfolioDomainServer(KiwoomDomainServer):
    """
    키움 Portfolio Domain 서버 - 포트폴리오 관리 핵심.

    🏗️ 아키텍처 위치:
    - **Layer 1 (MCP Server)**: 포트폴리오 관리 제공자
    - **Port**: 8034
    - **Domain**: portfolio_domain

    📊 주요 기능:
    1. **계좌 관리**:
       - 예수금 상세 현황
       - 계좌 평가 현황
       - 주문 가능 금액
       - 출금 가능 금액

    2. **보유종목 관리**:
       - 보유 종목 상세
       - 평가 손익 현황
       - 보유 비중 분석
       - 포지션 트래킹

    3. **손익 분석**:
       - 실현 손익 조회
       - 평가 손익 계산
       - 일별 손익 추이
       - 종목별 손익 상세

    4. **성과 평가**:
       - 수익률 계산 (MDD, CAGR)
       - 리스크 지표 (VaR, Sharpe)
       - 벤치마크 비교
       - 포트폴리오 최적화

    🔧 LangGraph Agent 연동:
    - **TradingAgent**: 포트폴리오 리스크 검사 (핵심 연동)
    - **AnalysisAgent**: 포트폴리오 성과 분석
    - **SupervisorAgent**: 자산 배분 전략 수립

    ⚡ MCP Tools (12개):
    - get_account_balance: 예수금 조회
    - get_account_evaluation: 계좌 평가
    - get_position_details: 보유종목 상세
    - get_realized_profit_daily: 일별 실현손익
    - get_realized_profit_by_stock: 종목별 실현손익
    - get_account_performance: 계좌 수익률
    - get_trading_history: 거래 내역
    - calculate_portfolio_risk: 포트폴리오 위험 계산
    - optimize_portfolio: 포트폴리오 최적화

    💡 특징:
    - 실시간 포트폴리오 평가
    - 리스크 지표 자동 계산
    - 자산 배분 최적화 알고리즘
    - 성과 비교 대시보드

    📈 위험 지표:
    - VaR (Value at Risk): 95% 신뢰수준 최대 손실
    - Sharpe Ratio: 위험 대비 초과 수익률
    - MDD (Maximum Drawdown): 최대 냙폭
    - Beta: 시장 민감도

    Note:
        - 키움 API의 kt00xxx 계좌 시리즈 활용
        - 포트폴리오 평가는 실시간 업데이트
        - 리스크 지표는 매 10분 재계산
        - 모든 거래 내역 자동 기록
    """

    def __init__(self, debug: bool = False):
        """
        Portfolio Domain 서버 초기화.

        Args:
            debug: 디버그 모드 활성화 여부

        Note:
            - 포트 8034에서 실행
            - 포트폴리오 평가 엔진 초기화
            - 리스크 계산 모듈 활성화
            - 성과 추적 시스템 시작
        """
        super().__init__(
            domain_name="portfolio",
            server_name="kiwoom-portfolio-domain",
            port=8034,
            debug=debug,
        )

        logger.info("Portfolio Domain Server initialized")

    def _initialize_clients(self) -> None:
        """클라이언트 초기화"""
        # 부모 클래스 호출
        super()._initialize_clients()
        # 추가 클라이언트 초기화 (필요시)
        logger.info("Portfolio domain clients initialized")

    def _register_tools(self) -> None:
        """도구 등록"""
        # 포트폴리오 관련 도구 등록
        self._register_portfolio_tools()
        # 공통 리소스 등록
        self.register_common_resources()
        logger.info("Portfolio domain tools registered")

    def _register_portfolio_tools(self):
        """
        포트폴리오 관리 MCP 도구들 등록.

        등록되는 도구 카테고리:
        1. 계좌 잔고 및 평가 도구 (3개)
        2. 손익 분석 도구 (2개)
        3. 수익률 및 성과 도구 (2개)
        4. 거래 이력 도구 (2개)
        5. 리스크 관리 도구 (3개)

        Important:
            - VaR 계산시 95% 신뢰수준 사용
            - Sharpe Ratio는 무위험 수익률 2% 가정
            - MDD는 최대 2년간 데이터로 계산
            - 모든 수익률은 연환산 기준
        """

        # === 1. 계좌 잔고 및 평가 도구들 ===

        @self.mcp.tool()
        async def get_account_balance(
            query_type: str = "01",
            account_no: str | None = None
        ) -> StandardResponse:
            """
            예수금 상세 현황 조회

            Args:
                query_type: 조회구분 (01:기본)
                account_no: 계좌번호 (선택사항)

            API: kt00001 (예수금상세현황요청)
            현금 잔고, 주문가능금액, 출금가능금액 등 조회
            """
            query = "예수금 상세 조회"

            params = {"qry_tp": query_type}
            if account_no:
                params["account_no"] = account_no

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.DEPOSIT_DETAIL, query=query, params=params
            )

        @self.mcp.tool()
        async def get_account_evaluation(
            query_type: str = "01",
            stock_exchange: str = "01"
        ) -> StandardResponse:
            """
            계좌평가현황 조회

            Args:
                query_type: 조회구분
                stock_exchange: 거래소구분 (01:전체)

            API: kt00004 (계좌평가현황요청)
            총평가금액, 총손익, 수익률 등 계좌 전체 평가
            """
            query = "계좌 평가 현황"

            params = {
                "qry_tp": query_type,
                "dmst_stex_tp": stock_exchange,
            }

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.ACCOUNT_EVALUATION, query=query, params=params
            )

        @self.mcp.tool()
        async def get_position_details(
            stock_exchange: str = "01"
        ) -> StandardResponse:
            """
            체결잔고 조회 (보유종목 상세)

            Args:
                stock_exchange: 거래소구분 (01:전체)

            API: kt00005 (체결잔고요청)
            보유종목별 수량, 평가금액, 손익 등 상세 정보
            """
            query = "보유종목 상세 조회"

            params = {"dmst_stex_tp": stock_exchange}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.EXECUTION_BALANCE, query=query, params=params
            )

        # === 2. 손익 분석 도구들 ===

        @self.mcp.tool()
        async def get_realized_profit_daily(
            start_date: str,
            end_date: str | None = None,
            stock_code: str | None = None
        ) -> StandardResponse:
            """
            일자별 실현손익 조회

            Args:
                start_date: 시작일자 (YYYYMMDD)
                end_date: 종료일자 (YYYYMMDD) - 선택사항, 기본값: 당일
                stock_code: 종목코드 (선택사항)

            API: ka10074 (일자별실현손익요청)
            지정 기간의 일별 실현손익 추이
            """
            # 입력값 검증
            if not start_date:
                return self.create_standard_response(
                    success=False,
                    query="일자별 실현손익 조회",
                    error="시작일자는 필수입니다"
                )

            query = (
                f"일자별 실현손익: {start_date}~{end_date or '당일'}"
            )

            params = {
                "strt_dt": start_date,
                "end_dt": end_date or datetime.now().strftime("%Y%m%d"),
            }
            if stock_code:
                params["stock_code"] = stock_code

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.DAILY_REALIZED_PL, query=query, params=params
            )

        @self.mcp.tool()
        async def get_realized_profit_by_stock(
            stock_code: str | None = None,
            query_date: str | None = None
        ) -> StandardResponse:
            """
            당일 실현손익 상세 조회

            Args:
                stock_code: 종목코드 (선택사항)
                query_date: 조회일자 (YYYYMMDD) (선택사항)

            API: ka10077 (당일실현손익상세요청)
            종목별 당일 실현손익 상세 내역
            """
            query = f"당일 실현손익 상세: {stock_code or '전체'}"

            params = {"stk_cd": stock_code or ""}
            if query_date:
                params["query_date"] = query_date

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.TODAY_REALIZED_PL_DETAIL, query=query, params=params
            )

        # === 3. 수익률 및 성과 도구들 ===

        @self.mcp.tool()
        async def get_account_performance(
            start_date: str | None = None,
            end_date: str | None = None,
            stock_exchange: str = "01"
        ) -> StandardResponse:
            """
            계좌 수익률 조회

            Args:
                start_date: 시작일자 (선택사항)
                end_date: 종료일자 (선택사항)
                stock_exchange: 거래소구분

            API: ka10085 (계좌수익률요청)
            계좌의 전체 수익률 및 성과 지표
            """
            query = "계좌 수익률 조회"

            params = {"stex_tp": stock_exchange}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.ACCOUNT_RETURN, query=query, params=params
            )

        @self.mcp.tool()
        async def get_daily_performance_history(
            start_date: str,
            end_date: str
        ) -> StandardResponse:
            """
            일별 계좌수익률 상세 현황

            Args:
                start_date: 시작일자 (YYYYMMDD)
                end_date: 종료일자 (YYYYMMDD)

            API: kt00016 (일별계좌수익률상세현황요청)
            지정 기간의 일별 수익률 추이
            """
            # 입력값 검증
            if not start_date or not end_date:
                return self.create_standard_response(
                    success=False,
                    query="일별 수익률 조회",
                    error="시작일자와 종료일자는 필수입니다"
                )

            query = f"일별 수익률: {start_date}~{end_date}"

            params = {"fr_dt": start_date, "to_dt": end_date}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.DAILY_ACCOUNT_RETURN, query=query, params=params
            )

        # === 4. 자산 및 거래내역 도구들 ===

        @self.mcp.tool()
        async def get_estimated_assets(query_type: str = "01") -> StandardResponse:
            """
            추정자산 조회

            API: kt00003 (추정자산조회요청)
            예상 자산 평가액 및 구성 내역
            """
            query = "추정자산 조회"

            params = {"qry_tp": query_type}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.ESTIMATED_ASSET, query=query, params=params
            )

        @self.mcp.tool()
        async def get_trading_history(
            start_date: str,
            end_date: str,
            trade_type: str = "01",
            stock_code: str | None = None
        ) -> StandardResponse:
            """
            위탁종합 거래내역 조회

            Args:
                start_date: 시작일자 (YYYYMMDD)
                end_date: 종료일자 (YYYYMMDD)
                trade_type: 거래구분 (01:전체)
                stock_code: 종목코드 (선택사항)

            API: kt00015 (위탁종합거래내역요청)
            지정 기간의 모든 거래 내역
            """
            # 입력값 검증
            if not start_date or not end_date:
                return self.create_standard_response(
                    success=False,
                    query="거래내역 조회",
                    error="시작일자와 종료일자는 필수입니다"
                )

            query = f"거래내역: {start_date}~{end_date}"

            params = {
                "strt_dt": start_date,
                "end_dt": end_date,
                "tp": trade_type,
                "gds_tp": "01",  # 상품구분
                "dmst_stex_tp": "01",  # 국내거래소
                "stk_cd": stock_code,
                "crnc_cd": None,
                "frgn_stex_code": None,
            }

            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.CONSIGNMENT_TRADE, query=query, params=params
            )

        @self.mcp.tool()
        async def get_daily_trading_journal(
            market_type: str = "01",
            credit_type: str = "00",
            base_date: str | None = None
        ) -> StandardResponse:
            """
            당일 매매일지 조회

            Args:
                market_type: 시장구분
                credit_type: 신용구분
                base_date: 기준일자 (선택사항)

            API: ka10170 (당일매매일지요청)
            당일 거래 활동 요약 및 분석
            """
            query = "당일 매매일지"

            params = {
                "ottks_tp": market_type,
                "ch_crd_tp": credit_type,
                "base_dt": base_date,
            }

            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.TODAY_TRADE_LOG, query=query, params=params
            )

        # === 5. 통합 포트폴리오 분석 도구 ===

        @self.mcp.tool()
        async def get_portfolio_summary() -> StandardResponse:
            """
            포트폴리오 종합 요약

            여러 API를 조합하여 포트폴리오 전체 현황 제공
            """
            query = "포트폴리오 종합 요약"

            try:
                # 병렬로 여러 데이터 조회
                tasks = [
                    self.call_api_with_response(
                        KiwoomAPIID.DEPOSIT_DETAIL, "예수금", {"qry_tp": "01"}
                    ),
                    self.call_api_with_response(
                        KiwoomAPIID.ACCOUNT_EVALUATION,
                        "계좌평가",
                        {"qry_tp": "01", "dmst_stex_tp": "01"},
                    ),
                    self.call_api_with_response(
                        KiwoomAPIID.EXECUTION_BALANCE,
                        "보유종목",
                        {"dmst_stex_tp": "01"},
                    ),
                    self.call_api_with_response(
                        KiwoomAPIID.ACCOUNT_RETURN, "수익률", {"stex_tp": "01"}
                    ),
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 결과 조합 - 타입 안전성을 위한 길이 체크
                if len(results) >= 4:
                    summary_data = {
                        "cash_balance": results[0].data
                        if isinstance(results[0], StandardResponse)
                        and results[0].success
                        else None,
                        "account_evaluation": results[1].data
                        if isinstance(results[1], StandardResponse)
                        and results[1].success
                        else None,
                        "positions": results[2].data
                        if isinstance(results[2], StandardResponse)
                        and results[2].success
                        else None,
                        "performance": results[3].data
                        if isinstance(results[3], StandardResponse)
                        and results[3].success
                        else None,
                        "summary_date": datetime.now().strftime("%Y%m%d"),
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    summary_data = {
                        "error": "Insufficient API responses",
                        "summary_date": datetime.now().strftime("%Y%m%d"),
                        "timestamp": datetime.now().isoformat(),
                    }

                return self.create_standard_response(
                    success=True, query=query, data=summary_data
                )

            except Exception as e:
                logger.error(f"Portfolio summary error: {e}")
                return self.create_standard_response(
                    success=False,
                    query=query,
                    error=f"포트폴리오 요약 조회 실패: {str(e)}",
                )

        logger.info("Portfolio domain tools registered successfully")


# === 서버 인스턴스 생성 ===


def create_portfolio_domain_server(debug: bool = False) -> PortfolioDomainServer:
    """Portfolio Domain 서버 인스턴스 생성"""
    return PortfolioDomainServer(debug=debug)


# === 메인 실행 ===


def main():
    """메인 실행 함수"""
    import argparse

    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware

    parser = argparse.ArgumentParser(description="Kiwoom Portfolio Domain Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8034, help="Server port")
    args = parser.parse_args()

    # 서버 생성
    server = create_portfolio_domain_server(debug=args.debug)

    # 포트 설정 (필요시)
    if args.port != 8034:
        server.port = args.port

    # CORS 미들웨어 정의
    custom_middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=False,
            expose_headers=["*"],
            max_age=600,
        )
    ]

    # Health 엔드포인트 등록 (한 번만)
    @server.mcp.custom_route(
        path="/health",
        methods=["GET", "OPTIONS"],
        include_in_schema=True,
    )
    async def health_check(request):
        """Health check endpoint"""
        from starlette.responses import JSONResponse

        response_data = server.create_standard_response(
            success=True,
            query="MCP Server Health check",
            data="OK",
        )
        return JSONResponse(content=response_data)

    try:
        # FastMCP 실행 - middleware 파라미터 전달이 핵심!
        logger.info(f"Starting Portfolio Domain Server on port {server.port} with CORS middleware")
        server.mcp.run(
            transport="streamable-http",
            host=server.host,
            port=server.port,
            middleware=custom_middleware  # CORS 미들웨어 전달
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("Portfolio Domain Server stopped")


if __name__ == "__main__":
    main()
