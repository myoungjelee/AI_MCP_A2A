"""A2A Client Manager V2 - A2A 클라이언트.

A2A 표준 스펙에 충실하면서 사용하기 쉽고 안정적인 API를 제공합니다.
TextPart, DataPart, FilePart를 모두 지원.
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Union
from uuid import uuid4

import httpx
import structlog
from a2a.client import A2ACardResolver, A2AClientError, ClientConfig, ClientFactory
from a2a.client.auth.credentials import CredentialService
from a2a.client.helpers import create_text_message_object
from a2a.types import (
    AgentCard,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    Role,
    TextPart,
    TransportProtocol,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from src.lg_agents.base.a2a_interface import A2AOutput

logger = structlog.get_logger(__name__)
wrapper_logger = logging.getLogger(__name__)

# ==================== Response Types ====================

@dataclass
class TextResponse:
    """텍스트 전송 응답."""
    text: str
    streaming_chunks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_count: int = 0


@dataclass
class DataResponse:
    """데이터 전송 응답."""
    data_parts: List[Dict[str, Any]]
    merged_data: Optional[Dict[str, Any]] = None
    validation_errors: List[str] = field(default_factory=list)
    event_count: int = 0


@dataclass
class FileResponse:
    """파일 전송 응답."""
    file_uri: Optional[str] = None
    file_bytes: Optional[bytes] = None
    mime_type: str = "application/octet-stream"
    size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedResponse:
    """통합 응답 - 모든 Part 타입 포함."""
    text_parts: List[str] = field(default_factory=list)
    data_parts: List[Dict[str, Any]] = field(default_factory=list)
    file_parts: List[FileResponse] = field(default_factory=list)
    merged_text: str = ""
    merged_data: Optional[Dict[str, Any]] = None
    history: Optional[List[Message]] = None
    event_count: int = 0
    errors: List['PartError'] = field(default_factory=list)


@dataclass
class PartError:
    """Part 처리 중 발생한 에러."""
    part_type: Literal["text", "data", "file"]
    error: Exception
    retry_count: int = 0
    recoverable: bool = True


class ErrorStrategy(Enum):
    """에러 처리 전략."""
    FAIL_FAST = "fail_fast"          # 첫 에러 시 중단
    CONTINUE_ON_ERROR = "continue"    # 에러 무시하고 계속
    PARTIAL_SUCCESS = "partial"       # 성공한 것만 반환


# ==================== Core Engine ====================

class A2AMessageEngine:
    """A2A 메시지 처리 엔진.

    모든 메시지 전송, 이벤트 처리, 재시도 로직을 담당합니다.
    """

    def __init__(
        self,
        base_url: str,
        streaming: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        credential_service: Optional[CredentialService] = None,
    ):
        self.base_url = base_url
        self.streaming = streaming
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.credential_service = credential_service
        self.client = None
        self.agent_card: Optional[AgentCard] = None
        self._httpx_client = None

        # Task ID 캐싱 및 중복 방지를 위한 새로운 속성들
        self.task_cache: Dict[str, str] = {}  # {request_hash: task_id}
        self.current_task_id: Optional[str] = None  # 현재 실행 중인 task_id

    async def initialize(self) -> 'A2AMessageEngine':
        """엔진을 초기화합니다."""
        try:
            logger.debug(f"Initializing A2A engine for {self.base_url}")

            # HTTPX 클라이언트 생성
            self._httpx_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=60.0,
                    read=600.0,
                    write=60.0,
                    pool=600.0,
                ),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=50,
                    keepalive_expiry=60.0,
                ),
                follow_redirects=True,
                headers={
                    "User-Agent": "A2AClientManager/2.0",
                    "Accept": "application/json; charset=utf-8",
                    "Connection": "keep-alive",
                },
            )

            # Agent Card 가져오기
            resolver = A2ACardResolver(
                httpx_client=self._httpx_client,
                base_url=self.base_url,
            )

            self.agent_card = await resolver.get_agent_card()
            logger.debug(f"Successfully fetched agent card: {self.agent_card.name}")

            # Docker 호스트명 변환 (로컬 개발용)
            if self.agent_card.url and not os.getenv("IS_DOCKER", "false").lower() == "true":
                docker_hosts = ["data-collector-agent", "analysis-agent", "trading-agent", "supervisor-agent"]
                for docker_host in docker_hosts:
                    if docker_host in self.agent_card.url:
                        self.agent_card.url = self.agent_card.url.replace(f"http://{docker_host}", "http://localhost")
                        logger.debug(f"Converted Docker URL to localhost: {self.agent_card.url}")
                        break

            # A2A 클라이언트 설정
            config = ClientConfig(
                streaming=self.streaming,
                polling=not self.streaming,
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

            # 인터셉터 추가 (인증이 필요한 경우)
            interceptors = []
            if self.credential_service:
                from a2a.client.auth.interceptor import AuthInterceptor
                interceptors.append(AuthInterceptor(self.credential_service))
                logger.debug("Auth interceptor added")

            self.client = factory.create(
                card=self.agent_card,
                interceptors=interceptors,
            )

            logger.debug(f"A2A client created successfully for {self.agent_card.name}")
            return self

        except Exception as e:
            logger.error(f"Failed to initialize A2A engine: {e}")
            if self._httpx_client:
                await self._httpx_client.aclose()
            raise

    async def close(self):
        """리소스를 정리합니다."""
        if self._httpx_client:
            await self._httpx_client.aclose()
        if self.client:
            await self.client.close()

    async def send_message_core(
        self,
        message: Message,
        process_callback: Optional[Callable] = None,
    ) -> UnifiedResponse:
        """핵심 메시지 전송 메서드 (Task ID 캐싱 및 중복 방지 포함).

        Args:
            message: 전송할 Message 객체
            process_callback: 각 이벤트 처리 시 호출할 콜백

        Returns:
            UnifiedResponse: 통합된 응답
        """
        if not self.client:
            raise ValueError("Engine not initialized. Call initialize() first.")

        response = UnifiedResponse()
        text_accumulator = ""

        # Step 1: Task 캐싱 비활성화 - 항상 새 task 생성
        # 이유: GetTask API가 완료된 task의 artifacts/history를 완전히 가져오지 못하는 문제 때문
        logger.info("Creating new task (caching disabled to prevent data loss)")

        # Step 2: 항상 새로운 task 생성
        logger.info("Creating new task - sending message")

        # 메시지 해시 생성 (새 task를 캐시하기 위해)
        request_hash = self._generate_request_hash(message)

        event_counter = 0
        task_id = None

        # 이벤트 스트리밍 처리
        logger.info("Starting event loop for NEW message processing")
        async for event in self.client.send_message(message):
            event_counter += 1
            logger.info(f"Received event #{event_counter}: {type(event)}")

            # Task ID 추출 및 캐시 저장
            if isinstance(event, tuple) and len(event) > 0:
                task = event[0]
                if hasattr(task, 'id'):
                    task_id = task.id
                    self.current_task_id = task_id
                    # 새로운 task_id를 캐시에 저장
                    self.task_cache[request_hash] = task_id
                    logger.info(f"Cached new task_id: {task_id} with hash: {request_hash}")

            event_data = await self._process_event(event)

            # 텍스트 누적
            if event_data.get("text"):
                new_text = self._merge_incremental_text(text_accumulator, event_data["text"])
                if new_text != text_accumulator:
                    delta = new_text[len(text_accumulator):]
                    if delta:
                        response.text_parts.append(delta)
                        if process_callback:
                            await process_callback({"type": "text", "content": delta})
                    text_accumulator = new_text

            # 데이터 수집
            if event_data.get("data"):
                response.data_parts.append(event_data["data"])
                if process_callback:
                    await process_callback({"type": "data", "content": event_data["data"]})

            # TODO: 파일 처리 (추후 구현)
            # if event_data.get("file"):
            #     file_resp = FileResponse(
            #         file_uri=event_data["file"].get("uri"),
            #         file_bytes=event_data["file"].get("bytes"),
            #         mime_type=event_data["file"].get("mime_type", "application/octet-stream"),
            #     )
            #     response.file_parts.append(file_resp)
            #     if process_callback:
            #         await process_callback({"type": "file", "content": file_resp})

            response.event_count += 1

        logger.info(f"Event loop completed. Total events processed: {event_counter}")

        # FIX: Always poll for task completion to ensure complete data retrieval
        if task_id:
            logger.info(f"Always polling for NEW task completion (task_id: {task_id})")

            completed_task = await self._wait_for_task_completion(task_id)

            if completed_task:
                text_accumulator = await self._extract_task_results(completed_task, response, text_accumulator)
            else:
                logger.warning("NEW task completion polling failed")

        # 최종 텍스트 병합
        response.merged_text = text_accumulator.strip()
        if response.data_parts:
            response.merged_data = self._merge_data_parts(response.data_parts)

        logger.info(f"Successfully completed NEW task processing: {task_id}")
        return response

    async def _process_event(self, event) -> Dict[str, Any]:
        """단일 이벤트를 처리하여 Part들을 추출합니다."""
        result = {}

        # 이벤트 구조 로깅
        logger.info(f"Raw event type: {type(event)}, length: {len(event) if isinstance(event, (tuple, list)) else 'N/A'}")

        if not isinstance(event, tuple) or len(event) < 1:
            logger.info("Invalid event format, returning empty result")
            return result

        task = event[0]
        logger.info(f"Task type: {type(task)}, has artifacts: {hasattr(task, 'artifacts')}, has history: {hasattr(task, 'history')}")

        # Artifacts에서 Part 추출
        if hasattr(task, "artifacts") and task.artifacts:
            logger.info(f"Found {len(task.artifacts)} artifacts")
            for i, artifact in enumerate(task.artifacts):
                logger.info(f"Artifact {i}: has parts: {hasattr(artifact, 'parts')}, parts length: {len(artifact.parts) if hasattr(artifact, 'parts') and artifact.parts else 0}")
                if hasattr(artifact, "parts") and artifact.parts:
                    for j, part in enumerate(artifact.parts):
                        root = getattr(part, "root", None)
                        logger.info(f"Part {j}: root type: {type(root)}, has text: {hasattr(root, 'text') if root else False}, has data: {hasattr(root, 'data') if root else False}")
                        if root:
                            # TextPart
                            if hasattr(root, "text") and root.text:
                                result["text"] = root.text
                                logger.info(f"Extracted TextPart, length: {len(root.text)}")
                            # DataPart
                            elif hasattr(root, "data") and root.data:
                                result["data"] = root.data
                                logger.info(f"Extracted DataPart, type: {type(root.data)}")
                            # FilePart
                            elif hasattr(root, "kind") and root.kind == "file":
                                result["file"] = {
                                    "uri": getattr(root, "file_with_uri", None),
                                    "bytes": getattr(root, "file_with_bytes", None),
                                    "mime_type": getattr(root, "mime_type", "application/octet-stream"),
                                }
                                logger.info("Extracted FilePart")

        # History에서 Part 추출 (artifacts가 없는 경우)
        elif hasattr(task, "history") and task.history:
            logger.info(f"Found history with {len(task.history)} messages")
            last_message = task.history[-1]
            logger.info(f"Last message role: {last_message.role.value if hasattr(last_message, 'role') else 'no role'}")
            if hasattr(last_message, "role") and last_message.role.value == "agent":
                if hasattr(last_message, "parts") and last_message.parts:
                    logger.info(f"Agent message has {len(last_message.parts)} parts")
                    for j, part in enumerate(last_message.parts):
                        root = getattr(part, "root", None)
                        logger.info(f"History Part {j}: root type: {type(root)}, has text: {hasattr(root, 'text') if root else False}, has data: {hasattr(root, 'data') if root else False}")
                        if root:
                            if hasattr(root, "text") and root.text:
                                result["text"] = root.text
                                logger.info(f"Extracted TextPart from history, length: {len(root.text)}")
                            elif hasattr(root, "data") and root.data:
                                result["data"] = root.data
                                logger.info(f"Extracted DataPart from history, type: {type(root.data)}")
        else:
            logger.info("No artifacts or history found in task")

        logger.info(f"Event processing result: {result}")
        return result

    def _merge_incremental_text(self, existing: str, new: str) -> str:
        """증분 텍스트를 병합합니다."""
        if not existing:
            return new
        if new.startswith(existing):
            return new
        if existing.startswith(new):
            return existing

        # 겹치는 부분 찾기
        max_overlap = min(len(existing), len(new))
        overlap = 0
        for k in range(max_overlap, 0, -1):
            if existing.endswith(new[:k]):
                overlap = k
                break

        return existing + new[overlap:]

    def _merge_data_parts(
        self,
        parts: List[Dict[str, Any]],
        mode: str = "smart"
    ) -> Dict[str, Any]:
        """여러 DataPart를 하나로 병합합니다."""
        if not parts:
            return {}

        if mode == "last":
            return parts[-1] if parts else {}

        # Smart merge
        result = {}
        for part in parts:
            if not isinstance(part, dict):
                continue

            for key, value in part.items():
                if key not in result:
                    result[key] = value
                elif isinstance(result[key], list) and isinstance(value, list):
                    # 리스트는 합치고 중복 제거
                    combined = result[key] + value
                    seen = set()
                    deduped = []
                    for item in combined:
                        item_key = str(item) if not isinstance(item, dict) else json.dumps(item, sort_keys=True)
                        if item_key not in seen:
                            seen.add(item_key)
                            deduped.append(item)
                    result[key] = deduped
                elif isinstance(result[key], dict) and isinstance(value, dict):
                    # 딕셔너리는 재귀적으로 병합
                    result[key] = self._merge_data_parts([result[key], value], mode)
                else:
                    # 그 외는 마지막 값 우선
                    result[key] = value

        return result

    async def execute_with_retry(self, func, *args, **kwargs):
        """재시도 로직을 적용하여 함수를 실행합니다."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except A2AClientError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"A2A client error, retry {attempt + 1}/{self.max_retries}: {e}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Max retries exceeded: {e}")
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"HTTP error, retry {attempt + 1}/{self.max_retries}: {e}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Max retries exceeded: {e}")
            except ValueError as e:
                # 값 오류는 재시도 무의미
                logger.error(f"ValueError (no retry): {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise RuntimeError(f"Unexpected error in A2A client: {str(e)}") from e

        if last_error:
            raise last_error

        raise RuntimeError("Unknown error after retries")

    # ==================== Task ID 캐싱 및 중복 방지 메서드들 ====================

    def _generate_request_hash(self, message: Message) -> str:
        """메시지 내용을 기반으로 고유한 해시를 생성합니다."""
        try:
            # 메시지의 핵심 내용들을 추출하여 해시 생성
            content_parts = []

            if hasattr(message, 'parts') and message.parts:
                for part in message.parts:
                    if hasattr(part, 'root'):
                        root = part.root
                        if hasattr(root, 'text') and root.text:
                            content_parts.append(f"text:{root.text}")
                        elif hasattr(root, 'data') and root.data:
                            content_parts.append(f"data:{json.dumps(root.data, sort_keys=True)}")
                        elif hasattr(root, 'file'):
                            # 파일의 경우 URI나 이름 등 식별 가능한 정보 사용
                            file_info = root.file
                            if hasattr(file_info, 'uri') and file_info.uri:
                                content_parts.append(f"file_uri:{file_info.uri}")
                            elif hasattr(file_info, 'name') and file_info.name:
                                content_parts.append(f"file_name:{file_info.name}")

            # 내용이 없다면 빈 문자열 해시
            content_string = "|".join(content_parts) if content_parts else "empty_message"

            # SHA256 해시 생성 (짧게 truncate)
            hash_object = hashlib.sha256(content_string.encode('utf-8'))
            return hash_object.hexdigest()[:16]  # 16자리로 축약

        except Exception as e:
            logger.warning(f"Failed to generate request hash: {e}")
            # fallback으로 현재 시간 기반 해시 생성
            import time
            return hashlib.sha256(f"fallback_{time.time()}".encode()).hexdigest()[:16]

    async def _get_task_direct(self, task_id: str) -> Optional[Any]:
        """GetTask API를 직접 호출하여 task 정보를 가져옵니다 (새 메시지 생성 안 함)."""
        try:
            from a2a.types import TaskQueryParams

            logger.info(f"Direct GetTask API call for task_id: {task_id}")

            # ClientTaskManager
            query_params = TaskQueryParams(id=task_id, history_length=20)

            # Transport layer를 통한 직접 호출 시도
            if hasattr(self.client, '_transport') and hasattr(self.client._transport, 'get_task'):
                task = await self.client._transport.get_task(query_params)
                logger.info(f"Successfully retrieved task via transport layer: {task_id}")
                return task
            else:
                # Fallback: client.get_task 사용 (다만 이것도 새 메시지를 생성할 가능성이 있음)
                logger.warning("Transport layer not available, using client.get_task as fallback")
                task = await self.client.get_task(query_params)
                return task

        except Exception as e:
            logger.error(f"Direct GetTask failed for {task_id}: {e}")
            return None

    async def _get_or_create_task_id(self, message: Message) -> tuple[Optional[str], bool]:
        """기존 task_id를 찾거나 새로 생성합니다.

        Returns:
            tuple[Optional[str], bool]: (task_id, is_new_task)
        """
        try:
            # 메시지 해시 생성
            request_hash = self._generate_request_hash(message)
            logger.info(f"Generated request hash: {request_hash}")

            # 캐시에서 기존 task_id 확인
            if request_hash in self.task_cache:
                existing_task_id = self.task_cache[request_hash]
                logger.info(f"Found existing task_id in cache: {existing_task_id}")

                # 기존 task가 여전히 유효한지 확인
                existing_task = await self._get_task_direct(existing_task_id)
                if existing_task:
                    # Task 상태 확인
                    task_status_obj = getattr(existing_task, 'status', None)
                    if task_status_obj:
                        current_state = getattr(task_status_obj, 'state', None)
                        state_str = str(current_state).lower() if current_state else ""

                        # 완료된 task라면 재사용 가능
                        if 'completed' in state_str or 'failed' in state_str or 'cancelled' in state_str:
                            logger.info(f"Reusing completed task: {existing_task_id}")
                            return existing_task_id, False
                        elif 'working' in state_str or 'running' in state_str:
                            logger.info(f"Found running task, will wait for completion: {existing_task_id}")
                            return existing_task_id, False

                # 유효하지 않은 task라면 캐시에서 제거
                logger.warning(f"Removing invalid task from cache: {existing_task_id}")
                del self.task_cache[request_hash]

            # 새로운 task가 필요함
            logger.info("No existing valid task found, will create new one")
            return None, True

        except Exception as e:
            logger.error(f"Error in _get_or_create_task_id: {e}")
            # 에러가 발생하면 새 task 생성으로 fallback
            return None, True

    async def _wait_for_task_completion(self, task_id: str, max_wait: int = 120, poll_interval: float = 10.0) -> Optional[Any]:
        """Task 완료 polling (직접 GetTask API 사용)."""
        logger.info(f"Task completion polling for task {task_id} (max_wait: {max_wait}s)")

        consecutive_failures = 0
        max_consecutive_failures = 5

        for attempt in range(int(max_wait / poll_interval)):
            try:
                # 직접 GetTask API 호출
                task = await self._get_task_direct(task_id)
                if not task:
                    consecutive_failures += 1
                    logger.warning(f"Could not retrieve task {task_id}, attempt {attempt + 1}")

                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"Too many consecutive failures retrieving task {task_id}")
                        return None

                    await asyncio.sleep(poll_interval * (1 + consecutive_failures * 0.5))
                    continue

                consecutive_failures = 0  # 성공 시 리셋

                # Task 상태 확인
                task_status_obj = getattr(task, 'status', None)
                logger.info(f"Task status object: {task_status_obj}")
                if task_status_obj:
                    current_state = getattr(task_status_obj, 'state', None)
                    state_str = str(current_state).lower() if current_state else ""

                    logger.info(f"Attempt {attempt + 1}: Task {task_id} state: {current_state} state_str: {state_str}")

                    if 'completed' in state_str:
                        # logger.info(f"Task {task_id} completed successfully after {attempt + 1} attempts")
                        return task
                    elif 'failed' in state_str or 'cancelled' in state_str:
                        # logger.warning(f"Task {task_id} failed or cancelled")
                        return task  # 실패한 task도 반환하여 에러 정보 추출 가능
                    elif 'working' in state_str or 'running' in state_str:
                        # logger.debug(f"Task {task_id} still in progress...")
                        pass
                    else:
                        # 알 수 없는 상태면 내용이 있는지 확인
                        if hasattr(task, 'artifacts') and task.artifacts:
                            logger.info(f"Task {task_id} has artifacts despite unknown state - assuming completed")
                            return task
                        elif hasattr(task, 'history') and task.history:
                            for msg in task.history:
                                if hasattr(msg, 'role') and str(msg.role).lower() == 'agent':
                                    logger.info(f"Task {task_id} has agent messages - assuming completed")
                                    return task

                await asyncio.sleep(poll_interval)

            except Exception as e:
                consecutive_failures += 1
                logger.warning(f"Enhanced polling attempt {attempt + 1} failed: {e}")

                if consecutive_failures >= max_consecutive_failures:
                    logger.error("Too many consecutive polling failures, giving up")
                    return None

                await asyncio.sleep(poll_interval * (1 + consecutive_failures * 0.5))

        logger.warning(f"Enhanced task completion polling timed out after {max_wait}s")
        return None

    async def _extract_task_results(self, task: Any, response: UnifiedResponse, text_accumulator: str) -> str:
        """Task에서 결과를 추출하여 response에 저장합니다.

        Returns:
            str: 업데이트된 text_accumulator
        """
        try:
            logger.info("Extracting results from completed task")

            # Artifacts에서 데이터 추출 (우선순위 높음)
            if hasattr(task, 'artifacts') and task.artifacts:
                logger.info(f"Found {len(task.artifacts)} artifacts")
                for artifact in task.artifacts:
                    if hasattr(artifact, 'parts') and artifact.parts:
                        for part in artifact.parts:
                            root = getattr(part, 'root', None)
                            if root:
                                if hasattr(root, 'text') and root.text:
                                    # Authoritative text from artifacts
                                    response.text_parts = [root.text]
                                    text_accumulator = root.text
                                    logger.info(f"Extracted authoritative text: {len(root.text)} chars")
                                elif hasattr(root, 'data') and root.data:
                                    # Authoritative data from artifacts
                                    response.data_parts = [root.data]
                                    logger.info("Extracted authoritative data from artifacts")

            # History에서 데이터 추출 (fallback)
            if hasattr(task, 'history') and task.history and not response.text_parts and not response.data_parts:
                logger.info("No artifacts found, extracting from history")
                for msg in reversed(task.history):
                    if hasattr(msg, 'role') and str(msg.role).lower() == 'agent':
                        if hasattr(msg, 'parts') and msg.parts:
                            for part in msg.parts:
                                root = getattr(part, 'root', None)
                                if root:
                                    if hasattr(root, 'text') and root.text:
                                        response.text_parts.append(root.text)
                                        text_accumulator = root.text
                                        logger.info(f"Extracted text from history: {len(root.text)} chars")
                                    elif hasattr(root, 'data') and root.data:
                                        response.data_parts.append(root.data)
                                        logger.info("Extracted data from history")
                        break  # 첫 번째 agent 메시지만 사용

            logger.info(f"Task result extraction complete - text parts: {len(response.text_parts)}, data parts: {len(response.data_parts)}")
            return text_accumulator

        except Exception as e:
            logger.error(f"Error extracting task results: {e}")
            return text_accumulator


