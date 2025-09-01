"""
단일 통합 에이전트

모든 기능을 통합한 단일 LangGraph 에이전트입니다.
MCP 서버들과 연동하여 종합적인 데이터 수집, 분석, 의사결정을 수행합니다.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from langgraph.graph import END, START

from ..base import BaseGraphAgent
from ..base.mcp_config import MCPServerConfig, create_mcp_client_and_tools
from ..base.mcp_loader import MCPLoader
from .nodes import (
    collect_comprehensive_data,
    conversational_response,
    execute_action,
    make_intelligent_decision,
    perform_comprehensive_analysis,
    validate_request,
)
from .state import IntegratedAgentState, create_initial_state, get_state_summary

logger = logging.getLogger(__name__)


class IntegratedAgent(BaseGraphAgent):
    """단일 통합 에이전트"""

    def __init__(
        self,
        name: str = "integrated_agent",
        mcp_servers: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        llm_model: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
    ):
        """통합 에이전트 초기화"""

        # 기본 MCP 서버 목록
        default_mcp_servers = [
            "macroeconomic",
            "financial_analysis",
            "stock_analysis",
            "naver_news",
            "tavily_search",
            "kiwoom",
        ]

        self.mcp_servers = mcp_servers or default_mcp_servers
        self.config = config or {}

        # LLM 모델 설정
        self.llm_model = llm_model or os.getenv("LLM_MODEL", "gpt-oss:20b")
        self.ollama_base_url = ollama_base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

        # MCP 서버 설정 가져오기
        self.mcp_server_configs = MCPServerConfig.get_server_configs(self.mcp_servers)

        # MCP 로더 초기화
        self.mcp_loader = MCPLoader(self.mcp_servers)

        # MCP 클라이언트와 도구들 (나중에 초기화)
        self.mcp_client = None
        self.mcp_tools = []

        super().__init__(
            name=name,
            mcp_servers=self.mcp_servers,
            config=self.config,
        )

        # LLM 초기화 (logger가 초기화된 후)
        self.llm = self._setup_llm()

        self.logger.info(f"통합 에이전트 '{name}' 초기화 완료")
        self.logger.info(f"로컬 LLM 모델: {self.llm_model}")
        self.logger.info(f"MCP 서버 설정: {list(self.mcp_server_configs.keys())}")

    def _add_nodes(self):
        """노드 추가"""
        self.logger.info("통합 에이전트 노드 추가 시작")

        # 각 노드에 에이전트 참조를 제공하는 래퍼 함수 생성
        async def validate_request_with_agent(state):
            return await validate_request(state)

        async def collect_data_with_agent(state):
            # MCP 클라이언트와 도구들을 노드에 전달
            return await collect_comprehensive_data(
                state, mcp_client=self.mcp_client, mcp_tools=self.mcp_tools
            )

        async def analyze_data_with_agent(state):
            return await perform_comprehensive_analysis(state)

        async def make_decision_with_agent(state):
            # LLM 사용이 필요한 노드에만 agent 참조 전달
            return await make_intelligent_decision(state, agent=self)

        async def execute_action_with_agent(state):
            return await execute_action(state)

        async def generate_response_with_agent(state):
            # 대화형 응답 생성 노드 - Ollama LLM 활용
            return await conversational_response(state, agent=self)

        # 노드 추가 (LangGraph 문서에 따른 방식)
        self.workflow.add_node("validate_request", validate_request_with_agent)
        self.workflow.add_node("collect_data", collect_data_with_agent)
        self.workflow.add_node("analyze_data", analyze_data_with_agent)
        self.workflow.add_node("make_decision", make_decision_with_agent)
        self.workflow.add_node("execute_action", execute_action_with_agent)
        self.workflow.add_node("generate_response", generate_response_with_agent)

        self.logger.info("통합 에이전트 노드 추가 완료")

    def _add_edges(self):
        """엣지 추가"""
        self.logger.info("통합 에이전트 엣지 연결 시작")

        # LangGraph 문서에 따른 엣지 연결 방식
        self.workflow.add_edge(START, "validate_request")
        self.workflow.add_edge("validate_request", "collect_data")
        self.workflow.add_edge("collect_data", "analyze_data")
        self.workflow.add_edge("analyze_data", "make_decision")
        self.workflow.add_edge("make_decision", "execute_action")
        self.workflow.add_edge("execute_action", "generate_response")
        self.workflow.add_edge("generate_response", END)

        self.logger.info("통합 에이전트 엣지 연결 완료")

    def _create_initial_state(self, **kwargs) -> Dict[str, Any]:
        """초기 상태 생성"""
        request = kwargs.get("request", {})
        task_type = kwargs.get("task_type", "comprehensive_analysis")

        return create_initial_state(request=request, task_type=task_type)

    def _get_state_type(self):
        """상태 타입 반환"""
        return IntegratedAgentState

    async def run_comprehensive_analysis(
        self, request: Dict[str, Any], task_type: str = "comprehensive_analysis"
    ) -> Dict[str, Any]:
        """종합 분석 실행"""
        try:
            self.logger.info(f"종합 분석 시작: {task_type}")

            # MCP 서버들 연결
            await self._connect_mcp_servers()

            # 에이전트 실행
            result = await self.start(request=request, task_type=task_type)

            # 결과 요약 생성
            summary = get_state_summary(result)

            self.logger.info(f"종합 분석 완료: {summary}")

            # 🔍 결과 구조 상세 디버깅
            self.logger.info("🔍 에이전트 실행 결과 분석:")
            self.logger.info(f"  - result 타입: {type(result)}")
            self.logger.info(f"  - result 키들: {list(result.keys()) if isinstance(result, dict) else 'dict가 아님'}")
            
            # ai_response 찾기 (여러 경로 시도)
            ai_response = None
            if isinstance(result, dict):
                # 경로 1: 직접 ai_response
                if "ai_response" in result:
                    ai_response = result["ai_response"]
                    self.logger.info(f"  - ai_response 발견 (직접): {len(ai_response) if isinstance(ai_response, str) else type(ai_response)} 문자")
                # 경로 2: metadata에서 ai_response
                elif "metadata" in result and isinstance(result["metadata"], dict) and "ai_response" in result["metadata"]:
                    ai_response = result["metadata"]["ai_response"]
                    self.logger.info(f"  - ai_response 발견 (metadata): {len(ai_response) if isinstance(ai_response, str) else type(ai_response)} 문자")
                    # 최상위로 복사
                    result["ai_response"] = ai_response
                else:
                    self.logger.warning("  - ai_response를 찾을 수 없음 (직접 및 metadata 모두 확인)")
            else:
                self.logger.warning("  - result가 dict가 아님")
                
            # ai_response가 있으면 result에 명시적으로 포함
            if "ai_response" in result:
                result["ai_response"] = result["ai_response"]

            return {
                "success": True,
                "result": result,
                "summary": summary,
                "agent_name": self.name,
            }

        except Exception as e:
            self.logger.error(f"종합 분석 실패: {e}")
            return {"success": False, "error": str(e), "agent_name": self.name}
        finally:
            # MCP 서버들 연결 해제
            await self._disconnect_mcp_servers()

    async def run_data_collection(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 수집만 실행"""
        return await self.run_comprehensive_analysis(
            request=request, task_type="data_collection"
        )

    async def run_market_analysis(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """시장 분석만 실행"""
        return await self.run_comprehensive_analysis(
            request=request, task_type="market_analysis"
        )

    async def run_investment_decision(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """투자 의사결정만 실행"""
        return await self.run_comprehensive_analysis(
            request=request, task_type="investment_decision"
        )

    async def run_trading_execution(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """거래 실행만 실행"""
        return await self.run_comprehensive_analysis(
            request=request, task_type="trading_execution"
        )

    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 반환"""
        return {
            "name": self.name,
            "type": "integrated_agent",
            "description": "종합적인 데이터 수집, 분석, 의사결정을 수행하는 통합 에이전트",
            "capabilities": [
                "데이터 수집 (거시경제, 재무, 주식, 뉴스, 검색)",
                "종합 분석 (기술적, 기본적, 감정, 시장)",
                "지능적 의사결정",
                "액션 실행",
            ],
            "mcp_servers": self.mcp_loader.mcp_servers,
            "workflow_steps": [
                "validate_request",
                "collect_data",
                "analyze_data",
                "make_decision",
                "execute_action",
            ],
            "status": "ready",
        }

    async def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return {
            "agent_name": self.name,
            "total_executions": 0,  # 실제로는 카운터 필요
            "success_rate": 1.0,
            "average_execution_time": 30.0,  # 초
            "last_execution": None,
            "mcp_connections": self.mcp_loader.get_connection_summary(),
            "error_count": self.error_handler.get_error_count(),
        }

    async def _connect_mcp_servers(self):
        """MCP 서버들 연결"""
        try:
            self.logger.info("MCP 서버 연결 시작")

            # MCP 로더를 사용하여 서버들 연결
            await self.mcp_loader.connect_all()

            # MCP 클라이언트와 도구들 생성
            self.mcp_client, self.mcp_tools = await create_mcp_client_and_tools(
                self.mcp_server_configs
            )
            self.logger.info(
                f"MCP 서버 연결 완료: {len(self.mcp_loader.connected_servers)}개"
            )
            self.logger.info(f"MCP 도구 로딩 완료: {len(self.mcp_tools)}개")

        except Exception as e:
            self.logger.error(f"MCP 서버 연결 실패: {e}")
            raise

    async def _disconnect_mcp_servers(self):
        """MCP 서버들 연결 해제"""
        try:
            self.logger.info("MCP 서버 연결 해제 시작")

            # MCP 로더를 사용하여 서버들 연결 해제
            await self.mcp_loader.disconnect_all()

            # 클라이언트 정리
            self.mcp_client = None
            self.mcp_tools = []

            self.logger.info("MCP 서버 연결 해제 완료")

        except Exception as e:
            self.logger.error(f"MCP 서버 연결 해제 실패: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            # MCP 서버 연결 상태 확인
            mcp_status = {}
            for server in self.mcp_loader.mcp_servers:
                is_connected = self.mcp_loader.is_server_connected(server)
                mcp_status[server] = "connected" if is_connected else "disconnected"

            return {
                "status": "healthy",
                "agent_name": self.name,
                "workflow_ready": self.workflow is not None,
                "mcp_servers": mcp_status,
                "error_count": self.error_handler.get_error_count(),
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "agent_name": self.name,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time(),
            }

    def _setup_llm(self) -> Any:
        """로컬 Ollama LLM 모델 설정"""
        try:
            # Ollama 모델 초기화
            from langchain_community.llms import Ollama

            # Ollama 기반 로컬 모델 사용
            llm = Ollama(
                model=self.llm_model,  # 로컬 Ollama 모델명
                temperature=0.1,  # 낮은 temperature로 일관된 결과
                base_url=self.ollama_base_url,  # 설정된 Ollama URL 사용
            )

            self.logger.info(f"로컬 Ollama LLM 모델 초기화 완료: {self.llm_model}")
            return llm

        except ImportError:
            self.logger.error(
                "langchain_community 패키지가 설치되지 않았습니다. 'pip install langchain-community'를 실행해주세요."
            )
            return None
        except Exception as e:
            self.logger.error(f"로컬 Ollama LLM 모델 초기화 실패: {e}")
            self.logger.info("Ollama가 실행 중인지 확인해주세요: 'ollama serve'")
            return None
