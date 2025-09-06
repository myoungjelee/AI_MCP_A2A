"""AI_MCP_A2A: src package initializer.

- 안전한 최소 부트스트랩(무거운 사이드이펙트 없음)
- .env가 있으면 자동 로드(선택적, 미설치 시 무시)
- 자주 쓰는 서브패키지 re-export: `agent.base`, `agent.integrated_agent`
"""

from __future__ import annotations

import os
from pathlib import Path

# 패키지/프로젝트 경로 상수
PACKAGE_ROOT: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = PACKAGE_ROOT.parent

# .env 자동 로드 (python-dotenv가 있으면만)
try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional
    load_dotenv = None  # type: ignore

if load_dotenv:
    # override=False: 이미 환경에 있는 값은 덮어쓰지 않음 (운영 안전)
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)

# 패키지 버전 (환경변수로 덮어쓰기 가능)
__version__ = os.getenv("A2A_VERSION", "0.1.0")

# 자주 쓰는 서브패키지 re-export (없어도 동작하도록 방어)
try:
    from .agent import base, integrated_agent  # noqa: F401
except Exception:  # pragma: no cover
    base = None  # type: ignore
    integrated_agent = None  # type: ignore

__all__ = [
    "base",
    "integrated_agent",
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
    "__version__",
]
