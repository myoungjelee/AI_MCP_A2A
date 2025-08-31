#!/usr/bin/env python3
"""
DataCollectorAgent A2A 서버 - 공식 A2A 프로토콜 준수

공식 A2A SDK 패턴을 사용하여 DataCollectorAgent를 A2A 프로토콜로 제공합니다.
BaseAgent + GenericAgentExecutor 패턴을 통해 스트리밍 에러를 완전히 해결합니다.

Core Responsibilities:
    - 실시간 시장 데이터 수집 (시세, 차트, 거래량)
    - 종목 정보 및 재무 데이터 수집
    - 뉴스 및 공시 정보 실시간 모니터링
    - 투자자 동향 및 매매 패턴 분석 데이터 수집

Data Sources:
    - MCP 서버를 통한 실시간 시장 데이터
    - 외부 API를 통한 뉴스 및 경제 지표
    - 웹 크롤링을 통한 추가 정보 수집
"""

# 표준 라이브러리 임포트
import logging  # 시스템 로깅
import os  # 환경 변수 관리

# 외부 라이브러리 임포트
import structlog  # 구조화된 로깅 시스템
import uvicorn

# A2A SDK 임포트 - Agent-to-Agent 통신 프로토콜
from a2a.types import AgentCard  # 에이전트 메타데이터 정의

from src.a2a_integration.a2a_lg_utils import (
    build_a2a_starlette_application,
    build_request_handler,
    create_agent_card,
    create_agent_skill,
)
from src.a2a_integration.cors_utils import create_cors_enabled_app
from src.a2a_integration.executor_v2 import create_data_collector_executor

# 프로젝트 내부 임포트

logger = structlog.get_logger(__name__)

class DataCollectorAgentA2A:
    """
    공식 A2A 프로토콜을 준수하는 DataCollectorAgent A2A 서버
    """

    def __init__(self, is_debug: bool = True):
        """
        DataCollectorAgentA2A 초기화

        Args:
            is_debug: 디버그 모드 활성화 여부

        """
        self.is_debug = is_debug  # 디버그 모드 플래그
        self.react_agent = None  # LangGraph 기반 DataCollectorAgent 인스턴스
        self.langgraph_agent = None  # 컴파일된 LangGraph 상태 그래프
        self.executor = None  # A2A 프로토콜 호환 에이전트 실행기 (LangGraphAgentExecutor)

    async def initialize(self):
        """
        LangGraph Agent 및 A2A 래퍼 초기화

        초기화 프로세스:
            1. A2A 호환 실행기 생성 (내부적으로 DataCollectorAgent 생성)
            2. MCP 서버 연결 및 도구 초기화
            3. LangGraph 상태 그래프 검증

        Returns:
            bool: 초기화 성공 여부

        Raises:
            ValueError: LangGraph 컴파일 실패 시
            ConnectionError: MCP 서버 연결 실패 시
        """
        try:
            # Step 1: Executor V2를 사용하여 A2A 호환 실행기 생성
            # 내부적으로 create_data_collector_agent가 호출되어 LangGraph agent 생성됨
            self.executor = create_data_collector_executor(is_debug=self.is_debug)

            logger.info("DataCollectorAgentA2A 초기화 완료 - Executor V2 사용")
            return True

        except Exception as e:
            logger.error(f"DataCollectorAgentA2A 초기화 실패: {e}", exc_info=True)
            return False

    def get_agent_card(self, url: str) -> AgentCard:
        """A2A AgentCard 생성"""
        if os.getenv("IS_DOCKER", "false").lower() == "true":
            url = f"http://data-collector-agent:{os.getenv('AGENT_PORT', '8001')}"
        _skill = create_agent_skill(
            skill_id="stock_data_collection",
            name="주식 데이터 수집",
            description="실시간 시세, 차트, 뉴스, 재무정보 등 주식 투자에 필요한 모든 데이터를 수집합니다",
            tags=[
                "stock",
                "data",
                "market",
                "news",
                "financial"
            ],
            examples=[
                "삼성전자의 현재 시세와 최근 뉴스를 수집해주세요",
                "KOSPI 200 종목들의 실시간 데이터를 가져와주세요"
            ]
        )
        agent_card = create_agent_card(
            name="DataCollectorAgent",
            description="주식 데이터 수집 전문 Agent - 실시간 시세, 차트, 뉴스, 재무정보 수집",
            url=url,
            version="1.0.0",
            skills=[_skill]
        )

        return agent_card

def main():
    """DataCollectorAgent A2A 서버 실행"""
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    async def async_init():
        """
        비동기 초기화 헬퍼 함수

        MCP 서버와의 비동기 연결이 필요하므로 별도의 비동기 함수로 분리.
        초기화 실패 시 None을 반환하여 서버 시작을 중단.

        Returns:
            DataCollectorAgentA2A: 초기화된 인스턴스
            None: 초기화 실패 시
        """
        try:
            _a2a_wrapper = DataCollectorAgentA2A(is_debug=False)
            if not await _a2a_wrapper.initialize():
                logger.error("❌ DataCollectorAgentA2A 초기화 실패")
                return None
            logger.info("✅ DataCollectorAgentA2A 초기화 완료")
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
        port = int(os.getenv("AGENT_PORT", "8001"))
        url = f"http://{host}:{port}"

        handler = build_request_handler(a2a_agent.executor)
        server_app = build_a2a_starlette_application(
            agent_card=a2a_agent.get_agent_card(url),
            handler=handler
        )

        # CORS가 적용된 앱 생성
        app = create_cors_enabled_app(server_app)

        logger.info(f"✅ DataCollectorAgent A2A server starting at {url} with CORS enabled")
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
