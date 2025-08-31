"""
CORS 설정을 위한 유틸리티 함수들

A2A 서버들이 브라우저에서 직접 접근 가능하도록 CORS를 설정합니다.
"""

from a2a.server.apps import A2AStarletteApplication
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware


def create_cors_enabled_app(a2a_app: A2AStarletteApplication) -> Starlette:
    """
    A2A 애플리케이션에 CORS를 적용한 Starlette 앱을 생성합니다.

    Args:
        a2a_app: A2A SDK로 생성된 Starlette 애플리케이션

    Returns:
        CORS가 적용된 Starlette 앱
    """
    # A2A 앱 빌드
    built_a2a_app = a2a_app.build()

    # 새로운 Starlette 앱 생성
    app = Starlette()

    # CORS 미들웨어를 먼저 추가 (순서 중요!)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js 개발 서버
            "http://localhost:3001",  # Next.js 대체 포트
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "*"  # 개발 환경에서는 모든 origin 허용
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,  # Preflight 캐시 시간 (1시간)
    )

    # A2A 앱을 루트에 마운트
    app.mount("/", built_a2a_app)

    return app


def get_cors_config() -> dict:
    """
    CORS 설정을 딕셔너리로 반환합니다.

    uvicorn이나 다른 서버에서 직접 사용할 수 있는 형식입니다.
    """
    return {
        "allow_origins": [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "*"
        ],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
        "max_age": 3600,
    }