# ==================== Specialized Clients ====================

class A2ATextClient:
    """텍스트 전송 특화 클라이언트."""

    def __init__(self, engine: A2AMessageEngine):
        self.engine = engine

    async def send(
        self,
        text: str,
        streaming_callback: Optional[Callable] = None,
    ) -> TextResponse:
        """텍스트를 전송합니다."""
        message = create_text_message_object(
            role=Role.user,
            content=text,
        )

        # 엔진을 통해 전송
        unified = await self.engine.execute_with_retry(
            self.engine.send_message_core,
            message,
            streaming_callback,
        )

        # TextResponse로 변환
        return TextResponse(
            text=unified.merged_text,
            streaming_chunks=unified.text_parts,
            event_count=unified.event_count,
        )


class A2ADataClient:
    """데이터 전송 특화 클라이언트."""

    def __init__(self, engine: A2AMessageEngine):
        self.engine = engine

    async def send(
        self,
        data: Dict[str, Any],
        merge_mode: str = "smart",
        streaming_callback: Optional[Callable] = None,
    ) -> DataResponse:
        """구조화된 데이터를 전송합니다."""
        # DataPart로 Message 생성 (dictionary 객체를 직접 전달)
        message = Message(
            role=Role.user,
            parts=[Part(root=DataPart(data=data))],
            message_id=str(uuid4()),
        )

        # 엔진을 통해 전송
        unified = await self.engine.execute_with_retry(
            self.engine.send_message_core,
            message,
            streaming_callback,
        )

        # DataResponse로 변환
        return DataResponse(
            data_parts=unified.data_parts,
            merged_data=unified.merged_data if merge_mode != "none" else None,
            event_count=unified.event_count,
        )


