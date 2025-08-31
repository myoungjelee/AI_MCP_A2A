"""
Supervisor 에이전트 - 단순화된 버전
FastCampus의 실제 구현체를 참조하여 2-3년차 수준으로 단순화했습니다.
전체 워크플로우를 조율하고 다른 에이전트들을 순차적으로 호출합니다.
"""

import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

# 원본 코드 패턴: OpenAI GPT-5 모델 사용
from .base import BaseGraphAgent, handle_async_agent_errors


# Supervisor 에이전트 전용 상태 정의
class SupervisorState(TypedDict):
    """Supervisor 에이전트의 상태 스키마"""

    # 기본 상태 (BaseGraphState에서 상속)
    messages: List[Any]  # 메시지 히스토리

    # 감독 상태
    supervision_status: str  # 감독 상태 (monitoring, intervention, resolved)
    active_agents: List[str]  # 활성 에이전트 목록
    system_health: str  # 시스템 상태 (healthy, warning, critical)

    # 워크플로우 상태
    workflow_status: str  # 워크플로우 상태 (initialized, running, completed, failed)
    current_step: str  # 현재 단계
    total_steps: int  # 전체 단계 수

    # 에이전트 상태 및 결과
    agent_states: Dict[str, Any]  # 각 에이전트의 상태
    final_result: Optional[Dict[str, Any]]  # 최종 결과

    # 시스템 정보
    alerts: List[str]  # 알림 목록
    warnings: List[str]  # 경고 목록
    error_log: List[str]  # 에러 로그
    execution_time: float  # 실행 시간


