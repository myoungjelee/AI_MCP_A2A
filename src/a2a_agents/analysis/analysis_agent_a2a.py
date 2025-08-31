#!/usr/bin/env python3
"""
AnalysisAgent A2A 서버 - 공식 A2A 프로토콜 준수

공식 A2A SDK 패턴을 사용하여 AnalysisAgent를 A2A 프로토콜로 제공합니다.
BaseAgent + GenericAgentExecutor 패턴을 통해 스트리밍 에러를 완전히 해결합니다.

Architecture Overview:
    LangGraph AnalysisAgent -> A2A Wrapper -> A2A Protocol Server

Key Features:
    - 기술적, 기본적, 감성, 거시경제 분석 통합
    - MCP(Model Context Protocol) 서버와의 실시간 연동
    - 스트리밍 응답 지원을 통한 실시간 분석 결과 제공
    - 표준 A2A 프로토콜 준수로 다른 에이전트와의 상호운용성 보장
"""

# 표준 라이브러리 임포트
import logging  # 로깅 설정 - 디버깅 및 모니터링
import os  # 환경 변수 및 시스템 관련 작업

import structlog  # 구조화된 로깅 - JSON 형식의 구조화된 로그
import uvicorn

from src.a2a_integration.a2a_lg_utils import (
    build_a2a_starlette_application,
    build_request_handler,
    create_agent_card,
    create_agent_skill,
)
from src.a2a_integration.cors_utils import create_cors_enabled_app
from src.a2a_integration.executor_v2 import create_analysis_executor

# 프로젝트 내부 임포트

logger = structlog.get_logger(__name__)


class AnalysisAgentA2A:
    """
    공식 A2A 프로토콜을 준수하는 AnalysisAgent A2A 서버
    """

    def __init__(self, is_debug: bool = True):
        """
        AnalysisAgentA2A 초기화

        Args:
            is_debug: 디버그 모드 활성화 여부. True일 경우 상세한 로깅 출력
        """
        self.is_debug = is_debug  # 디버그 모드 플래그
        self.react_agent = None  # LangGraph 기반 AnalysisAgent 인스턴스
        self.langgraph_agent = None  # 컴파일된 LangGraph 상태 그래프
        self.executor = None  # A2A 프로토콜 호환 에이전트 실행기 (LangGraphAgentExecutor)

    async def initialize(self):
        """
        LangGraph Agent 및 A2A 래퍼 초기화

        이 메서드는 다음 작업을 수행합니다:
        1. A2A 호환 실행기 생성 (내부적으로 AnalysisAgent 생성)
        2. MCP 서버와의 연결 및 도구 초기화
        3. LangGraph 상태 그래프 검증

        Returns:
            bool: 초기화 성공 시 True, 실패 시 False
        """
        try:
            # Step 1: Executor V2를 사용하여 A2A 호환 실행기 생성
            # 내부적으로 create_analysis_agent가 호출되어 LangGraph agent 생성됨
            self.executor = create_analysis_executor(is_debug=self.is_debug)

            logger.info("AnalysisAgentA2A 초기화 완료 - Executor V2 사용")
            return True

        except Exception as e:
            # 초기화 실패 시 상세한 에러 로그 기록
            logger.error(f"AnalysisAgentA2A 초기화 실패: {e}", exc_info=True)
            return False

    def get_agent_card(self, url: str):
        """
        A2A AgentCard 생성

        AgentCard는 에이전트의 메타데이터와 기능을 설명하는 표준화된 문서입니다.
        다른 에이전트나 시스템이 이 에이전트의 기능을 이해하고 상호작용할 수 있도록 합니다.

        Args:
            url: 에이전트 서버의 기본 URL

        Returns:
            AgentCard: 에이전트 메타데이터 카드
        """
        # Docker 환경에서는 서비스 이름을 사용하여 내부 통신
        if os.getenv("IS_DOCKER", "false").lower() == "true":
            url = f"http://analysis-agent:{os.getenv('AGENT_PORT', '8002')}"
        _skill = create_agent_skill(
            skill_id="stock_analysis",
            name="통합 주식 분석",
            description="기술적, 기본적, 거시경제, 감성 분석을 통합하여 종합적인 투자 신호와 인사이트를 생성합니다",
            tags=[
                "analysis",
                "technical",
                "fundamental",
                "macro",
                "sentiment"
            ],
            examples=[
                "삼성전자의 종합적인 투자 분석을 해주세요",
                "KOSPI 시장 전체의 거시경제 분석을 진행해주세요"
            ]
        )

        return create_agent_card(
            name="AnalysisAgent",
            description="주식 분석 전문 Agent - 기술적/기본적/감성/거시경제 통합 분석",
            url=url,
            version="1.0.0",
            skills=[_skill],
        )

