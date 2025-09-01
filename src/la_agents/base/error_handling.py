"""
에이전트 에러 처리 모듈

LangGraph 에이전트에서 발생하는 에러들을 처리하는 클래스들입니다.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """에이전트 기본 에러 클래스"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.timestamp = None


class AgentConfigurationError(AgentError):
    """에이전트 설정 에러"""
    pass


class AgentExecutionError(AgentError):
    """에이전트 실행 에러"""
    pass


class MCPConnectionError(AgentError):
    """MCP 서버 연결 에러"""
    pass


class WorkflowError(AgentError):
    """워크플로우 에러"""
    pass


class ErrorHandler:
    """에러 처리기"""
    
    def __init__(self):
        self.error_count = 0
        self.error_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("error_handler")
    
    async def handle_error(self, error: Exception, context: str = "unknown"):
        """에러 처리"""
        self.error_count += 1
        
        error_info = {
            "timestamp": None,  # datetime.now().isoformat(),
            "context": context,
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        
        self.error_history.append(error_info)
        
        # 로깅
        self.logger.error(
            f"에러 발생 (컨텍스트: {context}): {error}",
            extra={"error_info": error_info}
        )
        
        # 에러 타입별 처리
        if isinstance(error, MCPConnectionError):
            await self._handle_mcp_error(error, context)
        elif isinstance(error, WorkflowError):
            await self._handle_workflow_error(error, context)
        else:
            await self._handle_generic_error(error, context)
    
    async def _handle_mcp_error(self, error: MCPConnectionError, context: str):
        """MCP 연결 에러 처리"""
        self.logger.warning(f"MCP 연결 에러 (컨텍스트: {context}): {error}")
        # 재연결 로직 등 추가 가능
    
    async def _handle_workflow_error(self, error: WorkflowError, context: str):
        """워크플로우 에러 처리"""
        self.logger.error(f"워크플로우 에러 (컨텍스트: {context}): {error}")
        # 워크플로우 재시작 로직 등 추가 가능
    
    async def _handle_generic_error(self, error: Exception, context: str):
        """일반 에러 처리"""
        self.logger.error(f"일반 에러 (컨텍스트: {context}): {error}")
    
    def get_error_count(self) -> int:
        """에러 개수 반환"""
        return self.error_count
    
    def get_error_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """에러 히스토리 반환"""
        if limit is None:
            return self.error_history.copy()
        return self.error_history[-limit:]
    
    def clear_error_history(self):
        """에러 히스토리 초기화"""
        self.error_history.clear()
        self.error_count = 0
    
    def get_recent_errors(self, count: int = 5) -> List[Dict[str, Any]]:
        """최근 에러들 반환"""
        return self.get_error_history(limit=count)
    
    def has_errors(self) -> bool:
        """에러 발생 여부 확인"""
        return self.error_count > 0
    
    def get_error_summary(self) -> Dict[str, Any]:
        """에러 요약 정보 반환"""
        if not self.error_history:
            return {"total_errors": 0, "error_types": {}}
        
        error_types = {}
        for error in self.error_history:
            error_type = error.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": self.error_count,
            "error_types": error_types,
            "recent_errors": self.get_recent_errors(3),
        }