class A2AFileClient:
    """파일 전송 특화 클라이언트."""

    def __init__(self, engine: A2AMessageEngine):
        self.engine = engine

    async def send(
        self,
        file: Union[bytes, str, Path],
        mime_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileResponse:
        """파일을 전송합니다."""
        # FilePart 생성
        if isinstance(file, (str, Path)):
            # 파일 경로인 경우
            file_path = Path(file)
            if file_path.exists():
                file_with_uri = FileWithUri(uri=str(file_path.absolute()), mime_type=mime_type)
                file_part = FilePart(file=file_with_uri)
            else:
                raise FileNotFoundError(f"File not found: {file}")
        else:
            # 바이트 데이터인 경우
            file_with_bytes = FileWithBytes(bytes=file, mime_type=mime_type)
            file_part = FilePart(file=file_with_bytes)

        # Message 생성
        message = Message(
            role=Role.user,
            parts=[Part(root=file_part)],
            message_id=str(uuid4()),
        )

        # 엔진을 통해 전송
        unified = await self.engine.execute_with_retry(
            self.engine.send_message_core,
            message,
        )

        # FileResponse로 변환
        if unified.file_parts:
            return unified.file_parts[0]
        else:
            return FileResponse(mime_type=mime_type, metadata=metadata or {})


# ==================== Unified Manager (Legacy Compatible) ====================

class A2AClientManagerV2:
    """A2A 클라이언트 통합 관리자 V2.

    기존 A2AClientManager와 100% API 호환을 유지하면서
    내부적으로는 개선된 구조를 사용합니다.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        streaming: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        credential_service: Optional[CredentialService] = None,
    ):
        # 엔진 초기화
        self.engine = A2AMessageEngine(
            base_url=base_url,
            streaming=streaming,
            max_retries=max_retries,
            retry_delay=retry_delay,
            credential_service=credential_service,
        )

        # 전문 클라이언트 초기화
        self.text_client = A2ATextClient(self.engine)
        self.data_client = A2ADataClient(self.engine)
        self.file_client = A2AFileClient(self.engine)

        # 레거시 호환성을 위한 속성들
        self.base_url = base_url
        self.streaming = streaming
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.credential_service = credential_service
        self.client = None  # engine.client로 대체
        self.agent_card = None  # engine.agent_card로 대체
        self._httpx_client = None  # engine._httpx_client로 대체

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self) -> 'A2AClientManagerV2':
        """클라이언트를 초기화합니다."""
        await self.engine.initialize()

        # 레거시 호환성을 위한 속성 매핑
        self.client = self.engine.client
        self.agent_card = self.engine.agent_card
        self._httpx_client = self.engine._httpx_client

        return self

    async def close(self):
        """리소스를 정리합니다."""
        await self.engine.close()

    async def get_agent_card(self) -> AgentCard:
        """Agent Card를 반환합니다."""
        return self.engine.agent_card

    def get_agent_info(self) -> Dict[str, Any]:
        """Agent 정보를 반환합니다."""
        if not self.engine.agent_card:
            return {}

        return {
            "name": self.engine.agent_card.name,
            "description": self.engine.agent_card.description,
            "url": self.engine.agent_card.url,
            "capabilities": self.engine.agent_card.capabilities.model_dump(),
            "default_input_modes": self.engine.agent_card.default_input_modes,
            "default_output_modes": self.engine.agent_card.default_output_modes,
            "skills": [
                {"name": skill.name, "description": skill.description}
                for skill in self.engine.agent_card.skills
            ],
        }

    async def health_check(self) -> bool:
        """연결 상태를 확인합니다."""
        try:
            if not self.engine._httpx_client:
                return False

            response = await self.engine._httpx_client.get(
                f"{self.base_url}{AGENT_CARD_WELL_KNOWN_PATH}",
                timeout=5.0,
                headers={
                    "User-Agent": "A2AClientManager/2.0",
                    "Accept": "application/json; charset=utf-8",
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed for {self.base_url}: {e}")
            return False

    async def ensure_connection(self):
        """연결 상태를 확인하고 필요시 재연결합니다."""
        if not await self.health_check():
            logger.info(f"Connection lost to {self.base_url}, reconnecting...")
            await self.close()
            await self.initialize()

    # ==================== Legacy Compatible Methods ====================

    async def send_query(self, user_query: str) -> str:
        """텍스트 질의를 전송합니다. (레거시 호환)

        Args:
            user_query: 전송할 텍스트

        Returns:
            str: 응답 텍스트
        """
        response = await self.text_client.send(user_query)
        return response.text

    async def send_data(self, data: Dict[str, Any]) -> dict[str, Any]:
        """데이터를 전송합니다.

        Args:
            data: 전송할 데이터

        Returns:
            List[Dict]: DataPart 리스트
        """
        response = await self.data_client.send(data)
        return asdict(response)

    async def send_data_with_full_messages(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터를 전송하고 전체 메시지 히스토리를 반환합니다. (레거시 호환)

        Args:
            data: 전송할 데이터

        Returns:
            Dict: data_parts와 history를 포함한 딕셔너리
        """
        # 일단 기본 구현 - 추후 히스토리 수집 로직 추가
        response = await self.data_client.send(data)

        return {
            "data_parts": response.data_parts,
            "full_message_history": [],  # TODO: 히스토리 수집 구현
            "streaming_text": "",
            "event_count": response.event_count,
        }

    async def send_data_merged(
        self,
        data: Dict[str, Any],
        merge_mode: str = "smart"
    ) -> Dict[str, Any]:
        """데이터를 전송하고 병합된 결과를 반환합니다. (레거시 호환)

        Args:
            data: 전송할 데이터
            merge_mode: 병합 모드

        Returns:
            Dict: 병합된 데이터
        """
        response = await self.data_client.send(data, merge_mode=merge_mode)
        return response.merged_data or {}

    # ==================== New Unified Methods ====================

    async def send_parts(
        self,
        parts: List[Part],
        include_history: bool = False,
        error_strategy: ErrorStrategy = ErrorStrategy.FAIL_FAST,
    ) -> UnifiedResponse:
        """여러 Part를 한 번에 전송합니다.

        Args:
            parts: 전송할 Part 리스트
            include_history: 히스토리 포함 여부
            error_strategy: 에러 처리 전략

        Returns:
            UnifiedResponse: 통합 응답
        """
        # Message 생성
        message = Message(
            role=Role.user,
            parts=parts,
            message_id=str(uuid4()),
        )

        # 엔진을 통해 전송
        response = await self.engine.execute_with_retry(
            self.engine.send_message_core,
            message,
        )

        # TODO: include_history, error_strategy 구현

        return response

    async def send_text(self, text: str, **options) -> TextResponse:
        """텍스트를 전송합니다. (새 API)"""
        return await self.text_client.send(text, **options)

    async def send_file(
        self,
        file: Union[bytes, str, Path],
        mime_type: str = "application/octet-stream",
        **options
    ) -> FileResponse:
        """파일을 전송합니다. (새 API)"""
        return await self.file_client.send(file, mime_type, **options)


# ==================== A2A Interface Integration ====================

def convert_a2a_output_to_message(output: A2AOutput) -> Message:
    """
    Convert A2AOutput from LangGraph agents to A2A Message.

    Args:
        output: Standardized A2AOutput from agent

    Returns:
        Message: A2A protocol message
    """
    parts = []

    # Add text part if present
    text_content = output.get("text_content")
    if text_content:
        parts.append(Part(root=TextPart(text=text_content)))

    # Add data part if present
    data_content = output.get("data_content")
    if data_content:
        parts.append(Part(root=DataPart(data=data_content)))

    # Determine role based on agent type
    agent_type = output.get("agent_type", "unknown")
    role = Role.assistant if agent_type != "user" else Role.user

    # Create message with metadata
    message = Message(
        role=role,
        parts=parts,
        message_id=str(uuid4()),
        metadata=output.get("metadata", {})
    )

    return message


def convert_a2a_output_to_parts(output: A2AOutput) -> List[Part]:
    """
    Convert A2AOutput to A2A Parts for flexible message construction.

    Args:
        output: Standardized A2AOutput from agent

    Returns:
        List[Part]: A2A protocol parts
    """
    parts = []

    # Add text part if present
    text_content = output.get("text_content")
    if text_content:
        parts.append(Part(root=TextPart(text=text_content)))

    # Add data part if present
    data_content = output.get("data_content")
    if data_content:
        parts.append(Part(root=DataPart(data=data_content)))

    return parts


async def send_a2a_output(
    client_manager: 'A2AClientManagerV2',
    output: A2AOutput,
    streaming_callback: Optional[Callable] = None
) -> UnifiedResponse:
    """
    Send A2AOutput through A2A client.

    Args:
        client_manager: Initialized A2A client manager
        output: Standardized A2AOutput from agent
        streaming_callback: Optional callback for streaming

    Returns:
        UnifiedResponse: Response from A2A server
    """
    # Convert to message
    message = convert_a2a_output_to_message(output)

    # Send through engine
    return await client_manager.engine.send_message_core(
        message,
        streaming_callback
    )


class A2AOutputProcessor:
    """
    Helper class for processing A2AOutput streams.

    This class helps aggregate streaming A2AOutputs and extract final results.
    """

    def __init__(self):
        self.text_buffer = []
        self.data_parts = []
        self.final_output = None
        self.metadata = {}

    def process_output(self, output: A2AOutput):
        """Process a single A2AOutput."""
        # Accumulate text
        if output.get("text_content"):
            self.text_buffer.append(output["text_content"])

        # Collect data parts
        if output.get("data_content"):
            self.data_parts.append(output["data_content"])

        # Update metadata
        if output.get("metadata"):
            self.metadata.update(output["metadata"])

        # Check if final
        if output.get("final", False):
            self.final_output = output

    def get_merged_text(self) -> str:
        """Get merged text from all outputs."""
        return "".join(self.text_buffer)

    def get_merged_data(self) -> Dict[str, Any]:
        """Get merged data from all outputs."""
        if not self.data_parts:
            return {}

        # Simple merge strategy - later parts override earlier ones
        merged = {}
        for part in self.data_parts:
            if isinstance(part, dict):
                merged.update(part)

        return merged

    def get_final_result(self) -> Dict[str, Any]:
        """Get final aggregated result."""
        return {
            "text": self.get_merged_text(),
            "data": self.get_merged_data(),
            "metadata": self.metadata,
            "final_output": self.final_output
        }
