"""통합 에이전트 상태 관리 모듈"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict


class IntegratedAgentState(TypedDict):
    """통합 에이전트 상태 관리 클래스"""

    # === 기본 입력 ===
    question: str  # 사용자 질문
    session_id: Optional[str]  # 세션 ID
    timestamp: datetime  # 질문 시간

    # === 대화 히스토리 ===
    conversation_history: List[
        Dict[str, str]
    ]  # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    # === 투자 질문 검증 ===
    is_investment_related: bool  # 투자 관련 질문인지 여부
    validation_confidence: float  # 검증 신뢰도 (0.0-1.0)
    validation_reasoning: str  # 검증 이유

    # === MCP 서버 관련 ===
    available_mcp_servers: List[str]  # 사용 가능한 MCP 서버들

    # 단계별 MCP 서버 사용 현황
    current_step: (
        str  # 현재 진행 단계 ("validate", "collect", "analyze", "decide", "respond")
    )
    active_mcp_servers: List[str]  # 현재 활성화된 MCP 서버들
    mcp_server_status: Dict[
        str, str
    ]  # 각 서버별 상태 ("idle", "running", "completed", "error")
    mcp_server_actions: Dict[str, str]  # 각 서버별 현재 작업 내용
    mcp_server_results: Dict[str, Any]  # 각 서버별 결과

    # 단계별 사용된 서버 기록
    step_mcp_usage: Dict[
        str, List[str]
    ]  # {"collect": ["macroeconomic", "naver_news"], "analyze": [...]}
    total_used_servers: List[str]  # 전체 사용된 서버들 (중복 제거)

    # === 데이터 수집 ===
    collected_data: Dict[str, Any]  # 수집된 데이터
    data_collection_status: str  # 데이터 수집 상태
    data_quality_score: float  # 데이터 품질 점수

    # === 분석 결과 ===
    analysis_result: Dict[str, Any]  # 분석 결과
    analysis_confidence: float  # 분석 신뢰도
    key_insights: List[str]  # 핵심 인사이트

    # === 최종 응답 ===
    final_response: str  # 마크다운 형식 최종 응답
    response_type: str  # 응답 타입 ("analysis", "rejection", "error")

    # === 에러 처리 ===
    errors: List[Dict[str, Any]]  # 발생한 에러들
    warning_messages: List[str]  # 경고 메시지들

    # === 메타데이터 ===
    processing_start_time: datetime  # 처리 시작 시간
    processing_end_time: Optional[datetime]  # 처리 완료 시간
    total_processing_time: Optional[float]  # 총 처리 시간 (초)


def create_initial_state(
    question: str, session_id: Optional[str] = None
) -> IntegratedAgentState:
    """초기 상태 생성"""
    return IntegratedAgentState(
        question=question,
        session_id=session_id,
        timestamp=datetime.now(),
        # 대화 히스토리 초기값
        conversation_history=[],  # 빈 히스토리로 시작
        # 검증 초기값 (검증 과정 제거로 기본값으로 설정)
        is_investment_related=True,  # 모든 질문을 처리하도록 설정
        validation_confidence=1.0,
        validation_reasoning="검증 과정 생략",
        # MCP 서버 초기값
        available_mcp_servers=[
            "macroeconomic",
            "financial_analysis",
            "stock_analysis",
            "naver_news",
            "tavily_search",
            "kiwoom",
        ],
        current_step="collect",
        active_mcp_servers=[],
        mcp_server_status={},
        mcp_server_actions={},
        mcp_server_results={},
        step_mcp_usage={},
        total_used_servers=[],
        # 데이터 수집 초기값
        collected_data={},
        data_collection_status="pending",
        data_quality_score=0.0,
        # 분석 초기값
        analysis_result={},
        analysis_confidence=0.0,
        key_insights=[],
        # 응답 초기값
        final_response="",
        response_type="",
        # 에러 초기값
        errors=[],
        warning_messages=[],
        # 메타데이터 초기값
        processing_start_time=datetime.now(),
        processing_end_time=None,
        total_processing_time=None,
    )


def update_mcp_server_status(
    state: IntegratedAgentState, server_name: str, status: str, action: str = ""
) -> IntegratedAgentState:
    """MCP 서버 상태 업데이트"""
    new_state = state.copy()
    new_state["mcp_server_status"][server_name] = status
    if action:
        new_state["mcp_server_actions"][server_name] = action
    return new_state


def add_mcp_server_result(
    state: IntegratedAgentState, server_name: str, result: Any
) -> IntegratedAgentState:
    """MCP 서버 결과 추가"""
    new_state = state.copy()
    new_state["mcp_server_results"][server_name] = result
    return new_state


def update_current_step(
    state: IntegratedAgentState, step: str, active_servers: Optional[List[str]] = None
) -> IntegratedAgentState:
    """현재 단계 및 활성 서버 업데이트"""
    new_state = state.copy()
    new_state["current_step"] = step

    if active_servers is not None:
        new_state["active_mcp_servers"] = active_servers

        # 단계별 사용 서버 기록
        if step not in new_state["step_mcp_usage"]:
            new_state["step_mcp_usage"][step] = []
        new_state["step_mcp_usage"][step].extend(active_servers)

        # 전체 사용된 서버 목록 업데이트 (중복 제거)
        for server in active_servers:
            if server not in new_state["total_used_servers"]:
                new_state["total_used_servers"].append(server)

    return new_state


def add_error(
    state: IntegratedAgentState, error_message: str, error_code: str = "UNKNOWN"
) -> IntegratedAgentState:
    """에러 추가"""
    new_state = state.copy()
    error_info = {
        "message": error_message,
        "code": error_code,
        "timestamp": datetime.now().isoformat(),
        "step": state["current_step"],
    }
    new_state["errors"].append(error_info)
    return new_state


def add_warning(
    state: IntegratedAgentState, warning_message: str
) -> IntegratedAgentState:
    """경고 메시지 추가"""
    new_state = state.copy()
    new_state["warning_messages"].append(warning_message)
    return new_state


def set_processing_end_time(state: IntegratedAgentState) -> IntegratedAgentState:
    """처리 완료 시간 설정"""
    new_state = state.copy()
    end_time = datetime.now()
    new_state["processing_end_time"] = end_time

    # 총 처리 시간 계산
    start_time = new_state["processing_start_time"]
    total_time = (end_time - start_time).total_seconds()
    new_state["total_processing_time"] = total_time

    return new_state


def get_step_summary(state: IntegratedAgentState) -> Dict[str, Any]:
    """단계별 요약 정보 반환"""
    return {
        "current_step": state["current_step"],
        "active_servers": state["active_mcp_servers"],
        "step_usage": state["step_mcp_usage"],
        "total_used": state["total_used_servers"],
        "server_status": state["mcp_server_status"],
    }


def get_state_summary(state: IntegratedAgentState) -> Dict[str, Any]:
    """전체 상태 요약 정보 반환"""
    return {
        "question": state["question"],
        "session_id": state["session_id"],
        "is_investment_related": state["is_investment_related"],
        "validation_confidence": state["validation_confidence"],
        "current_step": state["current_step"],
        "total_used_servers": len(state["total_used_servers"]),
        "processing_time": state["total_processing_time"],
        "error_count": len(state["errors"]),
        "warning_count": len(state["warning_messages"]),
        "response_type": state["response_type"],
    }
