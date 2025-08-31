"""
Kiwoom API 연동 MCP 서버 (개발 기술 중심)

키움증권 API를 연동하는 단순한 MCP 서버입니다.
실제 트레이딩 로직은 제거하고 API 연동 기술을 어필합니다.

주요 기능:
- 주식 가격 및 정보 조회
- 계좌 정보 조회
- 시장 상태 조회
- 에러 처리 및 재시도
- 캐싱 및 성능 최적화

개발 기술 어필:
- FastMCP 기반 MCP 서버 구현
- 비동기 HTTP 클라이언트 (httpx)
- 지수 백오프 재시도 로직
- 메모리 캐싱 시스템
- 체계적인 에러 처리
- 로깅 및 모니터링
"""

from .client import (
    KiwoomClient,
    KiwoomDataType,
    KiwoomError,
    KiwoomRecord,
)
from .server import KiwoomMCPServer

__version__ = "1.0.0"
__all__ = [
    "KiwoomClient",
    "KiwoomError",
    "KiwoomDataType",
    "KiwoomRecord",
    "KiwoomMCPServer",
]
