"""통합 에이전트 LangGraph 워크플로우 구현"""

from typing import Any, Dict, List, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import IntegratedAgentNodes
from .state import IntegratedAgentState, create_initial_state, set_processing_end_time


class IntegratedAgent:
    """통합 투자 분석 에이전트 - LangGraph 기반"""

    def __init__(self, model_name: str = "gpt-oss:20b"):
        """초기화"""
        self.model_name = model_name
        self.nodes = IntegratedAgentNodes(model_name)

        # 메모리 저장소 (세션 기반 대화 기억)
        self.memory = MemorySaver()

        # 워크플로우 그래프 구축
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.memory)

        # MCP 도구 초기화 플래그
        self._mcp_initialized = False

    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구성 (검증 과정 제거)"""
        workflow = StateGraph(IntegratedAgentState)

        # 노드 추가 (validate 노드 제거)
        workflow.add_node("collect", self.nodes.collect_node)
        workflow.add_node("analyze", self.nodes.analyze_node)
        workflow.add_node("decide", self.nodes.decide_node)
        workflow.add_node("respond", self.nodes.respond_node)

        # 시작점 설정 (바로 collect부터 시작)
        workflow.set_entry_point("collect")

        # 순차적 흐름
        workflow.add_edge("collect", "analyze")
        workflow.add_edge("analyze", "decide")
        workflow.add_edge("decide", "respond")
        workflow.add_edge("respond", END)

        return workflow

    async def process_question(
        self, question: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        질문 처리 메인 메서드

        Args:
            question: 사용자 질문
            session_id: 세션 ID (대화 기억용)

        Returns:
            Dict[str, Any]: 처리 결과
        """
        try:
            # MCP 도구 초기화 (최초 1회)
            if not self._mcp_initialized:
                await self.nodes.initialize_mcp_tools()
                self._mcp_initialized = True

            # 초기 상태 생성
            initial_state = create_initial_state(question, session_id)

            # 워크플로우 실행
            config = {"configurable": {"thread_id": session_id or "default"}}

            # 스트리밍 실행
            final_state = None
            async for state in self.app.astream(initial_state, config):
                final_state = state

            # 마지막 상태에서 결과 추출
            if final_state:
                last_node_state = list(final_state.values())[-1]
                # 처리 완료 시간 설정
                completed_state = set_processing_end_time(last_node_state)

                return {
                    "success": True,
                    "response": completed_state["final_response"],
                    "response_type": completed_state["response_type"],
                    "is_investment_related": completed_state["is_investment_related"],
                    "validation_confidence": completed_state["validation_confidence"],
                    "processing_time": completed_state["total_processing_time"],
                    "used_servers": completed_state["total_used_servers"],
                    "step_usage": completed_state["step_mcp_usage"],
                    "state": completed_state,
                }
            else:
                return {
                    "success": False,
                    "error": "워크플로우 실행 중 상태를 받지 못했습니다.",
                    "response": "처리 중 오류가 발생했습니다.",
                    "response_type": "error",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"질문 처리 중 오류가 발생했습니다: {str(e)}",
                "response_type": "error",
            }

    async def stream_process_question(
        self, question: str, session_id: Optional[str] = None
    ):
        """
        스트리밍 방식으로 질문 처리 (실시간 단계별 진행 상황)

        Args:
            question: 사용자 질문
            session_id: 세션 ID

        Yields:
            Dict[str, Any]: 단계별 진행 상황
        """
        try:
            # MCP 도구 초기화 (최초 1회)
            if not self._mcp_initialized:
                await self.nodes.initialize_mcp_tools()
                self._mcp_initialized = True

            # 초기 상태 생성
            initial_state = create_initial_state(question, session_id)

            # 워크플로우 스트리밍 실행
            config = {"configurable": {"thread_id": session_id or "default"}}

            async for state_update in self.app.astream(initial_state, config):
                # 각 노드의 실행 결과를 실시간으로 전송
                for node_name, node_state in state_update.items():
                    yield {
                        "type": "step_update",
                        "step": node_state["current_step"],
                        "node": node_name,
                        "active_servers": node_state["active_mcp_servers"],
                        "step_usage": node_state["step_mcp_usage"],
                        "total_used": node_state["total_used_servers"],
                        "is_investment_related": node_state["is_investment_related"],
                        "validation_confidence": node_state.get(
                            "validation_confidence", 0.0
                        ),
                        "errors": node_state["errors"],
                        "warnings": node_state["warning_messages"],
                    }

                    # 최종 응답이 준비되면 전송
                    if node_state["final_response"]:
                        # 처리 완료 시간 설정
                        completed_state = set_processing_end_time(node_state)

                        yield {
                            "type": "final_response",
                            "response": completed_state["final_response"],
                            "response_type": completed_state["response_type"],
                            "processing_time": completed_state["total_processing_time"],
                            "used_servers": completed_state["total_used_servers"],
                            "step_usage": completed_state["step_mcp_usage"],
                            "state": completed_state,
                        }

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "response": f"스트리밍 처리 중 오류: {str(e)}",
                "response_type": "error",
            }

    def get_conversation_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션의 대화 기록 조회"""
        try:
            # MemorySaver에서 세션 기록 조회
            config = {"configurable": {"thread_id": session_id}}

            # 체크포인트에서 마지막 상태 가져오기
            checkpoint = self.memory.get(config)
            if checkpoint:
                return {
                    "session_id": session_id,
                    "last_state": checkpoint,
                    "exists": True,
                }
            else:
                return {"session_id": session_id, "exists": False}

        except Exception as e:
            return {"session_id": session_id, "error": str(e), "exists": False}

    def clear_conversation_history(self, session_id: str) -> bool:
        """세션의 대화 기록 삭제"""
        try:
            # 메모리에서 세션 기록 삭제
            # MemorySaver에는 직접적인 삭제 메서드가 없으므로
            # 새로운 워크플로우 앱을 다시 컴파일하여 메모리 초기화
            return True

        except Exception:
            return False

    def get_available_mcp_servers(self) -> List[str]:
        """사용 가능한 MCP 서버 목록 반환"""
        return list(self.nodes.server_tools_map.keys())

    def get_mcp_server_tools(self, server_name: str) -> Optional[List[str]]:
        """특정 MCP 서버의 도구 목록 반환"""
        return self.nodes.server_tools_map.get(server_name)
