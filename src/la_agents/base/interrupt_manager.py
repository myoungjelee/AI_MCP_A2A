"""
Interrupt Manager for LangGraph Agent System

LangGraph의 interrupt 기능을 활용한 실행 중단 및 재개 관리 시스템.
에이전트 실행 중 특정 체크포인트에서 중단하고 사용자 개입을 받을 수 있도록 합니다.

Key Features:
- Checkpoint 기반 중단점 관리
- Conditional interrupt 지원
- State inspection 및 modification
- Resume with user input
- WebSocket을 통한 실시간 상태 동기화
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphInterrupt
from pydantic import BaseModel, Field


class InterruptType(str, Enum):
    """중단 유형 정의"""

    CHECKPOINT = "checkpoint"  # 체크포인트 기반 중단
    CONDITIONAL = "conditional"  # 조건부 중단
    MANUAL = "manual"  # 수동 중단
    ERROR = "error"  # 에러 발생 중단
    TIMEOUT = "timeout"  # 타임아웃 중단


class InterruptPriority(str, Enum):
    """중단 우선순위"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InterruptReason(BaseModel):
    """중단 사유 정보"""

    type: InterruptType
    priority: InterruptPriority
    title: str
    description: str
    require_approval: bool = False
    allow_modification: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InterruptCondition(BaseModel):
    """중단 조건 정의"""

    checkpoint_id: str
    condition_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    reason: InterruptReason
    timeout_seconds: Optional[int] = None
    auto_resume: bool = False
    max_retries: int = 3


class InterruptState(BaseModel):
    """중단 상태 정보"""

    id: str
    checkpoint_id: str
    thread_id: str
    node_name: str
    state: Dict[str, Any]
    reason: InterruptReason
    created_at: datetime
    expires_at: Optional[datetime] = None
    status: str = "pending"  # pending, approved, rejected, expired, resumed
    user_input: Optional[Dict[str, Any]] = None
    modification: Optional[Dict[str, Any]] = None
    retry_count: int = 0


class InterruptResponse(TypedDict):
    """중단 응답 스키마"""

    action: str  # approve, reject, modify, resume
    user_input: Optional[Dict[str, Any]]
    modification: Optional[Dict[str, Any]]
    notes: Optional[str]


