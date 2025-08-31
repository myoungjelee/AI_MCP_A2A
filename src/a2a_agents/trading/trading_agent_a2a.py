#!/usr/bin/env python3
"""
TradingAgent A2A 서버 - 공식 A2A 프로토콜 준수

공식 A2A SDK 패턴을 사용하여 TradingAgent를 A2A 프로토콜로 제공합니다.
BaseAgent + GenericAgentExecutor 패턴을 통해 스트리밍 에러를 완전히 해결합니다.
"""

import logging
import os

import structlog
import uvicorn

from src.a2a_integration.a2a_lg_utils import (
    build_a2a_starlette_application,
    build_request_handler,
    create_agent_card,
    create_agent_skill,
)
from src.a2a_integration.cors_utils import create_cors_enabled_app
from src.a2a_integration.executor_v2 import create_trading_executor

# 프로젝트 임포트

logger = structlog.get_logger(__name__)


class TradingAgentA2A:
    """
    공식 A2A 프로토콜을 준수하는 TradingAgent A2A 서버

    Key Features:
        - Human-in-the-Loop 승인 시스템
        - 리스크 평가 및 관리
        - 실시간 주문 실행 및 모니터링
        - 포트폴리오 최적화 및 리밸런싱

    Safety Mechanisms:
        - 모든 주문 실행 전 승인 요청
        - VaR(Value at Risk) 기반 리스크 평가
        - 포지션 한도 및 손실 제한 관리
    """

    def __init__(self, is_debug: bool = True):
        """
        TradingAgentA2A 초기화

        Args:
            is_debug: 디버그 모드 활성화 여부
                     True: 상세 로깅, Mock 거래 모드
                     False: 프로덕션 모드, 실제 거래 가능
        """
        self.is_debug = is_debug  # 디버그 모드 플래그
        self.react_agent = None  # LangGraph 기반 TradingAgent
        self.langgraph_agent = None  # 컴파일된 상태 그래프
        self.executor = None  # A2A 프로토콜 호환 에이전트 실행기 (LangGraphAgentExecutor)

    async def initialize(self):
        """
        LangGraph Agent 및 A2A 래퍼 초기화

        초기화 단계:
            1. A2A 호환 실행기 생성 (내부적으로 TradingAgent 생성)
            2. MCP 거래 서버 연결 (trading_domain, portfolio_domain)
            3. LangGraph 상태 그래프 검증

        Returns:
            bool: 초기화 성공 여부

        Note:
            초기화 실패 시 거래 기능이 비활성화되며,
            안전을 위해 모든 주문이 차단됩니다.
        """
        try:
            # Step 1: Executor V2를 사용하여 A2A 호환 실행기 생성
            # 내부적으로 create_trading_agent가 호출되어 LangGraph agent 생성됨
            # Human-in-the-Loop 승인 로직 포함
            self.executor = create_trading_executor(is_debug=self.is_debug)

            logger.info("TradingAgentA2A 초기화 완료 - Executor V2 사용")
            return True

        except Exception as e:
            logger.error(f"TradingAgentA2A 초기화 실패: {e}", exc_info=True)
            return False

    def get_agent_card(self, url: str):
        """A2A AgentCard 생성"""
        if os.getenv("IS_DOCKER", "false").lower() == "true":
            url = f"http://trading-agent:{os.getenv('AGENT_PORT', '8003')}"

        _skill = create_agent_skill(
            skill_id="stock_trading",
            name="주식 매매 실행",
            description="리스크 평가, Human-in-the-Loop 승인을 통해 안전하고 효율적인 주식 주문 실행 환경을 제공합니다",
            tags=[
                "trading",
                "execution",
                "risk",
                "approval",
                "safety"
            ],
            examples=[
                "삼성전자 100주 매수 주문을 실행해주세요",
                "포트폴리오 리밸런싱을 위한 매매를 진행해주세요"
            ]
        )

        return create_agent_card(
            name="TradingAgent",
            description="주식 매매 실행 전문 Agent - Human-in-the-Loop 승인을 통한 안전한 주문 실행",
            url=url,
            version="1.0.0",
            skills=[_skill],
        )


def main():
    """TradingAgent A2A 서버 실행"""
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async def async_init():
        """
        비동기 초기화 헬퍼 함수

        MCP 거래 서버와의 비동기 연결 설정.
        초기화 실패 시 안전을 위해 서버 시작을 중단.

        Returns:
            TradingAgentA2A: 초기화된 인스턴스
            None: 초기화 실패 시 (거래 차단)
        """
        try:
            _a2a_wrapper = TradingAgentA2A(is_debug=True)
            if not await _a2a_wrapper.initialize():
                logger.error("❌ TradingAgentA2A 초기화 실패")
                return None
            logger.info("✅ TradingAgentA2A 초기화 완료")
            return _a2a_wrapper
        except Exception as e:
            logger.error(f"초기화 중 오류 발생: {e}", exc_info=True)
            return None

    # 비동기 초기화 실행
    import asyncio
    a2a_agent = asyncio.run(async_init())
    if a2a_agent is None:
        return

    try:
        # 환경 설정
        is_docker = os.getenv("IS_DOCKER", "false").lower() == "true"
        host = os.getenv("AGENT_HOST", "localhost" if not is_docker else "0.0.0.0")
        port = int(os.getenv("AGENT_PORT", "8003"))
        url = f"http://{host}:{port}"

        agent_card = a2a_agent.get_agent_card(url)

        handler = build_request_handler(a2a_agent.executor)
        server_app = build_a2a_starlette_application(
            agent_card=agent_card,
            handler=handler
        )

        # CORS가 적용된 앱 생성
        app = create_cors_enabled_app(server_app)

        logger.info(f"✅ TradingAgent A2A server starting at {url} with CORS enabled")
        logger.info(f"Agent Card URL: {url}/.well-known/agent-card.json")

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
        logger.error(f"서버 시작 중 오류 발생: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
