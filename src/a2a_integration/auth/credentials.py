"""A2A CredentialService 구현.

API Key, OAuth2, Bearer Token 등 다양한 인증 방식을 지원합니다.
"""

import os
from typing import Dict, Optional

import structlog
from a2a.client.auth.credentials import CredentialService
from a2a.server.context import ServerCallContext

logger = structlog.get_logger(__name__)


class SimpleCredentialService(CredentialService):
    """간단한 메모리 기반 CredentialService 구현.

    테스트 및 개발용으로 사용합니다.
    """

    def __init__(self):
        self._credentials: Dict[str, str] = {}

    def set_credential(self, security_scheme_name: str, credential: str) -> None:
        """보안 스킴에 대한 자격 증명을 설정합니다.

        Args:
            security_scheme_name: 보안 스킴 이름 (예: "bearer", "api_key")
            credential: 자격 증명 값 (토큰, API 키 등)
        """
        self._credentials[security_scheme_name] = credential
        logger.debug(f"Credential set for scheme: {security_scheme_name}")

    async def get_credentials(
        self,
        security_scheme_name: str,
        context: ServerCallContext,
    ) -> Optional[str]:
        """보안 스킴에 대한 자격 증명을 가져옵니다.

        Args:
            security_scheme_name: 보안 스킴 이름
            context: 서버 호출 컨텍스트

        Returns:
            자격 증명 문자열, 없으면 None
        """
        credential = self._credentials.get(security_scheme_name)
        if credential:
            logger.debug(f"Credential retrieved for scheme: {security_scheme_name}")
        else:
            logger.debug(f"No credential found for scheme: {security_scheme_name}")
        return credential

    def clear_credentials(self) -> None:
        """모든 자격 증명을 제거합니다."""
        self._credentials.clear()
        logger.debug("All credentials cleared")


class EnvCredentialService(CredentialService):
    """환경 변수 기반 CredentialService 구현.

    프로덕션 환경에서 안전하게 자격 증명을 관리합니다.

    환경 변수 규칙:
    - Bearer Token: A2A_BEARER_TOKEN
    - API Key: A2A_API_KEY
    - OAuth2 Client ID: A2A_OAUTH2_CLIENT_ID
    - OAuth2 Client Secret: A2A_OAUTH2_CLIENT_SECRET
    """

    # 환경 변수 매핑
    ENV_MAPPING = {
        "bearer": "A2A_BEARER_TOKEN",
        "api_key": "A2A_API_KEY",
        "oauth2_client_id": "A2A_OAUTH2_CLIENT_ID",
        "oauth2_client_secret": "A2A_OAUTH2_CLIENT_SECRET",
    }

    def __init__(self, env_prefix: str = "A2A"):
        """환경 변수 기반 CredentialService 초기화.

        Args:
            env_prefix: 환경 변수 접두사 (기본값: "A2A")
        """
        self.env_prefix = env_prefix
        self._load_credentials()

    def _load_credentials(self) -> None:
        """환경 변수에서 자격 증명을 로드합니다."""
        loaded_count = 0
        for scheme_name, env_var in self.ENV_MAPPING.items():
            if os.getenv(env_var):
                loaded_count += 1
                logger.debug(f"Credential loaded from {env_var} for scheme: {scheme_name}")

        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} credentials from environment variables")
        else:
            logger.warning("No credentials found in environment variables")

    async def get_credentials(
        self,
        security_scheme_name: str,
        context: ServerCallContext,
    ) -> Optional[str]:
        """환경 변수에서 보안 스킴에 대한 자격 증명을 가져옵니다.

        Args:
            security_scheme_name: 보안 스킴 이름
            context: 서버 호출 컨텍스트

        Returns:
            자격 증명 문자열, 없으면 None
        """
        # 직접 환경 변수 이름으로 시도
        env_var = self.ENV_MAPPING.get(security_scheme_name)
        if env_var:
            credential = os.getenv(env_var)
            if credential:
                logger.debug(f"Credential retrieved from {env_var}")
                return credential

        # 대문자 변환 시도
        upper_env_var = f"{self.env_prefix}_{security_scheme_name.upper()}"
        credential = os.getenv(upper_env_var)
        if credential:
            logger.debug(f"Credential retrieved from {upper_env_var}")
            return credential

        logger.debug(f"No credential found for scheme: {security_scheme_name}")
        return None


class CompositeCredentialService(CredentialService):
    """여러 CredentialService를 조합하는 복합 서비스.

    우선순위에 따라 여러 소스에서 자격 증명을 가져옵니다.
    """

    def __init__(self, services: list[CredentialService]):
        """복합 CredentialService 초기화.

        Args:
            services: 우선순위 순으로 정렬된 CredentialService 리스트
        """
        self.services = services

    async def get_credentials(
        self,
        security_scheme_name: str,
        context: ServerCallContext,
    ) -> Optional[str]:
        """여러 소스에서 순차적으로 자격 증명을 찾습니다.

        Args:
            security_scheme_name: 보안 스킴 이름
            context: 서버 호출 컨텍스트

        Returns:
            첫 번째로 발견된 자격 증명, 없으면 None
        """
        for service in self.services:
            credential = await service.get_credentials(security_scheme_name, context)
            if credential:
                logger.debug(
                    f"Credential found for {security_scheme_name} in {service.__class__.__name__}"
                )
                return credential

        logger.debug(f"No credential found for scheme: {security_scheme_name} in any service")
        return None
