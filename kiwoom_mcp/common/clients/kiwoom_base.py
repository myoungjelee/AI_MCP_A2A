from typing import Optional

from pydantic import BaseModel


class KiwoomAPIResponse(BaseModel):
    """키움 API 표준 응답 모델"""

    success: bool
    data: Optional[dict[str, any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    api_verified: bool = False  # API 검증 상태
    is_mock: bool = False  # Mock 데이터 여부

    def check_api_verification(self, api_id: str) -> dict[str, any]:
        """API 검증 상태 확인"""
        pass

    async def _get_access_token(self) -> str:
        """액세스 토큰 조회"""
        pass

    def _get_headers(
        self, api_id: str, cont_yn: Optional[str] = None, next_key: Optional[str] = None
    ) -> dict[str, str]:
        """API 호출용 헤더 생성"""
        pass

    async def _make_request(
        self,
        api_id: str,
        endpoint: str,
        data: dict[str, any],
        cont_yn: Optional[str] = None,
        next_key: Optional[str] = None,
    ) -> "KiwoomAPIResponse":
        """실제 API 요청 수행"""
        pass

    def _create_mock_response(
        self,
        api_id: str,
        request_data: dict[str, any],
        verification_info: dict[str, any],
    ) -> "KiwoomAPIResponse":
        """Mock 응답 생성"""
        pass

    def _generate_mock_data(
        self, api_id: str, request_data: dict[str, any]
    ) -> dict[str, any]:
        """Mock 데이터 생성"""
        pass
