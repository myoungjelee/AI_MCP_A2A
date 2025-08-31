"""
공통 A2A 서버 유틸리티 (LangGraph 전용).

어떤 LangGraph 그래프(CompiledStateGraph)든 최소한의 코드로
A2A 서버를 구성할 수 있도록 헬퍼 함수들을 제공합니다.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

import httpx
import structlog
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AFastAPIApplication, A2AStarletteApplication
from a2a.server.apps.jsonrpc.jsonrpc_app import (
    JSONRPCApplication,
)
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from langgraph.graph.state import CompiledStateGraph

from src.a2a_integration.executor import LangGraphAgentExecutor
from src.a2a_integration.models import LangGraphExecutorConfig

wrapper_logger = structlog.get_logger(__name__)

# TODO: "image/png", "audio/mpeg", "video/mp4"
SUPPORTED_CONTENT_MIME_TYPES = ["text/plain", "text/markdown", "application/json"]


def build_request_handler(executor: AgentExecutor) -> DefaultRequestHandler:
    """DefaultRequestHandler 기반의 구성."""
    httpx_client = httpx.AsyncClient(
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
            "Connection": "keep-alive",
        },
    )
    # **DO NOT USE PRODUCTION**
    # TODO: MQ 기반 푸시 알림 구현 필요
    push_config_store = InMemoryPushNotificationConfigStore()
    push_sender = BasePushNotificationSender(
        httpx_client=httpx_client,
        config_store=push_config_store,
    )
    return DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),  # TODO: 메모리 기반이 아닌 데이터베이스 기반으로 변경 필요
        push_config_store=push_config_store,
        push_sender=push_sender,
    )


def build_a2a_starlette_application(
    agent_card: AgentCard, handler: DefaultRequestHandler
) -> A2AStarletteApplication:
    """A2AStarletteApplication 생성."""
    return A2AStarletteApplication(agent_card=agent_card, http_handler=handler)

# NOTE: uv add "a2a-sdk[http-server]" 를 설치해야함
def build_a2a_fastapi_application(
    agent_card: AgentCard, handler: DefaultRequestHandler
) -> A2AFastAPIApplication:
    """A2AFastAPIApplication 생성."""
    return A2AFastAPIApplication(agent_card=agent_card, http_handler=handler)


def create_agent_skill(
    skill_id: str,
    description: str,
    tags: list[str],
    name: str | None = None,
    input_modes: list[str] | None = None,
    output_modes: list[str] | None = None,
    examples: list[str] | None = None,
) -> AgentSkill:
    """에이전트 스킬 생성"""
    if input_modes is None:
        input_modes = SUPPORTED_CONTENT_MIME_TYPES
    if output_modes is None:
        output_modes = SUPPORTED_CONTENT_MIME_TYPES

    return AgentSkill(
        id=skill_id,
        name=name or skill_id,
        description=description,
        input_modes=input_modes,
        output_modes=output_modes,
        tags=tags,
        examples=examples,
    )


def create_agent_card(
    *,
    name: str,
    description: str,
    url: str,
    skills: Iterable[AgentSkill],
    version: str = "1.0.0",
    default_input_modes: list[str] | None = None,
    default_output_modes: list[str] | None = None,
    streaming: bool = True,
    push_notifications: bool = True,
) -> AgentCard:
    """
    A2A 프로토콜 표준에 맞는 AgentCard 생성.

    Args:
        name: 에이전트 이름
        description: 에이전트 설명
        url: 에이전트 URL => 위치에 따라 잘 선택해야함(ex> 도커환경이라면?)
        skills: 에이전트 기능
        version: 에이전트 버전
        default_input_modes: 기본 입력 모드
        default_output_modes: 기본 출력 모드
        streaming: 스트리밍 지원 여부
        push_notifications: 푸시 알림 지원 여부

    """
    capabilities = AgentCapabilities(
        streaming=streaming,
        push_notifications=push_notifications,
    )
    return AgentCard(
        name=name,
        description=description,
        url=url,
        version=version,
        default_input_modes=default_input_modes or SUPPORTED_CONTENT_MIME_TYPES,
        default_output_modes=default_output_modes or SUPPORTED_CONTENT_MIME_TYPES,
        capabilities=capabilities,
        skills=list(skills),
    )


def to_a2a_starlette_server(
    *,
    graph: CompiledStateGraph,
    agent_card: AgentCard,
    result_extractor: Callable[[Any], str] | None = None,
    config: LangGraphExecutorConfig | None = None,
    input_processor: Any | None = None,  # 커스텀 입력 프로세서 추가
) -> A2AStarletteApplication:
    """CompiledStateGraph를 받아 A2A 서버 애플리케이션을 Starlette 기반으로 구성."""
    # 커스텀 입력 프로세서가 제공되면 config에 추가
    if input_processor:
        if config is None:
            config = LangGraphExecutorConfig()
        if config.strategy_config is None:
            config.strategy_config = {}
        # 팩토리 함수인 경우 호출해서 인스턴스 생성
        if callable(input_processor):
            # 팩토리 함수 자체를 저장 (나중에 graph와 config로 호출)
            config.strategy_config["input_processor_factory"] = input_processor
        else:
            # 이미 인스턴스인 경우 직접 저장
            config.strategy_config["input_processor"] = input_processor

    executor = LangGraphAgentExecutor(
        graph=graph,
        result_extractor=result_extractor,
        config=config,
    )
    handler = build_request_handler(executor)
    return build_a2a_starlette_application(agent_card, handler)


def to_a2a_fastapi_server(
    *,
    graph: CompiledStateGraph,
    agent_card: AgentCard,
    result_extractor: Callable[[Any], str] | None = None,
    config: LangGraphExecutorConfig | None = None,
    input_processor: Any | None = None,  # 커스텀 입력 프로세서 추가
    agent_type: str | None = None,  # 에이전트 타입 추가
) -> A2AFastAPIApplication:
    """CompiledStateGraph를 받아 A2A 서버 애플리케이션을 FastAPI 기반으로 구성."""
    # 커스텀 입력 프로세서가 제공되면 config에 추가
    if input_processor:
        if config is None:
            config = LangGraphExecutorConfig()
        if config.strategy_config is None:
            config.strategy_config = {}
        config.strategy_config["input_processor"] = input_processor

    executor = LangGraphAgentExecutor(
        graph=graph,
        result_extractor=result_extractor,
        config=config,
        agent_type=agent_type,
    )
    handler = build_request_handler(executor)
    return build_a2a_fastapi_application(agent_card, handler)


def to_a2a_run_uvicorn(
    *,
    server_app: JSONRPCApplication,
    host: str,
    port: int,
    graph: CompiledStateGraph | None = None,
    agent_card: AgentCard | None = None,
    enable_schema_endpoint: bool = True,
):
    """A2A 서버를 uvicorn으로 실행.(JSONRPC 포맷을 지원하는 Starlette 또는 FastAPI 애플리케이션)"""
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    app = server_app.build()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add health check endpoint
    async def health_check(request: Request):
        return JSONResponse(
            {
                "status": "healthy",
                "request": str(request.values()),
            }
        )

    app.router.routes.append(
        Route(
            "/health",
            health_check,
            methods=["GET"],
        )
    )

    # LangGraph 스키마 엔드포인트 추가 (enable_schema_endpoint가 True인 경우)
    if enable_schema_endpoint:

        async def get_langgraph_schemas(request: Request):
            """LangGraph Agent의 입력/출력 스키마 조회"""

            try:
                # 1. 필수 객체들의 존재 여부 확인
                if graph is None:
                    raise ValueError("Graph is not provided")
                if agent_card is None:
                    raise ValueError("Agent card is not provided")

                # 2. 메서드 존재 여부 확인 후 스키마 조회
                input_schema = None
                output_schema = None

                # LangGraph 메서드 존재 여부 확인
                if hasattr(graph, "get_input_jsonschema"):
                    try:
                        input_schema = graph.get_input_jsonschema()
                    except Exception as e:
                        print(f"Failed to get input schema: {e}")

                if hasattr(graph, "get_output_jsonschema"):
                    try:
                        output_schema = graph.get_output_jsonschema()
                    except Exception as e:
                        print(f"Failed to get output schema: {e}")

                # 3. 대안 메서드 시도
                if input_schema is None and hasattr(graph, "get_input_schema"):
                    try:
                        input_schema = graph.get_input_schema()
                    except Exception as e:
                        print(
                            f"Failed to get input schema with alternative method: {e}"
                        )

                if output_schema is None and hasattr(graph, "get_output_schema"):
                    try:
                        output_schema = graph.get_output_schema()
                    except Exception as e:
                        print(
                            f"Failed to get output schema with alternative method: {e}"
                        )

                # 4. 안전한 스키마 변환
                def safe_schema_conversion(schema):
                    if schema is None:
                        return {}

                    # Pydantic 모델 변환
                    if hasattr(schema, "model_dump"):
                        try:
                            return schema.model_dump()
                        except Exception:
                            pass
                    elif hasattr(schema, "dict"):
                        try:
                            return schema.dict()
                        except Exception:
                            pass
                    elif hasattr(schema, "__dict__"):
                        try:
                            return schema.__dict__
                        except Exception:
                            pass
                    elif isinstance(schema, dict):
                        return schema
                    else:
                        # JSON 직렬화 가능한지 확인
                        try:
                            import json

                            json.dumps(schema)
                            return schema
                        except (TypeError, ValueError):
                            return {"type": "unknown", "description": str(type(schema))}

                converted_input_schema = safe_schema_conversion(input_schema)
                converted_output_schema = safe_schema_conversion(output_schema)

                return JSONResponse(
                    {
                        "input_schema": converted_input_schema,
                        "output_schema": converted_output_schema,
                        "agent_name": getattr(agent_card, "name", "unknown"),
                        "timestamp": str(datetime.now()),
                        "source": "langgraph",
                        "debug_info": {
                            "graph_type": str(type(graph)),
                            "has_input_jsonschema": hasattr(
                                graph, "get_input_jsonschema"
                            ),
                            "has_output_jsonschema": hasattr(
                                graph, "get_output_jsonschema"
                            ),
                            "input_schema_type": str(type(input_schema)),
                            "output_schema_type": str(type(output_schema)),
                        },
                    }
                )

            except Exception as e:
                # 상세한 에러 정보 포함
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "graph_available": graph is not None,
                    "agent_card_available": agent_card is not None,
                }

                if graph is not None:
                    error_details["graph_type"] = str(type(graph))
                    error_details["graph_methods"] = [
                        method
                        for method in dir(graph)
                        if method.startswith("get_") and "schema" in method
                    ]

                return JSONResponse(
                    {
                        "input_schema": {
                            "type": "object",
                            "properties": {"message": {"type": "string"}},
                            "required": ["message"],
                        },
                        "output_schema": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string"},
                                "data": {"type": "object"},
                            },
                        },
                        "error": f"Failed to get schemas: {str(e)}",
                        "error_details": error_details,
                        "source": "fallback",
                    }
                )

        app.router.routes.append(
            Route(
                "/schemas",
                get_langgraph_schemas,
                methods=["GET"],
            )
        )

    # uvicorn 서버 설정 - 타임아웃 증가
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
        reload=False,
        timeout_keep_alive=300,  # Keep-alive 타임아웃 300초로 증가
        timeout_notify=300,  # 종료 전 알림 타임아웃 300초
        ws_ping_interval=30,  # WebSocket ping 간격 30초
        ws_ping_timeout=60,  # WebSocket ping 타임아웃 60초
        limit_concurrency=1000,  # 동시 연결 제한 증가
    )
    server = uvicorn.Server(config)
    server.run()

# NOTE: 이 부분이 Agent Registry 라고 보실 수도 있습니다.
class A2AAgentFactory:
    """A2A 호환 Agent 생성을 위한 팩토리 클래스

    create_react_agent로 생성된 graph를 직접 받아 A2A 프로토콜과 연결합니다.
    """

    @staticmethod
    def create_data_collector_agent(
        graph: CompiledStateGraph = None,  # CompiledStateGraph from create_react_agent
        result_extractor: Callable[[dict[str, Any]], dict[str, Any] | str] | None = None
    ) -> "LangGraphAgentExecutor":
        """DataCollector Agent용 LangGraphAgentExecutor 생성

        Args:
            graph: create_data_collector_agent()로 생성된 CompiledStateGraph
            result_extractor: 결과 추출 함수 (A2A 프로토콜용 구조화)
        """
        return LangGraphAgentExecutor(
            graph=graph,
            result_extractor=result_extractor
        )

    @staticmethod
    def create_analysis_agent(
        graph: CompiledStateGraph = None,  # CompiledStateGraph from create_react_agent
        result_extractor: Callable[[dict[str, Any]], dict[str, Any] | str] | None = None
    ) -> "LangGraphAgentExecutor":
        """Analysis Agent용 LangGraphAgentExecutor 생성

        Args:
            graph: create_analysis_agent()로 생성된 CompiledStateGraph
            result_extractor: 결과 추출 함수 (A2A 프로토콜용 구조화)
        """
        return LangGraphAgentExecutor(
            graph=graph,
            result_extractor=result_extractor
        )

    @staticmethod
    def create_trading_agent(
        graph: CompiledStateGraph = None,
        result_extractor: Callable[[dict[str, Any]], dict[str, Any] | str] | None = None
    ) -> "LangGraphAgentExecutor":
        """Trading Agent용 LangGraphAgentExecutor 생성

        Args:
            graph: create_trading_agent()로 생성된 CompiledStateGraph
            result_extractor: 결과 추출 함수 (A2A 프로토콜용 구조화)
        """
        return LangGraphAgentExecutor(
            graph=graph,
            result_extractor=result_extractor
        )

    @staticmethod
    def create_supervisor_agent(
        graph: CompiledStateGraph = None,  # CompiledStateGraph from BaseGraphAgent
        result_extractor: Callable[[dict[str, Any]], dict[str, Any] | str] | None = None
    ) -> "LangGraphAgentExecutor":
        """Supervisor Agent용 LangGraphAgentExecutor 생성

        Args:
            graph: SupervisorAgent의 graph 속성
            result_extractor: 결과 추출 함수 (A2A 프로토콜용 구조화)
        """
        return LangGraphAgentExecutor(
            graph=graph,
            result_extractor=result_extractor
        )
