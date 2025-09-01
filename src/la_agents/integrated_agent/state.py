"""
단일 통합 에이전트 상태 정의

모든 기능을 통합한 단일 에이전트의 워크플로우 상태를 관리합니다.
"""

from typing import Any, Dict, List, Optional, TypedDict


class IntegratedAgentState(TypedDict):
    """통합 에이전트 상태"""

    # 입력 데이터
    request: Dict[str, Any]  # 사용자 요청
    task_type: str  # 작업 타입 (data_collection, analysis, trading, etc.)

    # 데이터 수집 단계
    collected_data: Dict[str, Any]  # 수집된 모든 데이터
    data_sources: List[str]  # 사용된 데이터 소스들
    data_quality: Dict[str, str]  # 데이터 품질 정보

    # 분석 단계
    analysis_results: Dict[str, Any]  # 분석 결과들
    insights: List[str]  # 주요 인사이트들
    correlations: Dict[str, float]  # 데이터 간 상관관계

    # 의사결정 단계
    decision: Optional[Dict[str, Any]]  # 최종 결정
    confidence: float  # 결정 신뢰도
    reasoning: str  # 결정 근거

    # 실행 단계
    action_taken: Optional[Dict[str, Any]]  # 실행된 액션
    execution_status: str  # 실행 상태

    # 처리 과정
    current_step: str  # 현재 처리 단계
    progress: float  # 진행률 (0.0 ~ 1.0)
    step_logs: List[Dict[str, Any]]  # 단계별 로그

    # 대화형 응답
    ai_response: Optional[str]  # LLM이 생성한 최종 응답 (ChatGPT 스타일)

    # 에러 및 메타데이터
    errors: List[Dict[str, Any]]  # 발생한 에러들
    metadata: Dict[str, Any]  # 메타데이터


def create_initial_state(
    request: Dict[str, Any], task_type: str = "comprehensive_analysis"
) -> IntegratedAgentState:
    """초기 상태 생성"""

    return IntegratedAgentState(
        request=request,
        task_type=task_type,
        collected_data={},
        data_sources=[],
        data_quality={},
        analysis_results={},
        insights=[],
        correlations={},
        decision=None,
        confidence=0.0,
        reasoning="",
        action_taken=None,
        execution_status="pending",
        current_step="initialized",
        progress=0.0,
        step_logs=[],
        ai_response=None,
        errors=[],
        metadata={},
    )


def update_progress(
    state: IntegratedAgentState, progress: float
) -> IntegratedAgentState:
    """진행률 업데이트"""
    state["progress"] = max(0.0, min(1.0, progress))
    return state


def add_step_log(
    state: IntegratedAgentState, step: str, message: str, level: str = "info"
) -> IntegratedAgentState:
    """단계별 로그 추가"""
    import time

    log_entry = {
        "timestamp": time.time(),
        "step": step,
        "level": level,
        "message": message,
    }

    state["step_logs"].append(log_entry)
    return state


def update_step(state: IntegratedAgentState, step: str) -> IntegratedAgentState:
    """처리 단계 업데이트"""
    state["current_step"] = step
    return state


def add_collected_data(
    state: IntegratedAgentState,
    category: str,
    data: Any,
    source: str,
    quality: str = "good",
) -> IntegratedAgentState:
    """수집된 데이터 추가"""
    import time

    if category not in state["collected_data"]:
        state["collected_data"][category] = []

    state["collected_data"][category].append(
        {
            "data": data,
            "source": source,
            "timestamp": time.time(),
        }
    )

    if source not in state["data_sources"]:
        state["data_sources"].append(source)

    state["data_quality"][category] = quality
    return state


def add_analysis_result(
    state: IntegratedAgentState, analysis_type: str, result: Any
) -> IntegratedAgentState:
    """분석 결과 추가"""
    state["analysis_results"][analysis_type] = result
    return state


def add_insight(state: IntegratedAgentState, insight: str) -> IntegratedAgentState:
    """인사이트 추가"""
    state["insights"].append(insight)
    return state


def set_decision(
    state: IntegratedAgentState,
    decision: Dict[str, Any],
) -> IntegratedAgentState:
    """의사결정 설정"""
    state["decision"] = decision
    state["confidence"] = decision.get("confidence", 0.0)
    state["reasoning"] = decision.get("reasoning", "")
    return state


def set_action_taken(
    state: IntegratedAgentState, action: Dict[str, Any], status: str = "completed"
) -> IntegratedAgentState:
    """실행된 액션 설정"""
    state["action_taken"] = action
    state["execution_status"] = status
    return state


def add_error(
    state: IntegratedAgentState, context: str, message: str
) -> IntegratedAgentState:
    """에러 추가"""
    import time

    error_entry = {
        "timestamp": time.time(),
        "error_type": "AgentError",
        "message": message,
        "context": context,
        "step": state["current_step"],
    }

    state["errors"].append(error_entry)
    return state


def get_state_summary(state: IntegratedAgentState) -> Dict[str, Any]:
    """상태 요약 반환"""
    return {
        "task_type": state["task_type"],
        "current_step": state["current_step"],
        "progress": state["progress"],
        "data_sources_count": len(state["data_sources"]),
        "analysis_results_count": len(state["analysis_results"]),
        "insights_count": len(state["insights"]),
        "decision_made": state["decision"] is not None,
        "confidence": state["confidence"],
        "execution_status": state["execution_status"],
        "error_count": len(state["errors"]),
    }
