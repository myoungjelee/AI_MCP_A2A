"""
키움 Info Domain 서버

종목/업종/테마/ETF 정보 제공 도메인 서버
- 종목 정보 조회
- 업종 정보 및 구성종목
- 테마 그룹 및 구성종목
- ETF 정보 및 시세

포트: 8032
"""

import logging

from pydantic import BaseModel, Field, field_validator

from src.mcp_servers.base.base_mcp_server import StandardResponse
from src.mcp_servers.kiwoom_mcp.common.constants.api_types import KiwoomAPIID
from src.mcp_servers.kiwoom_mcp.common.domain_base import KiwoomDomainServer

logger = logging.getLogger(__name__)


# === 입력 모델들 ===


class StockInfoRequest(BaseModel):
    """종목 정보 조회 요청"""

    stock_code: str = Field(description="종목코드 (6자리)", min_length=6, max_length=6)

    @field_validator("stock_code")
    def validate_stock_code(cls, v):
        if not v.isdigit():
            raise ValueError("종목코드는 6자리 숫자여야 합니다")
        return v


class StockListRequest(BaseModel):
    """종목 리스트 조회 요청"""

    market_type: str = Field(default="ALL", description="시장구분 (ALL, KOSPI, KOSDAQ)")


class SectorListRequest(BaseModel):
    """업종 코드 리스트 요청"""

    market_type: str = Field(default="0", description="시장구분 (0:KOSPI, 1:KOSDAQ)")


class SectorInfoRequest(BaseModel):
    """업종 정보 조회 요청"""

    market_type: str = Field(default="0", description="시장구분")
    sector_code: str = Field(description="업종코드")


class SectorStocksRequest(BaseModel):
    """업종별 종목 조회 요청"""

    market_type: str = Field(default="0", description="시장구분")
    sector_code: str = Field(description="업종코드")
    stock_exchange: str = Field(default="0", description="거래소구분")


class ThemeListRequest(BaseModel):
    """테마 그룹 리스트 요청"""

    query_type: str = Field(default="1", description="조회구분")
    date_type: str | None = Field(default=None, description="일자구분")
    sort_type: str | None = Field(default=None, description="정렬구분")
    stock_exchange: str = Field(default="0", description="거래소구분")


class ThemeStocksRequest(BaseModel):
    """테마 구성종목 요청"""

    theme_group_code: str = Field(description="테마그룹코드")
    stock_exchange: str = Field(default="0", description="거래소구분")


class ETFInfoRequest(BaseModel):
    """ETF 종목정보 요청"""

    stock_code: str = Field(description="ETF 종목코드")


class ETFListRequest(BaseModel):
    """ETF 전체시세 요청"""

    tax_type: str = Field(default="00", description="과세유형")
    nav_diff: str = Field(default="0", description="NAV괴리")
    manager: str | None = Field(default=None, description="운용사")
    tax_yn: str = Field(default="0", description="과세여부")
    index_code: str | None = Field(default=None, description="추적지수")
    stock_exchange: str = Field(default="0", description="거래소구분")


# === Info Domain 서버 클래스 ===