def main():
    """
    AnalysisAgent A2A 서버 실행

    이 함수는 서버 실행의 진입점으로, 다음 작업을 수행합니다:
    1. 로깅 설정
    2. 비동기 초기화 실행
    3. 환경 설정 로드
    4. A2A 서버 생성 및 실행
    """
    # 로깅 설정 - INFO 레벨로 설정하여 중요한 정보만 출력
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async def async_init():
        """
        비동기 초기화 헬퍼 함수

        MCP 서버와의 비동기 연결이 필요하므로 별도의 비동기 함수로 분리.

        Returns:
            AnalysisAgentA2A: 초기화된 A2A 래퍼 인스턴스 또는 None
        """
        try:
            # AnalysisAgentA2A 인스턴스 생성 (디버그 모드 활성화)
            _a2a_wrapper = AnalysisAgentA2A(is_debug=True)

            # 비동기 초기화 실행 및 결과 확인
            if not await _a2a_wrapper.initialize():
                logger.error("❌ AnalysisAgentA2A 초기화 실패")
                return None

            logger.info("✅ AnalysisAgentA2A 초기화 완료")
            return _a2a_wrapper

        except Exception as e:
            # 초기화 중 발생한 예외 처리
            logger.error(f"초기화 중 오류 발생: {e}", exc_info=True)
            return None

    # 비동기 초기화 실행
    import asyncio
    a2a_agent = asyncio.run(async_init())

    # 초기화 실패 시 조기 종료
    if a2a_agent is None:
        return

    try:
        # 환경 변수에서 서버 설정 로드
        # Docker 환경 여부 확인 - Docker에서는 모든 인터페이스에서 수신
        is_docker = os.getenv("IS_DOCKER", "false").lower() == "true"

        # 호스트 설정: Docker는 0.0.0.0, 로컬은 localhost
        host = os.getenv("AGENT_HOST", "localhost" if not is_docker else "0.0.0.0")
        port = int(os.getenv("AGENT_PORT", "8002"))
        url = f"http://{host}:{port}"

        agent_card = a2a_agent.get_agent_card(url)

        # A2A 서버 생성 - 기존에 생성된 executor 사용
        # Agent 인스턴스 기반으로 이미 생성된 executor를 직접 사용
        handler = build_request_handler(a2a_agent.executor)
        server_app = build_a2a_starlette_application(
            agent_card=agent_card,
            handler=handler
        )

        # CORS가 적용된 앱 생성
        app = create_cors_enabled_app(server_app)

        # 서버 시작 정보 로깅
        logger.info(f"✅ AnalysisAgent A2A server starting at {url} with CORS enabled")
        logger.info(f"📋 Agent Card URL: {url}/.well-known/agent-card.json")  # A2A 표준 메타데이터 엔드포인트
        logger.info(f"🩺 Health Check: {url}/health")  # 헬스체크 엔드포인트

        # uvicorn 서버 직접 실행
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=False,
            reload=False,
            timeout_keep_alive=1000,
            timeout_notify=1000,
            ws_ping_interval=30,
            ws_ping_timeout=60,
            limit_max_requests=None,
            timeout_graceful_shutdown=10,
        )
        server = uvicorn.Server(config)
        server.run()

    except Exception as e:
        # 서버 시작 실패 시 에러 로깅 및 예외 재발생
        logger.error(f"서버 시작 중 오류 발생: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
