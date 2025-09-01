"""
키움 도메인 서버 공통 베이스 클래스

모든 키움 도메인 서버가 상속받는 공통 기능을 제공합니다.
- UnifiedKiwoomClient 통합
- 공통 미들웨어 설정
- 환경변수 로드
- 표준 응답 생성
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import pytz

from src.mcp_servers.base.base_mcp_server import (
    BaseMCPServer,
    ErrorResponse,
    StandardResponse,
)
from src.mcp_servers.kiwoom_mcp.common.client import KiwoomAPIError, KiwoomRESTAPIClient
from src.mcp_servers.kiwoom_mcp.common.constants import KiwoomAPIID

logger = logging.getLogger(__name__)


class KiwoomDomainServer(BaseMCPServer):
    """
    키움 도메인 서버 베이스 클래스

    모든 도메인 서버 (Trading, Market, Info, Investor, Portfolio)가
    이 클래스를 상속받아 구현됩니다.
    """

    def __init__(
        self,
        domain_name: str,
        server_name: str,
        port: int,
        host: str = "0.0.0.0",
        debug: bool = False,
    ):
        """
        도메인 서버 초기화

        Args:
            domain_name: 도메인 이름 (trading, market, info, investor, portfolio)
            server_name: 서버 이름
            port: 서버 포트
            host: 호스트 주소
            debug: 디버그 모드
        """
        # 공통 미들웨어 설정
        middlewares = ["logging", "timing", "error_handling", "cors"]
        if debug:
            middlewares.append("debug")

        self.domain_name = domain_name

        # 환경변수 로드 (클라이언트 초기화 전에 필요)
        self._load_environment()

        # 서버 설명
        instructions = f"Kiwoom {domain_name.title()} Domain MCP Server - 키움증권 {domain_name} 도메인 서비스"

        # 부모 클래스 초기화
        super().__init__(
            server_name=server_name,
            port=port,
            host=host,
            debug=debug,
            server_instructions=instructions,
            enable_middlewares=middlewares,
            json_response=True,
        )

        # API 검증 상태
        self.api_verification_status = {}

        logger.info(
            f"{self.server_name} initialized for {domain_name} domain on port {port}"
        )

    def _load_environment(self):
        """환경변수 로드 (필수)"""
        self.app_key = os.getenv("KIWOOM_APP_KEY")
        self.app_secret = os.getenv("KIWOOM_APP_SECRET")  # 환경변수명 수정
        self.account_no = os.getenv("KIWOOM_ACCOUNT_NO")

        # 환경변수 필수 검증
        if not self.app_key or not self.app_secret or not self.account_no:
            missing = []
            if not self.app_key:
                missing.append("KIWOOM_APP_KEY")
            if not self.app_secret:
                missing.append("KIWOOM_APP_SECRET")  # 환경변수명 수정
            if not self.account_no:
                missing.append("KIWOOM_ACCOUNT_NO")

            error_msg = f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 모드 설정 (production mode 우선)
        if os.getenv("KIWOOM_PRODUCTION_MODE", "false").lower() == "true":
            self.mode = "production"
            logger.warning("🚨 PRODUCTION MODE 활성화 - 실거래 주의!")
        else:
            self.mode = "paper"
            logger.info("📊 Paper Trading 모드 활성화")

        logger.info(f"키움 API 환경변수 로드 완료: account={self.account_no[:4]}****")

    def _initialize_clients(self) -> None:
        """BaseMCPServer 추상 메서드 구현 - KiwoomRESTAPIClient 초기화"""
        try:
            self.client = KiwoomRESTAPIClient(
                app_key=self.app_key,
                app_secret=self.app_secret,
                account_no=self.account_no,
                mode=self.mode,
            )
            logger.info(f"KiwoomRESTAPIClient initialized in {self.mode} mode")
        except Exception as e:
            logger.error(f"Failed to initialize KiwoomRESTAPIClient: {e}")
            # 클라이언트 초기화 실패시 None으로 설정하여 AttributeError 방지
            self.client = None

    def _register_tools(self) -> None:
        """BaseMCPServer 추상 메서드 구현 - 하위 클래스에서 오버라이드"""
        # 하위 클래스에서 도구 등록 구현
        pass

    # === 공통 헬퍼 메서드 ===

    def create_standard_response(
        self,
        success: bool,
        query: str,
        data: Any = None,
        error: str | None = None,
        **kwargs,
    ) -> StandardResponse:
        """
        표준 응답 생성

        Args:
            success: 성공 여부
            query: 원본 쿼리
            data: 응답 데이터
            error: 에러 메시지
            **kwargs: 추가 필드

        Returns:
            StandardResponse 객체
        """
        response = StandardResponse(
            success=success,
            query=query,
            data=data,
        )

        output = response.model_dump()

        # 에러 정보가 있으면 추가
        if error is not None:
            output["error"] = error

        # 추가 필드 처리
        for key, value in kwargs.items():
            output[key] = value

        # 도메인 정보 추가
        output["domain"] = self.domain_name
        output["timestamp"] = datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat()

        return output

    def create_error_response(
        self,
        query: str,
        error: str,
        func_name: str | None = None,
    ) -> ErrorResponse:
        """
        에러 응답 생성

        Args:
            query: 원본 쿼리
            error: 에러 메시지
            func_name: 에러가 발생한 함수명

        Returns:
            ErrorResponse 객체
        """
        response = ErrorResponse(
            success=False,
            query=query,
            error=error,
            func_name=func_name,
        )

        output = response.model_dump()

        # 도메인 정보 추가
        output["domain"] = self.domain_name
        output["timestamp"] = datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat()

        return output

    async def call_api_with_response(
        self,
        api_id: KiwoomAPIID,
        query: str,
        params: dict[str, Any] | None = None,
        **kwargs,
    ) -> StandardResponse:
        """
        API 호출하고 표준 응답으로 래핑 (Rate Limiting 대응)

        Args:
            api_id: API ID
            query: 원본 쿼리
            params: API 파라미터
            **kwargs: 추가 파라미터

        Returns:
            StandardResponse 객체
        """
        if not isinstance(api_id, KiwoomAPIID):
            logger.error(f"Invalid API ID: {api_id}")
            return self.create_error_response(
                query=query,
                error="Invalid API ID: " + str(api_id),
                func_name="call_api_with_response",
            )

        try:
            # 클라이언트 초기화 상태 확인
            if self.client is None:
                logger.error("KiwoomRESTAPIClient is not initialized")
                return self.create_error_response(
                    query=query,
                    error="KiwoomRESTAPIClient is not initialized. Check environment variables and client setup.",
                    func_name="call_api_with_response",
                )

            # Rate Limiting 대응: API 호출 전 대기
            await asyncio.sleep(2)  # 2초 대기

            # KiwoomRESTAPIClient 통한 API 호출
            result: dict[str, Any] = await self.client.call_api(
                api_id,
                params,
                **kwargs,
            )

            # 키움 API 실제 응답 구조에 맞는 검증
            if result and isinstance(result, dict):
                # 키움 API는 rt_cd 대신 실제 데이터 존재 여부로 성공 판정
                has_data = len(result) > 0 and any(
                    key for key in result.keys() if not key.startswith("_")
                )

                # 에러 지표 확인
                has_error = (
                    "error" in str(result).lower()
                    or "fail" in str(result).lower()
                    or result.get("rt_cd")
                    and result.get("rt_cd") != "0"
                )

                if has_data and not has_error:
                    return self.create_standard_response(
                        success=True,
                        query=query,
                        data=result,
                    )
                else:
                    logger.warning(
                        f"API returned data but may have errors for {api_id}: {result}"
                    )
                    return self.create_standard_response(
                        success=True,
                        query=query,
                        data=result,
                    )
            else:
                logger.warning(f"No data returned for {api_id} with query: {query}")
                return self.create_error_response(
                    query=query,
                    error="No data returned",
                    func_name="call_api_with_response",
                )

        except KiwoomAPIError as e:
            logger.error(f"API call failed for {api_id}: {e}")
            return self.create_error_response(
                query=query,
                error=str(e),
                func_name="call_api_with_response",
            )
        except Exception as e:
            logger.error(f"Unexpected error in API call for {api_id}: {e}")
            return self.create_error_response(
                query=query,
                error=f"Unexpected error: {str(e)}",
                func_name="call_api_with_response",
            )

    def check_api_verification(self, api_id: str) -> bool:
        """
        API 검증 상태 확인

        Args:
            api_id: API ID

        Returns:
            검증 완료 여부
        """
        return self.api_verification_status.get(api_id, False)

    def mark_api_verified(self, api_id: str):
        """
        API를 검증 완료로 마킹

        Args:
            api_id: API ID
        """
        self.api_verification_status[api_id] = True
        logger.info(f"API {api_id} marked as verified")

    def get_domain_info(self) -> dict[str, Any]:
        """
        도메인 서버 정보 반환

        Returns:
            도메인 서버 정보 딕셔너리
        """
        return {
            "domain": self.domain_name,
            "server_name": self.server_name,
            "port": self.port,
            "mode": self.mode,
            "client_mode": self.client.mode if self.client else None,
            "verified_apis": list(self.api_verification_status.keys()),
            "timestamp": datetime.now().isoformat(),
        }

    def register_common_resources(self):
        """공통 리소스 등록 (하위 클래스에서 호출)"""
        # MCP 리소스 등록 로직
        # 예: self.mcp.add_resource(...)
        pass
