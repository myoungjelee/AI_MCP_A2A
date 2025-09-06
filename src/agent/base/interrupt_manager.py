"""
에이전트 인터럽트 관리 모듈

LangGraph 에이전트의 실행을 중단하고 관리하는 기능을 제공합니다.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class InterruptManager:
    """에이전트 인터럽트 관리자"""

    def __init__(self):
        self.interrupt_count = 0
        self.is_interrupted = False
        self.interrupt_reason = None
        self.callback_handlers: List[BaseCallbackHandler] = []
        self.logger = logging.getLogger("interrupt_manager")

    def interrupt(self, reason: Optional[str] = None):
        """인터럽트 설정"""
        self.is_interrupted = True
        self.interrupt_reason = reason or "사용자 요청"
        self.interrupt_count += 1

        self.logger.info(f"인터럽트 설정됨: {self.interrupt_reason}")

    def clear_interrupt(self):
        """인터럽트 해제"""
        self.is_interrupted = False
        self.interrupt_reason = None
        self.logger.info("인터럽트 해제됨")

    def should_interrupt(self) -> bool:
        """인터럽트 여부 확인"""
        return self.is_interrupted

    def get_interrupt_count(self) -> int:
        """인터럽트 횟수 반환"""
        return self.interrupt_count

    def get_interrupt_reason(self) -> Optional[str]:
        """인터럽트 이유 반환"""
        return self.interrupt_reason

    def get_callback(self) -> BaseCallbackHandler:
        """LangChain 콜백 핸들러 반환"""
        return InterruptCallbackHandler(self)

    def add_callback_handler(self, handler: BaseCallbackHandler):
        """콜백 핸들러 추가"""
        self.callback_handlers.append(handler)

    def remove_callback_handler(self, handler: BaseCallbackHandler):
        """콜백 핸들러 제거"""
        if handler in self.callback_handlers:
            self.callback_handlers.remove(handler)

    def get_status(self) -> Dict[str, Any]:
        """인터럽트 상태 반환"""
        return {
            "is_interrupted": self.is_interrupted,
            "interrupt_count": self.interrupt_count,
            "interrupt_reason": self.interrupt_reason,
            "callback_handlers_count": len(self.callback_handlers),
        }


class InterruptCallbackHandler(BaseCallbackHandler):
    """LangChain 인터럽트 콜백 핸들러"""

    def __init__(self, interrupt_manager: InterruptManager):
        super().__init__()
        self.interrupt_manager = interrupt_manager
        self.logger = logging.getLogger("interrupt_callback")

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """체인 시작 시 인터럽트 체크"""
        if self.interrupt_manager.should_interrupt():
            self.logger.info("체인 시작 시 인터럽트 감지")
            raise InterruptError("에이전트 실행이 인터럽트되었습니다")

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """체인 종료 시 인터럽트 체크"""
        if self.interrupt_manager.should_interrupt():
            self.logger.info("체인 종료 시 인터럽트 감지")
            raise InterruptError("에이전트 실행이 인터럽트되었습니다")

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """도구 시작 시 인터럽트 체크"""
        if self.interrupt_manager.should_interrupt():
            self.logger.info("도구 시작 시 인터럽트 감지")
            raise InterruptError("에이전트 실행이 인터럽트되었습니다")

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """도구 종료 시 인터럽트 체크"""
        if self.interrupt_manager.should_interrupt():
            self.logger.info("도구 종료 시 인터럽트 감지")
            raise InterruptError("에이전트 실행이 인터럽트되었습니다")


class InterruptError(Exception):
    """인터럽트 에러"""

    pass


class TimeoutManager:
    """타임아웃 관리자"""

    def __init__(self, default_timeout: float = 300.0):  # 5분 기본값
        self.default_timeout = default_timeout
        self.timeout_count = 0
        self.logger = logging.getLogger("timeout_manager")

    async def run_with_timeout(
        self,
        coro,
        timeout: Optional[float] = None,
        timeout_message: Optional[str] = None,
    ):
        """타임아웃과 함께 코루틴 실행"""
        timeout = timeout or self.default_timeout

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            self.timeout_count += 1
            message = timeout_message or f"작업이 {timeout}초 후 타임아웃되었습니다"
            self.logger.warning(f"타임아웃 발생: {message}")
            raise TimeoutError(message)

    def get_timeout_count(self) -> int:
        """타임아웃 횟수 반환"""
        return self.timeout_count

    def reset_timeout_count(self):
        """타임아웃 횟수 초기화"""
        self.timeout_count = 0


class TimeoutError(Exception):
    """타임아웃 에러"""

    pass
