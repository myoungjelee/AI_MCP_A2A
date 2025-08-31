"""
LangGraph 에이전트의 기본 클래스

모든 LangGraph 에이전트는 이 클래스를 상속받아 구현합니다.
MCP 서버 연결, 도구 로딩, 에러 처리 등의 공통 기능을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph

from .error_handling import (
    AgentConfigurationError,
    AgentExecutionError,
    validate_agent_state,
)
from .interrupt_manager import InterruptManager
from .mcp_loader import load_specific_mcp_tools

logger = structlog.get_logger(__name__)


class BaseGraphAgent(ABC):
    """
    LangGraph 에이전트의 기본 클래스

    모든 LangGraph 에이전트는 이 클래스를 상속받아 구현합니다.
    MCP 서버 연결, 도구 로딩, 에러 처리 등의 공통 기능을 제공합니다.
    """

    def __init__(
        self,
        model: BaseLanguageModel,
        agent_type: Optional[str] = None,
        state_schema: Optional[Type] = None,
        tools: Optional[List[BaseTool]] = None,
        lazy_init: bool = False,
        max_iterations: int = 10,
        interrupt_manager: Optional[InterruptManager] = None,
        **kwargs,
    ):
        """
        BaseGraphAgent 초기화

        Args:
            model: 언어 모델
            agent_type: 에이전트 타입 (MCP 서버 자동 연결용)
            state_schema: 상태 스키마
            tools: 도구 목록
            lazy_init: 지연 초기화 여부
            max_iterations: 최대 반복 횟수
            interrupt_manager: 인터럽트 관리자
            **kwargs: 추가 인자
        """
        self.model = model
        self.agent_type = agent_type
        self.state_schema = state_schema
        self.max_iterations = max_iterations
        self.interrupt_manager = interrupt_manager or InterruptManager()

        # MCP 서버 자동 연결
        self.mcp_server_names = self._get_mcp_servers_for_agent(agent_type)
        self.mcp_tools = []

        # 도구 설정
        self._tools = tools or []

        # 워크플로우
        self.workflow: Optional[StateGraph] = None

        # 지연 초기화가 아닌 경우 즉시 초기화
        if not lazy_init:
            self._initialize_workflow()

    def _get_mcp_servers_for_agent(self, agent_type: Optional[str]) -> List[str]:
        """에이전트 타입에 따라 필요한 MCP 서버 목록 반환"""
        if not agent_type:
            return []

        try:
            from .mcp_config import get_mcp_servers_for_agent

            return get_mcp_servers_for_agent(agent_type)
        except ImportError:
            logger.warning(f"MCP 설정을 불러올 수 없습니다: {agent_type}")
            return []

    async def _load_mcp_tools(self) -> List[BaseTool]:
        """MCP 서버에서 도구들을 로딩"""
        if not self.mcp_server_names:
            return []

        try:
            logger.info(f"MCP 도구 로딩 시작: {self.mcp_server_names}")
            tools = await load_specific_mcp_tools(self.mcp_server_names)
            logger.info(f"MCP 도구 로딩 완료: {len(tools)}개")
            return tools
        except Exception as e:
            logger.error(f"MCP 도구 로딩 실패: {e}")
            return []

    def _initialize_workflow(self):
        """워크플로우 초기화"""
        if not self.state_schema:
            raise AgentConfigurationError("state_schema가 설정되지 않았습니다")

        # 워크플로우 생성
        self.workflow = StateGraph(self.state_schema)

        # 노드와 엣지 초기화
        self.init_nodes(self.workflow)
        self.init_edges(self.workflow)

        # 워크플로우 컴파일
        self.workflow = self.workflow.compile()

        logger.info(f"워크플로우 초기화 완료: {self.__class__.__name__}")

    async def initialize(self):
        """에이전트 초기화 (비동기)"""
        try:
            # MCP 도구 로딩
            self.mcp_tools = await self._load_mcp_tools()

            # 모든 도구 통합
            all_tools = self._tools + self.mcp_tools

            # 워크플로우가 아직 초기화되지 않은 경우 초기화
            if not self.workflow:
                self._initialize_workflow()

            logger.info(
                f"에이전트 초기화 완료: {self.__class__.__name__}, 도구: {len(all_tools)}개"
            )

        except Exception as e:
            logger.error(f"에이전트 초기화 실패: {e}")
            raise AgentConfigurationError(f"초기화 실패: {e}") from e

    @abstractmethod
    def init_nodes(self, graph: StateGraph):
        """워크플로우 노드 초기화"""
        pass

    @abstractmethod
    def init_edges(self, graph: StateGraph):
        """워크플로우 엣지 초기화"""
        pass

    def build_graph(self) -> StateGraph:
        """워크플로우 그래프 빌드"""
        if not self.workflow:
            self._initialize_workflow()
        return self.workflow

    async def invoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        워크플로우 실행

        Args:
            input_data: 입력 데이터
            config: 실행 설정
            **kwargs: 추가 인자

        Returns:
            실행 결과
        """
        try:
            # 에이전트가 초기화되지 않은 경우 초기화
            if not self.workflow:
                await self.initialize()

            # 입력 데이터 검증
            validate_agent_state(input_data, self.state_schema)

            # 인터럽트 체크
            if self.interrupt_manager.should_interrupt():
                raise AgentExecutionError("에이전트 실행이 인터럽트되었습니다")

            # 워크플로우 실행
            result = await self.workflow.ainvoke(input_data, config=config, **kwargs)

            logger.info(f"워크플로우 실행 완료: {self.__class__.__name__}")
            return result

        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {e}")
            raise AgentExecutionError(f"실행 실패: {e}") from e

    def get_tools(self) -> List[BaseTool]:
        """사용 가능한 모든 도구 반환"""
        return self._tools + self.mcp_tools

    def add_tool(self, tool: BaseTool):
        """도구 추가"""
        self._tools.append(tool)

    def remove_tool(self, tool_name: str):
        """도구 제거"""
        self._tools = [t for t in self._tools if t.name != tool_name]

    def get_mcp_server_names(self) -> List[str]:
        """연결된 MCP 서버 이름 목록 반환"""
        return self.mcp_server_names.copy()

    def is_mcp_connected(self, server_name: str) -> bool:
        """특정 MCP 서버 연결 여부 확인"""
        return server_name in self.mcp_server_names

    async def test_mcp_connections(self) -> Dict[str, bool]:
        """MCP 서버 연결 상태 테스트"""
        from .mcp_loader import test_mcp_connection

        results = {}
        for server_name in self.mcp_server_names:
            try:
                # 간단한 연결 테스트
                is_connected = await test_mcp_connection(server_name)
                results[server_name] = is_connected
            except Exception as e:
                logger.error(f"MCP 서버 {server_name} 연결 테스트 실패: {e}")
                results[server_name] = False

        return results

    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 반환"""
        return {
            "class_name": self.__class__.__name__,
            "agent_type": self.agent_type,
            "mcp_servers": self.mcp_server_names,
            "total_tools": len(self.get_tools()),
            "custom_tools": len(self._tools),
            "mcp_tools": len(self.mcp_tools),
            "max_iterations": self.max_iterations,
            "workflow_initialized": self.workflow is not None,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_type={self.agent_type}, tools={len(self.get_tools())})"

    def __str__(self) -> str:
        return self.__repr__()
