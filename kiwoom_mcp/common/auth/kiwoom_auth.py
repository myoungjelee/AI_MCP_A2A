"""
키움증권 인증 관리자 래퍼

src.mcp_servers.common.auth.kiwoom_auth의 기능을 재사용합니다.
"""

import logging

from src.mcp_servers.common.auth.kiwoom_auth import (
    AuthError,
    KiwoomAuthManager,
    KiwoomOAuthError,
    TokenInfo,
    get_kiwoom_auth,
    make_kiwoom_api_call,
)

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = [
    "AuthError",
    "KiwoomAuthManager",
    "KiwoomOAuthError",
    "TokenInfo",
    "get_kiwoom_auth",
    "make_kiwoom_api_call",
]
