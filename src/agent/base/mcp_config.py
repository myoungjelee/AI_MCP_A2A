#!/usr/bin/env python3
"""
MCP 서버 설정 및 클라이언트 생성 헬퍼.

표준 패턴으로 MCP 도구를 로딩하기 위한 공통 설정과 유틸리티 함수들을 제공합니다.
"""

from typing import Dict, List

import structlog
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = structlog.get_logger(__name__)


class MCPServerConfig:
    """MCP 서버 설정 관리 클래스"""

    # 표준 MCP 서버 설정 - Docker Compose에서는 컨테이너 이름 사용
    STANDARD_MCP_SERVERS = {
        # 내가 만든 MCP 서버들
        "financedatareader": {
            "transport": "streamable_http",
            "url": "http://financedatareader_mcp:8030/mcp/",
        },
        "stock_analysis": {
            "transport": "streamable_http",
            "url": "http://stock_analysis_mcp:8052/mcp/",
        },
        "financial_analysis": {
            "transport": "streamable_http",
            "url": "http://financial_analysis_mcp:8040/mcp/",
        },
        "macroeconomic": {
            "transport": "streamable_http",
            "url": "http://macroeconomic_mcp:8042/mcp/",
        },
        "naver_news": {
            "transport": "streamable_http",
            "url": "http://naver_news_mcp:8051/mcp/",
        },
        "tavily_search": {
            "transport": "streamable_http",
            "url": "http://tavily_search_mcp:8053/mcp/",
        },
    }

    # Agent별 필요한 서버 그룹 정의
    AGENT_SERVER_GROUPS = {
        "data_collector": ["financedatareader", "naver_news", "tavily_search"],
        "analysis": [
            "financedatareader",
            "stock_analysis",
            "financial_analysis",
            "macroeconomic",
            "naver_news",
            "tavily_search",
        ],
        "portfolio": ["stock_analysis", "financial_analysis", "macroeconomic"],
    }

    @classmethod
    def get_standard_servers(cls) -> Dict[str, Dict[str, str]]:
        """표준 MCP 서버 설정을 반환"""
        return cls.STANDARD_MCP_SERVERS

    @classmethod
    def get_server_configs(cls, server_names: List[str]) -> Dict[str, Dict[str, str]]:
        """지정된 서버들의 설정을 반환"""
        configs = {}

        for server_name in server_names:
            if server_name in cls.STANDARD_MCP_SERVERS:
                configs[server_name] = cls.STANDARD_MCP_SERVERS[server_name]
            else:
                logger.warning(f"Unknown MCP server: {server_name}")

        return configs

    @classmethod
    def get_agent_server_configs(cls, agent_type: str) -> Dict[str, Dict[str, str]]:
        """Agent 타입에 따른 서버 설정을 반환"""
        if agent_type not in cls.AGENT_SERVER_GROUPS:
            raise ValueError(f"Unknown agent type: {agent_type}")

        server_names = cls.AGENT_SERVER_GROUPS[agent_type]
        return cls.get_server_configs(server_names)


def get_mcp_servers_for_agent(agent_type: str) -> List[str]:
    """에이전트 타입에 따라 필요한 MCP 서버 목록 반환"""
    return MCPServerConfig.AGENT_SERVER_GROUPS.get(agent_type, [])


async def create_mcp_client_and_tools(server_configs: Dict[str, Dict[str, str]]):
    """
    표준 패턴으로 MCP 클라이언트 생성 및 도구 로딩

    Args:
        server_configs: MCP 서버 설정 딕셔너리

    Returns:
        tuple: (mcp_client, tools) - 클라이언트와 로딩된 도구들

    Example:
        server_configs = MCPServerConfig.get_agent_server_configs("data_collector")
        client, tools = await create_mcp_client_and_tools(server_configs)
    """
    try:
        if not server_configs:
            raise ValueError("No server configs provided")

        logger.info(f"Creating MCP client for servers: {list(server_configs.keys())}")

        # MultiServerMCPClient 생성 (langchain-mcp-adapters 문서에 따른 방식)
        mcp_client = MultiServerMCPClient(server_configs)

        # 도구 로딩 - 문서에 따른 올바른 방식
        try:
            # 문서 예시: client = MultiServerMCPClient(...) → tools = await client.get_tools()
            tools = await mcp_client.get_tools()
            logger.info(f"MCP 도구 로딩 성공: {len(tools)}개 도구")
        except BaseExceptionGroup as eg:
            # TaskGroup에서 발생한 모든 예외를 자세히 로깅
            logger.error(
                f"MCP 도구 로딩 실패 - TaskGroup errors: {len(eg.exceptions)} exceptions"
            )
            for i, exc in enumerate(eg.exceptions):
                logger.error(f"  Exception {i+1}: {type(exc).__name__}: {exc}")
            raise
        except Exception as e:
            logger.error(f"MCP 도구 로딩 중 예상치 못한 오류: {type(e).__name__}: {e}")
            raise

        logger.info(
            f"Successfully loaded {len(tools)} tools from {len(server_configs)} servers"
        )

        return mcp_client, tools

    except Exception as e:
        logger.error(f"Failed to create MCP client and load tools: {e}")
        # 더 자세한 에러 정보 출력
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def load_tools_for_agent(agent_type: str):
    """
    Agent 타입에 맞는 MCP 도구들을 로딩

    Args:
        agent_type: Agent 타입 ("data_collector", "analysis", "portfolio")

    Returns:
        list: 로딩된 도구들

    Example:
        tools = await load_tools_for_agent("data_collector")
    """
    try:
        server_configs = MCPServerConfig.get_agent_server_configs(agent_type)
        _, tools = await create_mcp_client_and_tools(server_configs)
        return tools

    except Exception as e:
        logger.error(f"Failed to load tools for agent {agent_type}: {e}")
        raise


# 편의 함수들
async def load_data_collector_tools():
    """데이터 수집용 MCP 도구들 로딩"""
    return await load_tools_for_agent("data_collector")


async def load_analysis_tools():
    """분석용 MCP 도구들 로딩"""
    return await load_tools_for_agent("analysis")


async def load_portfolio_tools():
    """포트폴리오용 MCP 도구들 로딩"""
    return await load_tools_for_agent("portfolio")


# 테스트 함수
async def test_mcp_connections():
    """모든 MCP 서버 연결 테스트"""
    print("🔧 MCP 서버 연결 테스트 시작")

    for agent_type in MCPServerConfig.AGENT_SERVER_GROUPS.keys():
        try:
            print(f"\n📊 {agent_type} Agent용 도구 로딩 테스트...")
            tools = await load_tools_for_agent(agent_type)
            print(f"  ✅ 성공: {len(tools)}개 도구 로딩됨")

            # 도구 이름들 출력
            tool_names = [tool.name for tool in tools[:5]]  # 처음 5개만
            print(f"  🛠️ 도구 예시: {tool_names}")

        except Exception as e:
            print(f"  ❌ 실패: {e}")

    print("\n✅ MCP 서버 연결 테스트 완료")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_mcp_connections())