class SupervisorAgent(BaseGraphAgent):
    """
    Supervisor 에이전트

    전체 워크플로우를 조율하고 다른 에이전트들을 순차적으로 호출합니다.
    LangGraph의 StateGraph를 사용하여 복잡한 워크플로우를 관리합니다.
    """

    def __init__(
        self,
        model: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
        agent_name: str = "Supervisor",
        debug: bool = False,
    ):
        """
        Supervisor 에이전트를 초기화합니다.

        Args:
            model: LLM 모델 (기본값: OpenAI GPT-5)
            tools: 사용할 도구들
            mcp_servers: MCP 서버 설정 목록
            agent_name: 에이전트 이름
            debug: 디버그 모드
        """
        # 원본 코드 패턴: OpenAI GPT-5 모델 초기화
        if model is None:
            model = ChatOpenAI(
                model="gpt-5",
                temperature=0,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
            logging.info("✅ OpenAI GPT-5 모델 초기화 완료")

        super().__init__(
            model=model,
            state_schema=SupervisorState,
            tools=tools,
            mcp_servers=mcp_servers,
            agent_name=agent_name,
            is_debug=debug,
            lazy_init=True,  # MCP 도구 로딩을 위해 lazy_init 사용
        )

        self.logger = logging.getLogger(f"agent.{agent_name}")

        # 워크플로우 관련 설정
        self.workflow_steps = [
            "data_collection",
            "data_analysis",
            "portfolio_construction",
            "result_synthesis",
        ]
        self.max_retries = 3
        self.timeout_seconds = 300  # 5분

        self.logger.info(f"Supervisor 에이전트 초기화 완료: {agent_name}")

    def init_nodes(self, graph: StateGraph) -> None:
        """워크플로우 노드들을 초기화합니다."""
        # 각 단계별 노드 생성
        graph.add_node("start", self._start_workflow)
        graph.add_node("data_collection", self._execute_data_collection)
        graph.add_node("data_analysis", self._execute_data_analysis)
        graph.add_node("portfolio_construction", self._execute_portfolio_construction)
        graph.add_node("result_synthesis", self._synthesize_results)
        graph.add_node("error_handling", self._handle_errors)

        self.logger.info("워크플로우 노드 초기화 완료")

    def init_edges(self, graph: StateGraph) -> None:
        """워크플로우 엣지들을 초기화합니다."""
        # 기본 워크플로우 흐름
        graph.add_edge(START, "start")  # START 노드에서 시작점으로 연결
        graph.add_edge("start", "data_collection")
        graph.add_edge("data_collection", "data_analysis")
        graph.add_edge("data_analysis", "portfolio_construction")
        graph.add_edge("portfolio_construction", "result_synthesis")
        graph.add_edge("result_synthesis", END)

        # 에러 처리 흐름
        graph.add_edge("error_handling", END)

        # 조건부 엣지 (에러 발생 시)
        graph.add_conditional_edges(
            "data_collection",
            self._should_continue_to_analysis,
            {
                "continue": "data_analysis",
                "error": "error_handling",
            },
        )

        graph.add_conditional_edges(
            "data_analysis",
            self._should_continue_to_portfolio,
            {
                "continue": "portfolio_construction",
                "error": "error_handling",
            },
        )

        graph.add_conditional_edges(
            "portfolio_construction",
            self._should_continue_to_synthesis,
            {
                "continue": "result_synthesis",
                "error": "error_handling",
            },
        )

        self.logger.info("워크플로우 엣지 초기화 완료")

    def build_graph(self) -> StateGraph:
        """
        LangGraph 워크플로우를 구축합니다.

        Returns:
            컴파일된 StateGraph
        """
        # StateGraph 생성
        graph = StateGraph(SupervisorState)

        # 노드와 엣지 초기화
        self.init_nodes(graph)
        self.init_edges(graph)

        # 그래프 컴파일
        compiled_graph = graph.compile()

        self.logger.info("Supervisor 워크플로우 구축 완료")
        return compiled_graph

    async def _start_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우를 시작합니다."""
        self.logger.info("워크플로우 시작")

        # 초기 상태 설정
        state.update(
            {
                "supervision_status": "monitoring",
                "active_agents": [],
                "alerts": [],
                "warnings": [],
                "system_health": "healthy",
                "workflow_status": "initialized",
                "current_step": "start",
                "total_steps": len(self.workflow_steps),
                "agent_states": {},
                "final_result": None,
                "execution_time": 0.0,
                "error_log": [],
            }
        )
        return state

    async def _execute_data_collection(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 수집 단계를 실행합니다."""
        self.logger.info("데이터 수집 단계 시작")

        try:
            # 상태 업데이트
            state.update(
                {
                    "current_step": "data_collection",
                    "supervision_status": "intervention",
                    "active_agents": ["data_collector"],
                }
            )

            # 데이터 수집 실행 (실제로는 다른 에이전트 호출)
            collection_result = await self._call_data_collector(state)

            # 결과 저장
            state["agent_states"]["data_collector"] = collection_result
            state["workflow_status"] = "running"

            self.logger.info("데이터 수집 단계 완료")
            return state

        except Exception as e:
            self.logger.error(f"데이터 수집 단계 실패: {e}")
            state["error_log"].append(f"데이터 수집 실패: {e}")
            state["system_health"] = "warning"
            raise

    async def _execute_data_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 분석 단계를 실행합니다."""
        self.logger.info("데이터 분석 단계 시작")

        try:
            # 상태 업데이트
            state.update(
                {
                    "current_step": "data_analysis",
                    "active_agents": ["data_collector", "analysis"],
                }
            )

            # 데이터 분석 실행 (실제로는 다른 에이전트 호출)
            analysis_result = await self._call_analysis_agent(state)

            # 결과 저장
            state["agent_states"]["analysis"] = analysis_result
            state["workflow_status"] = "running"

            self.logger.info("데이터 분석 단계 완료")
            return state

        except Exception as e:
            self.logger.error(f"데이터 분석 단계 실패: {e}")
            state["error_log"].append(f"데이터 분석 실패: {e}")
            state["system_health"] = "warning"
            raise

    async def _execute_portfolio_construction(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """포트폴리오 구성 단계를 실행합니다."""
        self.logger.info("포트폴리오 구성 단계 시작")

        try:
            # 상태 업데이트
            state.update(
                {
                    "current_step": "portfolio_construction",
                    "active_agents": ["data_collector", "analysis", "portfolio"],
                }
            )

            # 포트폴리오 구성 실행 (실제로는 다른 에이전트 호출)
            portfolio_result = await self._call_portfolio_agent(state)

            # 결과 저장
            state["agent_states"]["portfolio"] = portfolio_result
            state["workflow_status"] = "running"

            self.logger.info("포트폴리오 구성 단계 완료")
            return state

        except Exception as e:
            self.logger.error(f"포트폴리오 구성 단계 실패: {e}")
            state["error_log"].append(f"포트폴리오 구성 실패: {e}")
            state["system_health"] = "warning"
            raise

    async def _synthesize_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """최종 결과를 종합합니다."""
        self.logger.info("결과 종합 단계 시작")

        try:
            # 상태 업데이트
            state.update(
                {
                    "current_step": "result_synthesis",
                    "supervision_status": "resolved",
                    "workflow_status": "completed",
                }
            )

            # 최종 결과 생성
            final_result = self._create_final_result(state)
            state["final_result"] = final_result

            # 시스템 상태 정리
            state["system_health"] = "healthy"
            state["active_agents"] = []

            self.logger.info("결과 종합 단계 완료")
            return state

        except Exception as e:
            self.logger.error(f"결과 종합 단계 실패: {e}")
            state["error_log"].append(f"결과 종합 실패: {e}")
            state["system_health"] = "critical"
            raise

    async def _handle_errors(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """에러를 처리합니다."""
        self.logger.error("에러 처리 단계 실행")

        # 상태 업데이트
        state.update(
            {
                "workflow_status": "failed",
                "supervision_status": "intervention",
                "system_health": "critical",
                "active_agents": [],
            }
        )

        # 에러 요약 생성
        error_summary = {
            "total_errors": len(state["error_log"]),
            "errors": state["error_log"],
            "current_step": state.get("current_step", "unknown"),
            "system_health": state["system_health"],
        }

        state["final_result"] = {
            "success": False,
            "error_summary": error_summary,
            "message": "워크플로우 실행 중 오류가 발생했습니다.",
        }

        return state

    def _should_continue_to_analysis(self, state: Dict[str, Any]) -> str:
        """데이터 수집 후 분석 단계로 진행할지 결정합니다."""
        if state.get("system_health") == "healthy":
            return "continue"
        return "error"

    def _should_continue_to_portfolio(self, state: Dict[str, Any]) -> str:
        """데이터 분석 후 포트폴리오 구성 단계로 진행할지 결정합니다."""
        if state.get("system_health") == "healthy":
            return "continue"
        return "error"

    def _should_continue_to_synthesis(self, state: Dict[str, Any]) -> str:
        """포트폴리오 구성 후 결과 종합 단계로 진행할지 결정합니다."""
        if state.get("system_health") == "healthy":
            return "continue"
        return "error"

    async def _call_data_collector(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 수집 에이전트를 호출합니다."""
        # 실제 구현에서는 다른 에이전트와 통신
        # 현재는 시뮬레이션된 결과 반환

        self.logger.info("데이터 수집 에이전트 호출")

        # 시뮬레이션된 데이터 수집 결과
        collection_result = {
            "success": True,
            "data": {
                "symbols": ["AAPL", "GOOGL", "MSFT"],
                "price_data": {"AAPL": 150.0, "GOOGL": 2800.0, "MSFT": 300.0},
                "volume_data": {"AAPL": 1000000, "GOOGL": 500000, "MSFT": 800000},
                "timestamp": "2024-01-01T00:00:00Z",
            },
            "quality_score": 0.85,
            "status": "completed",
            "source_count": 3,
        }

        return collection_result

    async def _call_analysis_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """분석 에이전트를 호출합니다."""
        # 실제 구현에서는 다른 에이전트와 통신
        # 현재는 시뮬레이션된 결과 반환

        self.logger.info("분석 에이전트 호출")

        # 수집된 데이터 가져오기
        collection_data = state["agent_states"]["data_collector"]["data"]
        self.logger.info(f"분석에 사용할 수집 데이터: {len(collection_data)}개 항목")

        # 시뮬레이션된 분석 결과
        analysis_result = {
            "success": True,
            "analysis_results": {
                "technical_analysis": {
                    "trend": "bullish",
                    "support_levels": [140, 135, 130],
                    "resistance_levels": [155, 160, 165],
                    "signals": ["매수 신호", "강세 지속"],
                },
                "fundamental_analysis": {
                    "pe_ratio": 25.5,
                    "pb_ratio": 3.2,
                    "roe": 0.18,
                    "investment_attractiveness": "medium",
                },
                "sentiment_analysis": {
                    "sentiment_score": 0.7,
                    "market_mood": "optimistic",
                    "news_tone": "positive",
                },
            },
            "recommendations": [
                "현재 가격대에서 매수 고려",
                "지지선 140 달러 근처에서 매수",
                "저항선 155 달러 돌파 시 추가 매수",
            ],
            "confidence_score": 0.78,
            "status": "completed",
        }

        return analysis_result

    async def _call_portfolio_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 에이전트를 호출합니다."""
        # 실제 구현에서는 다른 에이전트와 통신
        # 현재는 시뮬레이션된 결과 반환

        self.logger.info("포트폴리오 에이전트 호출")

        # 수집된 데이터와 분석 결과 가져오기 (로깅용)
        collection_data = state["agent_states"]["data_collector"]["data"]
        analysis_data = state["agent_states"]["analysis"]["analysis_results"]

        self.logger.info(
            f"포트폴리오 구성에 사용할 데이터: {len(collection_data)}개 항목, 분석 결과: {len(analysis_data)}개 항목"
        )

        # 시뮬레이션된 포트폴리오 구성 결과
        portfolio_result = {
            "success": True,
            "portfolio": {
                "total_stocks": 15,
                "expected_return": 12.5,
                "expected_risk": 14.2,
                "sharpe_ratio": 0.88,
                "diversification_score": 0.85,
            },
            "sector_allocation": {
                "IT/반도체": 35.0,
                "화학/소재": 25.0,
                "금융": 20.0,
                "소비재": 15.0,
                "에너지": 5.0,
            },
            "stock_weights": {
                "삼성전자": 15.0,
                "SK하이닉스": 12.0,
                "LG화학": 10.0,
                "NAVER": 8.0,
                "카카오": 7.0,
            },
            "risk_metrics": {
                "portfolio_risk": 0.142,
                "var_95": 0.234,
                "max_drawdown": 0.284,
                "correlation_avg": 0.45,
            },
            "status": "completed",
            "optimization_score": 0.88,
        }

        return portfolio_result

    def _create_final_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """최종 결과를 생성합니다."""
        try:
            # 각 에이전트의 결과 수집
            collection_result = state["agent_states"].get("data_collector", {})
            analysis_result = state["agent_states"].get("analysis", {})
            portfolio_result = state["agent_states"].get("portfolio", {})

            # 최종 결과 구성
            final_result = {
                "success": True,
                "workflow_summary": {
                    "total_steps": state["total_steps"],
                    "completed_steps": state["current_step"],
                    "execution_time": state.get("execution_time", 0.0),
                    "system_health": state["system_health"],
                },
                "data_collection": {
                    "status": collection_result.get("status", "unknown"),
                    "quality_score": collection_result.get("quality_score", 0.0),
                    "data_summary": self._summarize_collection_data(collection_result),
                },
                "analysis": {
                    "status": analysis_result.get("status", "unknown"),
                    "confidence_score": analysis_result.get("confidence_score", 0.0),
                    "key_insights": self._extract_key_insights(analysis_result),
                    "recommendations": analysis_result.get("recommendations", []),
                },
                "portfolio": {
                    "status": portfolio_result.get("status", "unknown"),
                    "optimization_score": portfolio_result.get(
                        "optimization_score", 0.0
                    ),
                    "portfolio_summary": portfolio_result.get("portfolio", {}),
                    "sector_allocation": portfolio_result.get("sector_allocation", {}),
                    "stock_weights": portfolio_result.get("stock_weights", {}),
                    "risk_metrics": portfolio_result.get("risk_metrics", {}),
                },
                "overall_assessment": self._create_overall_assessment(
                    collection_result, analysis_result, portfolio_result
                ),
            }

            return final_result

        except Exception as e:
            self.logger.error(f"최종 결과 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "최종 결과 생성 중 오류가 발생했습니다.",
            }

    def _summarize_collection_data(
        self, collection_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """수집된 데이터를 요약합니다."""
        data = collection_result.get("data", {})

        summary = {
            "symbols_count": len(data.get("symbols", [])),
            "data_types": list(data.keys()),
            "quality_score": collection_result.get("quality_score", 0.0),
            "source_count": collection_result.get("source_count", 0),
        }

        return summary

    def _extract_key_insights(self, analysis_result: Dict[str, Any]) -> List[str]:
        """분석 결과에서 핵심 인사이트를 추출합니다."""
        insights = []
        analysis_results = analysis_result.get("analysis_results", {})

        # 기술적 분석 인사이트
        if "technical_analysis" in analysis_results:
            tech = analysis_results["technical_analysis"]
            if "trend" in tech:
                insights.append(f"기술적 트렌드: {tech['trend']}")
            if "signals" in tech:
                insights.extend(tech["signals"])

        # 기본적 분석 인사이트
        if "fundamental_analysis" in analysis_results:
            fund = analysis_results["fundamental_analysis"]
            if "investment_attractiveness" in fund:
                insights.append(f"투자 매력도: {fund['investment_attractiveness']}")

        # 감정 분석 인사이트
        if "sentiment_analysis" in analysis_results:
            sent = analysis_results["sentiment_analysis"]
            if "market_mood" in sent:
                insights.append(f"시장 심리: {sent['market_mood']}")

        return insights

    def _create_overall_assessment(
        self,
        collection_result: Dict[str, Any],
        analysis_result: Dict[str, Any],
        portfolio_result: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """전체적인 평가를 생성합니다."""
        # 데이터 품질과 분석 신뢰도 기반으로 종합 평가
        data_quality = collection_result.get("quality_score", 0.0)
        analysis_confidence = analysis_result.get("confidence_score", 0.0)
        portfolio_optimization = (
            portfolio_result.get("optimization_score", 0.0) if portfolio_result else 0.0
        )

        # 종합 점수 계산 (포트폴리오 점수 포함)
        if portfolio_result:
            overall_score = (
                data_quality + analysis_confidence + portfolio_optimization
            ) / 3
        else:
            overall_score = (data_quality + analysis_confidence) / 2

        # 평가 등급 결정
        if overall_score >= 0.8:
            grade = "A"
            assessment = "매우 우수"
        elif overall_score >= 0.6:
            grade = "B"
            assessment = "양호"
        elif overall_score >= 0.4:
            grade = "C"
            assessment = "보통"
        else:
            grade = "D"
            assessment = "미흡"

        return {
            "overall_score": round(overall_score, 2),
            "grade": grade,
            "assessment": assessment,
            "data_quality_score": data_quality,
            "analysis_confidence_score": analysis_confidence,
            "recommendation": self._generate_overall_recommendation(overall_score),
        }

    def _generate_overall_recommendation(self, overall_score: float) -> str:
        """전체 점수 기반으로 권장사항을 생성합니다."""
        if overall_score >= 0.8:
            return "높은 신뢰도로 투자 결정에 활용 가능"
        elif overall_score >= 0.6:
            return "적당한 신뢰도로 참고 자료로 활용"
        elif overall_score >= 0.4:
            return "낮은 신뢰도로 추가 검증 필요"
        else:
            return "매우 낮은 신뢰도로 재수집 및 재분석 권장"

    @handle_async_agent_errors
    async def execute_workflow(
        self,
        request: Dict[str, Any],
        workflow_type: str = "standard",
    ) -> Dict[str, Any]:
        """
        전체 워크플로우를 실행합니다.

        Args:
            request: 사용자 요청
            workflow_type: 워크플로우 타입

        Returns:
            워크플로우 실행 결과
        """
        self.logger.info(f"워크플로우 실행 시작: {workflow_type}")

        # 입력 상태 생성
        input_state = {
            "messages": [
                {
                    "role": "user",
                    "content": f"워크플로우 요청: {str(request)[:200]}...",
                }
            ],
            "supervision_status": "monitoring",
            "active_agents": [],
            "alerts": [],
            "warnings": [],
            "system_health": "healthy",
            "workflow_status": "initialized",
            "current_step": "start",
            "total_steps": len(self.workflow_steps),
            "agent_states": {},
            "final_result": None,
            "execution_time": 0.0,
            "error_log": [],
        }

        try:
            # 워크플로우 실행
            result = await self.graph.ainvoke(input_state)

            # 실행 시간 계산
            import time

            execution_time = time.time() - time.time()  # 실제로는 시작 시간 저장 필요
            result["execution_time"] = execution_time

            self.logger.info(f"워크플로우 실행 완료: {result['workflow_status']}")

            return {
                "success": True,
                "workflow_type": workflow_type,
                "result": result,
                "execution_time": execution_time,
            }

        except Exception as e:
            self.logger.error(f"워크플로우 실행 실패: {e}")
            return {
                "success": False,
                "workflow_type": workflow_type,
                "error": str(e),
                "execution_time": 0.0,
            }

    def get_workflow_status(self) -> Dict[str, Any]:
        """
        현재 워크플로우 상태를 반환합니다.

        Returns:
            워크플로우 상태 정보
        """
        return {
            "agent_name": getattr(self, "agent_name", "Supervisor"),
            "workflow_steps": self.workflow_steps,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "status": "ready" if self.workflow else "not_initialized",
        }
