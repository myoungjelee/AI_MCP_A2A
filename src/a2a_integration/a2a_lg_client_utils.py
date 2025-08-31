"""A2A Client Utilities - A2A 클라이언트 0.3.0 기준 + A2A 호환 래퍼."""

import asyncio
import logging
import os
from typing import Any, Optional
from uuid import uuid4

import httpx
import structlog
from a2a.client import A2ACardResolver, A2AClientError, ClientConfig, ClientFactory
from a2a.client.auth.credentials import CredentialService
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    Part,
    Role,
    TaskIdParams,
    TransportProtocol,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

logger = structlog.get_logger(__name__)
wrapper_logger = logging.getLogger(__name__)


class A2AClientManager:
    """A2A 표준 클라이언트 관리 클래스.

    - 에이전트 카드 조회 및 A2A 클라이언트 초기화/종료 수명주기 관리
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        streaming: bool = False,
        max_retries: int = 2,
        retry_delay: float = 2.0,
        credential_service: Optional[CredentialService] = None,
    ):
        self.base_url = base_url
        self.streaming = streaming
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.credential_service = credential_service
        self.a2a_client = None
        self.agent_card: AgentCard | None = None
        self._httpx_client = None

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self) -> "A2AClientManager":
        """A2A 클라이언트를 초기화한다.

        - 원격 `/.well-known/agent-card.json`을 가져와 `AgentCard` 구성
        - 스트리밍/전송 프로토콜 설정 후 실제 전송 클라이언트 생성
        - 호출자는 컨텍스트 매니저(`async with`) 사용을 권장
        """
        try:
            logger.debug(f"Initializing A2A client for {self.base_url}")

            # HTTPX 클라이언트 생성
            self._httpx_client = httpx.AsyncClient(
                # 타임아웃 설정 - 스트리밍 모드를 위해 충분한 시간 확보
                timeout=httpx.Timeout(
                    connect=60.0,  # 연결 타임아웃
                    read=600.0,  # 읽기 타임아웃 - 10분
                    write=60.0,  # 쓰기 타임아웃
                    pool=600.0,  # 커넥션 풀 대기 타임아웃 - 10분
                ),
                limits=httpx.Limits(
                    max_connections=100,  # 최대 동시 연결 수
                    max_keepalive_connections=50,  # Keep-alive 연결 수
                    keepalive_expiry=60.0,  # Keep-alive 유지 시간 (초)
                ),
                follow_redirects=True,
                headers={
                    "User-Agent": "A2AClientManager/1.0",
                    "Accept": "application/json; charset=utf-8",
                    "Connection": "keep-alive",
                },
            )

            resolver = A2ACardResolver(
                httpx_client=self._httpx_client,
                base_url=self.base_url,
            )

            try:
                self.agent_card: AgentCard = await resolver.get_agent_card()
                logger.debug(f"Successfully fetched agent card: {self.agent_card.name}")

                # Docker 호스트명을 localhost로 변환 (로컬 개발 환경용)
                if self.agent_card.url and not os.getenv("IS_DOCKER", "false").lower() == "true":
                    docker_hosts = ["data-collector-agent", "analysis-agent", "trading-agent", "supervisor-agent"]
                    for docker_host in docker_hosts:
                        if docker_host in self.agent_card.url:
                            # NOTE: 로컬 개발 환경에서 사용하는 경우 컨테이너 이름을 localhost로 변환하여 호출.
                            self.agent_card.url = self.agent_card.url.replace(f"http://{docker_host}", "http://localhost")
                            logger.debug(f"Converted Docker URL to localhost: {self.agent_card.url}")
                            break
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching agent card: {e}")
                raise RuntimeError(
                    f"Failed to fetch agent card from {self.base_url}: {e}"
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error fetching agent card: {e}")
                raise RuntimeError(f"Failed to fetch agent card: {e}") from e

            # A2A클라이언트 세부 설정
            config = ClientConfig(
                streaming=self.streaming,
                httpx_client=self._httpx_client,
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                    TransportProtocol.grpc,
                ],
                accepted_output_modes=[
                    "text/plain",
                    "text/markdown",
                    "application/json",
                    "text/event-stream",
                ],
                use_client_preference=True,
            )
            factory = ClientFactory(config=config)

            # NOTE: 보안 인터셉터 추가 가능(Auth 구현 시 활용)
            interceptors = None
            if self.credential_service:
                from a2a.client.auth.interceptor import AuthInterceptor

                interceptors = [AuthInterceptor(self.credential_service)]
                logger.debug("Auth interceptor added")

            self.a2a_client = factory.create(
                card=self.agent_card,
                interceptors=interceptors,
            )
            logger.debug(f"A2A client created successfully for {self.agent_card.name}")

            return self

        except Exception as e:
            logger.error(f"Failed to initialize A2A client: {e}")
            if hasattr(self, "_httpx_client") and self._httpx_client:
                await self._httpx_client.aclose()
            raise

    async def get_agent_card(self) -> AgentCard:
        """초기화 시 획득한 `AgentCard`를 반환한다."""
        return self.agent_card

    async def close(self):
        """내부 HTTP 클라이언트를 정리한다."""
        if self._httpx_client:
            await self._httpx_client.aclose()
        if self.a2a_client:
            await self.a2a_client.close()

    async def health_check(self) -> bool:
        """에이전트 연결 상태를 확인한다.

        Returns:
            bool: 연결이 정상이면 True, 아니면 False
        """
        try:
            if not self._httpx_client:
                return False

            # Agent Card 엔드포인트로 헬스 체크
            response = await self._httpx_client.get(
                f"{self.base_url}{AGENT_CARD_WELL_KNOWN_PATH}",
                timeout=5.0,
                headers={
                    "User-Agent": "A2AClientManager/1.0",
                    "Accept": "application/json; charset=utf-8",
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed for {self.base_url}: {e}")
            return False

    async def ensure_connection(self):
        """연결 상태를 확인하고 필요시 재연결한다."""
        if not await self.health_check():
            logger.info(f"Connection lost to {self.base_url}, reconnecting...")
            await self.close()
            await self.initialize()

    def get_agent_info(self) -> dict[str, Any]:
        """에이전트 카드의 요약 정보를 딕셔너리로 반환한다.

        UI/로그 노출용으로 선별된 메타데이터만 포함한다.
        """
        return {
            "name": self.agent_card.name,
            "description": self.agent_card.description,
            "url": self.agent_card.url,
            "capabilities": self.agent_card.capabilities.model_dump(),
            "default_input_modes": self.agent_card.default_input_modes,
            "default_output_modes": self.agent_card.default_output_modes,
            "skills": [
                {"name": skill.name, "description": skill.description}
                for skill in self.agent_card.skills
            ],
        }

    async def _execute_with_retry(self, func, *args, **kwargs):
        """표준 A2A 에러 처리와 재시도 로직을 가진 래퍼.

        A2A 표준 에러 타입에 따라 적절한 재시도 정책 적용:
        - InvalidParamsError: 재시도 없음 (클라이언트 오류)
        - TaskNotFoundError: 재시도 없음 (리소스 없음)
        - InternalError/ServerError: max_retries 만큼 재시도
        - 기타 A2AClientError: max_retries 만큼 재시도
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except A2AClientError as e:
                # A2A 클라이언트 에러 (재시도 가능)
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"A2A 클라이언트 에러, 재시도 {attempt + 1}/{self.max_retries}: {e}"
                    )
                    await asyncio.sleep(self.retry_delay * (2**attempt))  # 지수 백오프
                else:
                    logger.error(f"최대 재시도 횟수 초과: {e}")
            except httpx.HTTPError as e:
                # HTTP 에러 (재시도 가능)
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"HTTP 에러, 재시도 {attempt + 1}/{self.max_retries}: {e}"
                    )
                    await asyncio.sleep(self.retry_delay * (2**attempt))  # 지수 백오프
                else:
                    logger.error(f"최대 재시도 횟수 초과: {e}")
            except ValueError as e:
                # 값 오류는 재시도 무의미
                logger.error(f"ValueError (재시도 없음): {e}")
                raise
            except Exception as e:
                # 예상치 못한 에러
                logger.error(f"예상치 못한 에러: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception module: {type(e).__module__}")
                import traceback

                logger.error(f"Traceback:\n{traceback.format_exc()}")
                # InternalError는 예외가 아닌 Pydantic 모델이므로 일반 Exception으로 재발생
                raise RuntimeError(f"Unexpected error in A2A client: {str(e)}") from e

        if last_error:
            raise last_error

        raise RuntimeError("알 수 없는 오류로 재시도 실패")

    async def cancel_task(self, task_id: str) -> None:
        """태스크를 취소합니다."""
        if not self.a2a_client:
            raise A2AClientError(
                "클라이언트가 초기화되지 않았습니다. initialize()를 먼저 호출하세요."
            )
        params = TaskIdParams(id=task_id)
        await self.a2a_client.cancel_task(params)

    def create_data_message_object(self, data: dict[str, Any]) -> Message:
        """Create a Message object containing a single DataPart.

        Args:
            data: The data content of the message.

        Returns:
            A `Message` object with a new UUID message_id.
        """
        return Message(
            role=Role.user, parts=[Part(DataPart(data=data))], message_id=str(uuid4())
        )

    def create_user_message(self, user_message: str | dict[str, Any]) -> Message:
        """사용자 메시지를 생성한다.

        Args:
            user_message: 사용자 메시지 문자열 또는 딕셔너리

        Returns:
        """
        if not isinstance(user_message, (str, dict)):
            raise ValueError("사용자 메시지는 문자열 또는 딕셔너리여야 합니다.")

        if isinstance(user_message, str):
            return create_text_message_object(content=user_message)
        elif isinstance(user_message, dict):
            return self.create_data_message_object(data=user_message)

    async def send_server_to_user_message(self, data: dict[str, Any]) -> Any:
        """Server에서 User로 메시지를 전송한다."""
        if not self.a2a_client:
            raise A2AClientError(
                "클라이언트가 초기화되지 않았습니다. initialize()를 먼저 호출하세요."
            )

        # TODO: 서버에서 원하는 데이터 스펙 찾기


