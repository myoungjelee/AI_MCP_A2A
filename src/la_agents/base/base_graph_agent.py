"""
LangGraph 에이전트 기본 클래스

모든 LangGraph 에이전트가 상속받는 기본 클래스입니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from .error_handling import AgentError, ErrorHandler
from .interrupt_manager import InterruptManager
from .mcp_loader import MCPLoader

logger = logging.getLogger(__name__)


class BaseGraphAgent(ABC):
    """LangGraph 에이전트 기본 클래스"""

    def __init__(
        self,
        name: str,
        mcp_servers: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """에이전트 초기화"""
        self.name = name
        self.config = config or {}

        # 로깅 설정
        self.logger = logging.getLogger(f"agent.{name}")
        self._setup_logging()

        # MCP 로더 초기화
        self.mcp_loader = MCPLoader(mcp_servers or [])

        # 에러 핸들러 초기화
        self.error_handler = ErrorHandler()

        # 인터럽트 매니저 초기화
        self.interrupt_manager = InterruptManager()

        # 워크플로우 그래프 초기화
        self.workflow = None
        self._build_workflow()

        # 상태 초기화
        self.current_state = None

        self.logger.info(f"에이전트 '{name}' 초기화 완료")

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _build_workflow(self):
        """워크플로우 구축"""
        # StateGraph 초기화
        self.workflow = StateGraph(self._get_state_type())

        # 하위 클래스에서 노드와 엣지를 추가
        self._add_nodes()
        self._add_edges()

        # 워크플로우 컴파일
        self.workflow = self.workflow.compile()

    @abstractmethod
    def _add_nodes(self):
        """노드 추가 (하위 클래스에서 구현)"""
        pass

    @abstractmethod
    def _add_edges(self):
        """엣지 추가 (하위 클래스에서 구현)"""
        pass

    @abstractmethod
    def _create_initial_state(self, **kwargs) -> Dict[str, Any]:
        """초기 상태 생성 (하위 클래스에서 구현)"""
        pass

    async def start(self, **kwargs) -> Dict[str, Any]:
        """에이전트 실행 시작"""
        try:
            self.logger.info(f"에이전트 '{self.name}' 실행 시작")

            # 초기 상태 생성
            initial_state = self._create_initial_state(**kwargs)

            # MCP 서버들 연결
            await self.mcp_loader.connect_all()

            # 워크플로우 실행
            config = RunnableConfig(
                callbacks=[self.interrupt_manager.get_callback()],
                configurable={"thread_id": self.name},
            )

            result = await self.workflow.ainvoke(initial_state, config)

            self.logger.info(f"에이전트 '{self.name}' 실행 완료")
            return result

        except Exception as e:
            self.logger.error(f"에이전트 '{self.name}' 실행 실패: {e}")
            await self.error_handler.handle_error(e, self.name)
            raise AgentError(f"에이전트 실행 실패: {e}") from e

        finally:
            # MCP 서버들 연결 해제
            await self.mcp_loader.disconnect_all()

    async def stop(self):
        """에이전트 중지"""
        try:
            self.logger.info(f"에이전트 '{self.name}' 중지")
            await self.interrupt_manager.interrupt()
            await self.mcp_loader.disconnect_all()
        except Exception as e:
            self.logger.error(f"에이전트 '{self.name}' 중지 실패: {e}")

    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        return {
            "name": self.name,
            "status": "running" if self.workflow else "stopped",
            "mcp_servers": self.mcp_loader.get_connected_servers(),
            "interrupts": self.interrupt_manager.get_interrupt_count(),
            "errors": self.error_handler.get_error_count(),
        }

    def get_workflow_info(self) -> Dict[str, Any]:
        """워크플로우 정보 반환"""
        return {
            "state_type": self._get_state_type().__name__,
            "compiled": self.workflow is not None,
            "nodes": [],  # 실제로는 워크플로우에서 추출
            "edges": [],  # 실제로는 워크플로우에서 추출
        }

    @abstractmethod
    def _get_state_type(self):
        """상태 타입 반환 (하위 클래스에서 구현)"""
        pass