class InfoDomainServer(KiwoomDomainServer):
    """
    키움 Info Domain 서버 - 종목 정보 중앙 허브.

    🏗️ 아키텍처 위치:
    - **Layer 1 (MCP Server)**: 종목 정보 제공자
    - **Port**: 8032
    - **Domain**: info_domain

    📊 주요 기능:
    1. **종목 정보**:
       - 기본 정보 (종목명, 시가총액, PER, PBR)
       - 재무 정보 (ROE, 부채비율, 영업이익률)
       - 배당 정보 (배당금, 배당수익률)

    2. **업종 정보**:
       - 업종 지수 현재가
       - 업종별 구성종목
       - 업종 등락률 및 거래량

    3. **테마 그룹**:
       - 테마별 종목 분류
       - 테마 구성종목 리스트
       - 테마별 수익률 현황

    4. **ETF 정보**:
       - ETF 종목 상세
       - NAV (순자산가치) 및 괴리도
       - ETF 구성종목 및 비중

    🔧 LangGraph Agent 연동:
    - **DataCollectorAgent**: 종목 기본정보 수집
    - **AnalysisAgent**: 재무 데이터 기반 fundamental 분석
    - **SupervisorAgent**: 업종/테마 비교 분석

    ⚡ MCP Tools (12개):
    - get_stock_basic_info: 주식 기본정보
    - get_stock_detail_info: 종목 상세정보
    - get_stock_list: 종목 리스트
    - get_sector_current_price: 업종 현재가
    - get_sector_stocks: 업종별 종목
    - get_sector_code_list: 업종코드 리스트
    - get_theme_group_list: 테마 그룹 리스트
    - get_theme_stocks: 테마 구성종목
    - get_etf_info: ETF 종목정보
    - get_etf_list: ETF 전체시세

    💡 특징:
    - 종목 데이터 캠싱으로 불필요한 API 호출 최소화
    - 업종/테마 분류 자동 업데이트
    - ETF 구성종목 실시간 추적
    - 재무 지표 자동 계산 및 정규화

    Note:
        - 키움 API의 ka101xx 시리즈 활용
        - 종목 정보는 1일 1회 갱신
        - 업종/테마 분류는 주기적 재분류
    """

    def __init__(self, debug: bool = False):
        """
        Info Domain 서버 초기화.

        Args:
            debug: 디버그 모드 활성화 여부

        Note:
            - 포트 8032에서 실행
            - 종목 정보 캐시 초기화
            - 업종/테마 분류 체계 로드
        """
        super().__init__(
            domain_name="info",
            server_name="kiwoom-stock-info-domain",
            port=8032,
            debug=debug,
        )

        logger.info("Info Domain Server initialized")

    def _initialize_clients(self) -> None:
        """클라이언트 초기화"""
        # 부모 클래스 호출
        super()._initialize_clients()
        logger.info("Info domain clients initialized")

    def _register_tools(self) -> None:
        """도구 등록"""
        # 정보 관련 도구 등록
        self._register_info_tools()
        # 공통 리소스 등록
        self.register_common_resources()
        logger.info("Info domain tools registered")

    def _register_info_tools(self):
        """
        종목 정보 MCP 도구들 등록.

        등록되는 도구 카테고리:
        1. 종목 정보 도구 (3개)
        2. 업종 정보 도구 (3개)
        3. 테마 정보 도구 (2개)
        4. ETF 정보 도구 (2개)

        Note:
            - 모든 도구는 Pydantic 모델로 입력 검증
            - 캐싱 가능한 도구들은 캐싱 적용
            - 종목코드는 6자리 숫자로 검증
        """

        # === 1. 종목 정보 도구들 ===

        @self.mcp.tool()
        async def get_stock_basic_info(stock_code: str) -> StandardResponse:
            """
            주식 기본정보 조회

            API: ka10001 (주식기본정보요청)
            종목의 기본 정보 (종목명, 시가총액, PER, PBR 등)

            Args:
                stock_code: 종목코드 (6자리)
            """
            # 유효성 검증
            if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
                return await self.create_error_response(
                    func_name="get_stock_basic_info",
                    error="종목코드는 6자리 숫자여야 합니다"
                )

            query = f"주식 기본정보: {stock_code}"
            params = {"stk_cd": stock_code}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.STOCK_BASIC_INFO,
                query=query,
                params=params,
            )

        @self.mcp.tool()
        async def get_stock_detail_info(stock_code: str) -> StandardResponse:
            """
            종목 상세정보 조회

            API: ka10100 (종목정보 조회)
            종목의 상세 정보 (재무정보, 배당정보 등)

            Args:
                stock_code: 종목코드 (6자리)
            """
            # 유효성 검증
            if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
                return await self.create_error_response(
                    func_name="get_stock_detail_info",
                    error="종목코드는 6자리 숫자여야 합니다"
                )

            query = f"종목 상세정보: {stock_code}"

            params = {"stk_cd": stock_code}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.STOCK_INFO,
                query=query,
                params=params,
            )

        @self.mcp.tool()
        async def get_stock_list(market_type: str = "ALL") -> StandardResponse:
            """
            종목정보 리스트 조회

            API: ka10099 (종목정보 리스트)
            시장별 전체 종목 리스트

            Args:
                market_type: 시장구분 (ALL, KOSPI, KOSDAQ) - 기본값 ALL
            """
            query = f"종목 리스트: {market_type}"

            params = {"mrkt_tp": market_type}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.STOCK_LIST,
                query=query,
                params=params,
            )

        # === 2. 업종 정보 도구들 ===

        @self.mcp.tool()
        async def get_sector_current_price(
            sector_code: str,
            market_type: str = "0",
        ) -> StandardResponse:
            """
            업종 현재가 조회

            API: ka20001 (업종현재가요청)
            업종 지수 현재가 및 등락률

            Args:
                sector_code: 업종코드
                market_type: 시장구분 (0:KOSPI, 1:KOSDAQ)
            """
            query = f"업종 현재가: {sector_code}"

            params = {"mrkt_tp": market_type, "inds_cd": sector_code}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.SECTOR_CURRENT_PRICE,
                query=query,
                params=params,
            )

        @self.mcp.tool()
        async def get_sector_stocks(
            sector_code: str,
            market_type: str = "0",
            stock_exchange: str = "0",
        ) -> StandardResponse:
            """
            업종별 주가 조회

            Kiwoom API: ka20002 (업종별주가요청)
            업종에 속한 종목들의 현재가 정보

            Args:
                sector_code: 업종코드
                market_type: 시장구분 (0:KOSPI, 1:KOSDAQ)
                stock_exchange: 거래소구분
            """
            query = f"업종별 종목: {sector_code}"

            params = {
                "mrkt_tp": market_type,
                "inds_cd": sector_code,
                "stex_tp": stock_exchange,
            }

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.SECTOR_PRICE,
                query=query,
                params=params,
            )

        @self.mcp.tool()
        async def get_sector_code_list(
            market_type: str = "0",
        ) -> StandardResponse:
            """
            업종코드 리스트 조회

            Kiwoom API: ka10101 (업종코드 리스트)
            시장별 업종 코드 목록

            Args:
                market_type: 시장구분 (0:KOSPI, 1:KOSDAQ)
            """
            query = f"업종코드 리스트: {market_type}"

            params = {"mrkt_tp": market_type}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.SECTOR_CODE_LIST,
                query=query,
                params=params,
            )

        # === 3. 테마 정보 도구들 ===

        @self.mcp.tool()
        async def get_theme_group_list(
            query_type: str = "1",
            date_type: str | None = None,
            sort_type: str | None = None,
            stock_exchange: str = "0",
        ) -> StandardResponse:
            """
            테마 그룹별 조회

            API: ka90001 (테마그룹별요청)
            테마 그룹 목록 및 정보

            Args:
                query_type: 조회구분 (기본값: "1")
                date_type: 일자구분 (선택사항)
                sort_type: 정렬구분 (선택사항)
                stock_exchange: 거래소구분 (기본값: "0")
            """
            query = "테마 그룹 목록"

            params = {
                "qry_tp": query_type,
                "date_tp": date_type,
                "flu_pl_amt_tp": sort_type,
                "stex_tp": stock_exchange,
                "stk_cd": None,
                "thema_nm": None,
            }

            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.THEME_GROUP,
                query=query,
                params=params,
            )

        @self.mcp.tool()
        async def get_theme_stocks(
            theme_group_code: str,
            stock_exchange: str = "0",
        ) -> StandardResponse:
            """
            테마 구성종목 조회

            API: ka90002 (테마구성종목요청)
            특정 테마에 속한 종목 목록

            Args:
                theme_group_code: 테마그룹코드
                stock_exchange: 거래소구분 (기본값: "0")
            """
            query = f"테마 구성종목: {theme_group_code}"

            params = {
                "thema_grp_cd": theme_group_code,
                "stex_tp": stock_exchange,
                "date_tp": None,
            }

            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.THEME_STOCKS,
                query=query,
                params=params,
            )

        # === 4. ETF 정보 도구들 ===

        @self.mcp.tool()
        async def get_etf_info(
            stock_code: str,
        ) -> StandardResponse:
            """
            ETF 종목정보 조회

            API: ka40002 (ETF종목정보요청)
            ETF 상세 정보 (기초지수, 운용사, NAV 등)

            Args:
                stock_code: ETF 종목코드
            """
            query = f"ETF 종목정보: {stock_code}"

            params = {"stk_cd": stock_code}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.ETF_STOCK_INFO,
                query=query,
                params=params,
            )

        @self.mcp.tool()
        async def get_etf_total_quote(
            tax_type: str = "00",
            nav_diff: str = "0",
            manager: str | None = None,
            tax_yn: str = "0",
            index_code: str | None = None,
            stock_exchange: str = "0",
        ) -> StandardResponse:
            """
            ETF 전체시세 조회

            API: ka40004 (ETF전체시세요청)
            ETF 전체 종목의 시세 정보

            Args:
                tax_type: 과세유형 (기본값: "00")
                nav_diff: NAV괴리 (기본값: "0")
                manager: 운용사 (선택사항)
                tax_yn: 과세여부 (기본값: "0")
                index_code: 추적지수 (선택사항)
                stock_exchange: 거래소구분 (기본값: "0")
            """
            query = "ETF 전체시세"

            params = {
                "txon_type": tax_type,
                "navpre": nav_diff,
                "mngmcomp": manager,
                "txon_yn": tax_yn,
                "trace_idex": index_code,
                "stex_tp": stock_exchange,
            }

            # None 값 제거
            params = {k: v for k, v in params.items() if v is not None}

            return await self.call_api_with_response(
                api_id=KiwoomAPIID.ETF_TOTAL_QUOTE,
                query=query,
                params=params,
            )

        logger.info("Info domain tools registered successfully")


# === 서버 인스턴스 생성 ===


def create_info_domain_server(debug: bool = False) -> InfoDomainServer:
    """Info Domain 서버 인스턴스 생성"""
    return InfoDomainServer(debug=debug)


# === 메인 실행 ===


def main():
    """메인 실행 함수"""
    import argparse

    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware

    parser = argparse.ArgumentParser(description="Kiwoom Info Domain Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=8032, help="Server port")
    args = parser.parse_args()

    # 서버 생성
    server = InfoDomainServer(debug=args.debug or False)

    # 포트 설정 (필요시)
    if args.port != 8032:
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
        logger.info(f"Starting Info Domain Server on port {server.port} with CORS middleware")
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
        logger.info("Info Domain Server stopped")


if __name__ == "__main__":
    main()