class InterruptManager:
    """
    LangGraph 에이전트의 중단점 관리 시스템

    이 클래스는 LangGraph의 interrupt 기능을 확장하여
    체크포인트 기반의 중단 및 재개 메커니즘을 제공합니다.

    주요 제한사항:
    - TradingAgent의 매수/매도 주문에만 중단점 활성화
    - 다른 에이전트나 작업은 중단 없이 진행
    """

    def __init__(
        self,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        default_timeout: int = 300,  # 5분
        enable_auto_resume: bool = False,
        trading_only: bool = True,  # 거래 전용 모드
    ):
        """
        InterruptManager 초기화

        Args:
            checkpointer: LangGraph checkpointer 인스턴스
            default_timeout: 기본 타임아웃 (초)
            enable_auto_resume: 자동 재개 활성화 여부
            trading_only: 거래 주문에만 중단점 적용 (기본값: True)
        """
        self.checkpointer = checkpointer
        self.default_timeout = default_timeout
        self.enable_auto_resume = enable_auto_resume
        self.trading_only = trading_only

        # 중단점 레지스트리
        self._interrupt_points: Dict[str, InterruptCondition] = {}

        # 활성 중단 상태
        self._active_interrupts: Dict[str, InterruptState] = {}

        # 중단 이벤트 핸들러
        self._event_handlers: Dict[str, List[Callable]] = {
            "on_interrupt": [],
            "on_resume": [],
            "on_expire": [],
            "on_approve": [],
            "on_reject": [],
        }

        # 중단 히스토리
        self._interrupt_history: List[InterruptState] = []

        # 거래 관련 체크포인트 ID 패턴
        self._trading_checkpoints = {
            "execute_order",
            "human_approval",
            "trading_execution",
            "order_submission",
            "risk_assessment",  # 고위험 거래만
        }

    def is_trading_checkpoint(self, checkpoint_id: str, state: Optional[Dict[str, Any]] = None) -> bool:
        """
        거래 관련 체크포인트인지 확인

        Args:
            checkpoint_id: 체크포인트 ID
            state: 현재 상태 (선택적, 추가 컨텍스트 확인용)

        Returns:
            bool: 거래 관련 체크포인트 여부
        """
        # 직접적인 거래 체크포인트 매칭
        if any(pattern in checkpoint_id.lower() for pattern in self._trading_checkpoints):
            return True

        # 상태 기반 확인 (있는 경우)
        if state:
            # TradingAgent의 주문 실행 노드 확인
            agent_name = state.get("agent_name", "")
            node_name = state.get("current_node", "")
            action = state.get("action", "")

            # TradingAgent의 매수/매도 주문인지 확인
            if "trading" in agent_name.lower():
                if action in ["buy", "sell"] and any(
                    keyword in node_name.lower()
                    for keyword in ["execute", "order", "approval"]
                ):
                    return True

        return False

    def register_interrupt_point(
        self,
        checkpoint_id: str,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        reason: Optional[InterruptReason] = None,
        timeout: Optional[int] = None,
        force_register: bool = False,  # 강제 등록 옵션
    ) -> None:
        """
        중단점 등록 (거래 관련 체크포인트만 허용)

        Args:
            checkpoint_id: 체크포인트 식별자
            condition: 중단 조건 함수 (state를 받아 bool 반환)
            reason: 중단 사유
            timeout: 타임아웃 시간 (초)
            force_register: 거래 전용 모드 무시하고 강제 등록

        Example:
            manager.register_interrupt_point(
                checkpoint_id="risk_assessment",
                condition=lambda state: state.get("risk_score", 0) > 0.7,
                reason=InterruptReason(
                    type=InterruptType.CONDITIONAL,
                    priority=InterruptPriority.HIGH,
                    title="High Risk Trade",
                    description="Risk score exceeds threshold",
                    require_approval=True
                )
            )
        """
        # 거래 전용 모드에서는 거래 관련 체크포인트만 등록
        if self.trading_only and not force_register:
            if not self.is_trading_checkpoint(checkpoint_id):
                # 거래 관련이 아닌 체크포인트는 무시
                return

        if reason is None:
            reason = InterruptReason(
                type=InterruptType.CHECKPOINT,
                priority=InterruptPriority.MEDIUM,
                title=f"Checkpoint: {checkpoint_id}",
                description=f"Interrupt at {checkpoint_id}",
            )

        interrupt_condition = InterruptCondition(
            checkpoint_id=checkpoint_id,
            condition_func=condition,
            reason=reason,
            timeout_seconds=timeout or self.default_timeout,
        )

        self._interrupt_points[checkpoint_id] = interrupt_condition

    async def handle_interrupt(
        self,
        state: Dict[str, Any],
        checkpoint_id: str,
        thread_id: str,
        node_name: str = "",
        config: Optional[RunnableConfig] = None,
    ) -> Dict[str, Any]:
        """
        중단 처리 (거래 관련 작업만)

        Args:
            state: 현재 에이전트 상태
            checkpoint_id: 체크포인트 ID
            thread_id: 스레드 ID
            node_name: 현재 노드 이름
            config: 실행 설정

        Returns:
            처리된 상태 또는 수정된 상태

        Raises:
            GraphInterrupt: 중단이 필요한 경우
        """
        # 거래 전용 모드에서는 거래 관련 체크포인트만 처리
        if self.trading_only:
            # 노드 이름을 상태에 추가하여 컨텍스트 제공
            state_with_context = state.copy()
            state_with_context["current_node"] = node_name

            if not self.is_trading_checkpoint(checkpoint_id, state_with_context):
                # 거래 관련이 아닌 경우 중단 없이 진행
                return state

        # 등록된 중단점 확인
        if checkpoint_id not in self._interrupt_points:
            return state

        interrupt_condition = self._interrupt_points[checkpoint_id]

        # 추가 조건: 매수/매도 주문인 경우에만 중단
        action = state.get("action", "")
        if self.trading_only and action not in ["buy", "sell"]:
            # rebalance, hold 등의 액션은 중단하지 않음
            return state

        # 조건 확인
        if interrupt_condition.condition_func:
            should_interrupt = interrupt_condition.condition_func(state)
            if not should_interrupt:
                return state

        # 중단 상태 생성
        interrupt_id = str(uuid.uuid4())
        expires_at = None
        if interrupt_condition.timeout_seconds:
            expires_at = datetime.now() + timedelta(
                seconds=interrupt_condition.timeout_seconds
            )

        interrupt_state = InterruptState(
            id=interrupt_id,
            checkpoint_id=checkpoint_id,
            thread_id=thread_id,
            node_name=node_name,
            state=state.copy(),
            reason=interrupt_condition.reason,
            created_at=datetime.now(),
            expires_at=expires_at,
        )

        # 중단 상태 저장
        self._active_interrupts[interrupt_id] = interrupt_state
        self._interrupt_history.append(interrupt_state)

        # 이벤트 핸들러 실행
        await self._trigger_event("on_interrupt", interrupt_state)

        # 자동 재개가 활성화된 경우
        if self.enable_auto_resume and interrupt_condition.auto_resume:
            await asyncio.sleep(1)  # 짧은 대기
            return await self.resume_from_interrupt(
                interrupt_id=interrupt_id,
                user_input={"auto_resumed": True},
            )

        # LangGraph interrupt 발생
        # NOTE: from langgraph.types import interrupt 로도 쓸 수 있음
        raise GraphInterrupt(
            f"Interrupt at {checkpoint_id}: {interrupt_condition.reason.title}"
        )

    async def resume_from_interrupt(
        self,
        interrupt_id: str,
        user_input: Optional[Dict[str, Any]] = None,
        modification: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        중단 상태에서 재개

        Args:
            interrupt_id: 중단 ID
            user_input: 사용자 입력
            modification: 상태 수정 사항

        Returns:
            재개된 상태
        """
        if interrupt_id not in self._active_interrupts:
            raise ValueError(f"Interrupt {interrupt_id} not found")

        interrupt_state = self._active_interrupts[interrupt_id]

        # 만료 확인
        if interrupt_state.expires_at and datetime.now() > interrupt_state.expires_at:
            interrupt_state.status = "expired"
            await self._trigger_event("on_expire", interrupt_state)
            raise TimeoutError(f"Interrupt {interrupt_id} has expired")

        # 상태 업데이트
        resumed_state = interrupt_state.state.copy()

        # 사용자 입력 적용
        if user_input:
            interrupt_state.user_input = user_input
            resumed_state.update(user_input)

        # 수정 사항 적용
        if modification:
            interrupt_state.modification = modification
            resumed_state.update(modification)

        # 상태 업데이트
        interrupt_state.status = "resumed"

        # 이벤트 핸들러 실행
        await self._trigger_event("on_resume", interrupt_state)

        # 활성 중단에서 제거
        del self._active_interrupts[interrupt_id]

        return resumed_state

    def get_pending_interrupts(
        self,
        thread_id: Optional[str] = None,
    ) -> List[InterruptState]:
        """
        대기 중인 중단 목록 조회

        Args:
            thread_id: 특정 스레드 ID (선택적)

        Returns:
            대기 중인 중단 상태 목록
        """
        pending = []
        for interrupt_state in self._active_interrupts.values():
            if interrupt_state.status == "pending":
                if thread_id is None or interrupt_state.thread_id == thread_id:
                    # 만료 확인
                    if (
                        interrupt_state.expires_at
                        and datetime.now() > interrupt_state.expires_at
                    ):
                        interrupt_state.status = "expired"
                    else:
                        pending.append(interrupt_state)

        return pending

    async def approve_interrupt(
        self,
        interrupt_id: str,
        user_input: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        중단 승인 및 재개

        Args:
            interrupt_id: 중단 ID
            user_input: 사용자 입력
            notes: 승인 메모

        Returns:
            재개된 상태
        """
        if interrupt_id not in self._active_interrupts:
            raise ValueError(f"Interrupt {interrupt_id} not found")

        interrupt_state = self._active_interrupts[interrupt_id]
        interrupt_state.status = "approved"

        # 이벤트 핸들러 실행
        await self._trigger_event("on_approve", interrupt_state)

        # 재개
        return await self.resume_from_interrupt(
            interrupt_id=interrupt_id,
            user_input=user_input,
        )

    async def reject_interrupt(
        self,
        interrupt_id: str,
        reason: Optional[str] = None,
    ) -> None:
        """
        중단 거부

        Args:
            interrupt_id: 중단 ID
            reason: 거부 사유
        """
        if interrupt_id not in self._active_interrupts:
            raise ValueError(f"Interrupt {interrupt_id} not found")

        interrupt_state = self._active_interrupts[interrupt_id]
        interrupt_state.status = "rejected"

        if reason:
            interrupt_state.metadata["rejection_reason"] = reason

        # 이벤트 핸들러 실행
        await self._trigger_event("on_reject", interrupt_state)

        # 활성 중단에서 제거
        del self._active_interrupts[interrupt_id]

    def register_event_handler(
        self,
        event: str,
        handler: Callable[[InterruptState], None],
    ) -> None:
        """
        이벤트 핸들러 등록

        Args:
            event: 이벤트 타입
            handler: 핸들러 함수
        """
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)

    async def _trigger_event(
        self,
        event: str,
        interrupt_state: InterruptState,
    ) -> None:
        """
        이벤트 트리거

        Args:
            event: 이벤트 타입
            interrupt_state: 중단 상태
        """
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(interrupt_state)
                    else:
                        handler(interrupt_state)
                except Exception as e:
                    # 핸들러 에러는 로깅만
                    print(f"Event handler error: {e}")

    def get_interrupt_history(
        self,
        thread_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[InterruptState]:
        """
        중단 히스토리 조회

        Args:
            thread_id: 특정 스레드 ID (선택적)
            limit: 최대 조회 수

        Returns:
            중단 히스토리
        """
        history = self._interrupt_history

        if thread_id:
            history = [h for h in history if h.thread_id == thread_id]

        return history[-limit:]

    def clear_expired_interrupts(self) -> int:
        """
        만료된 중단 정리

        Returns:
            정리된 중단 수
        """
        expired_ids = []
        now = datetime.now()

        for interrupt_id, interrupt_state in self._active_interrupts.items():
            if interrupt_state.expires_at and now > interrupt_state.expires_at:
                interrupt_state.status = "expired"
                expired_ids.append(interrupt_id)

        for interrupt_id in expired_ids:
            del self._active_interrupts[interrupt_id]

        return len(expired_ids)

    def get_statistics(self) -> Dict[str, Any]:
        """
        중단 통계 조회

        Returns:
            통계 정보
        """
        total = len(self._interrupt_history)
        pending = len(self.get_pending_interrupts())

        status_counts = {}
        for _interrupt in self._interrupt_history:
            status = _interrupt.status
            status_counts[status] = status_counts.get(status, 0) + 1

        type_counts = {}
        for _interrupt in self._interrupt_history:
            interrupt_type = _interrupt.reason.type
            type_counts[interrupt_type] = type_counts.get(interrupt_type, 0) + 1

        return {
            "total_interrupts": total,
            "pending_interrupts": pending,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "average_resolution_time": self._calculate_avg_resolution_time(),
        }

    def _calculate_avg_resolution_time(self) -> Optional[float]:
        """평균 해결 시간 계산"""
        resolved_times = []

        for _interrupt in self._interrupt_history:
            if _interrupt.status in ["approved", "rejected", "resumed"]:
                if _interrupt.user_input and "resolved_at" in _interrupt.metadata:
                    resolved_at = _interrupt.metadata["resolved_at"]
                    duration = (resolved_at - _interrupt.created_at).total_seconds()
                    resolved_times.append(duration)

        if resolved_times:
            return sum(resolved_times) / len(resolved_times)

        return None


# Export
__all__ = [
    "InterruptManager",
    "InterruptType",
    "InterruptPriority",
    "InterruptReason",
    "InterruptCondition",
    "InterruptState",
    "InterruptResponse",
]
