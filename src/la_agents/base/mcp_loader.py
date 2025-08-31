"""MCP 서버 도구 로더 모듈

langchain-mcp-adapters를 사용하여 MCP 서버와 연결하고
LangGraph Agent에서 사용할 도구를 로드합니다.

주요 함수들:
- load_tools_from_single_server: 단일 서버에서 도구 로드 (필터링 가능)
- load_specific_mcp_tools: 다중 서버에서 도구 로드 (병렬, 복원력 제공)
- load_specific_mcp_tools_with_filter: 다중 서버에서 필터링된 도구 로드
- _get_mcp_tools: 기존 호환성을 위한 단일 서버 로드 함수
"""

import asyncio
import logging
import os
from difflib import get_close_matches

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools

logger = logging.getLogger(__name__)

# MCP 서버 URL 매핑
# Docker 환경에서는 컨테이너 이름으로 접근

# Docker 환경인지 확인 (IS_DOCKER 환경변수로 통일)
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"

# 로그 출력
if IS_DOCKER:
    logger.info(
        "Docker environment detected (IS_DOCKER=true) - using container names for MCP servers"
    )
else:
    logger.info("Local environment detected - using localhost for MCP servers")

# Docker 환경에서는 컨테이너 이름 사용, 로컬에서는 localhost 사용
FINANCIAL_HOST = "financial-analysis-mcp" if IS_DOCKER else "localhost"
NEWS_HOST = "naver-news-mcp" if IS_DOCKER else "localhost"
TAVILY_HOST = "tavily-search-mcp" if IS_DOCKER else "localhost"
MACRO_HOST = "macroeconomic-analysis-mcp" if IS_DOCKER else "localhost"

MCP_SERVER_MAPPING = {
    # 내가 만든 MCP 서버들
    "kiwoom": f"http://{'kiwoom' if IS_DOCKER else 'localhost'}:8030/mcp",
    "stock_analysis": f"http://{'stock_analysis' if IS_DOCKER else 'localhost'}:8042/mcp",
    "financial_analysis": f"http://{'financial_analysis' if IS_DOCKER else 'localhost'}:8040/mcp",
    "macroeconomic": f"http://{'macroeconomic' if IS_DOCKER else 'localhost'}:8041/mcp",
    "naver_news": f"http://{'naver_news' if IS_DOCKER else 'localhost'}:8050/mcp",
    "tavily_search": f"http://{'tavily_search' if IS_DOCKER else 'localhost'}:3020/mcp",
}


def get_mcp_server_url(server_name: str) -> str:
    """MCP 서버 이름으로 URL 조회

    Args:
        server_name: MCP 서버 이름

    Returns:
        서버 URL
    """
    url = MCP_SERVER_MAPPING.get(server_name)
    if not url:
        raise ValueError(f"Unknown MCP server: {server_name}")
    return url


def _filter_tools(
    tools: list[BaseTool], allow: set[str] | None = None, require: bool = False
) -> list[BaseTool]:
    """도구 필터링 헬퍼 함수

    Args:
        tools: 필터링할 도구 리스트
        allow: 허용할 도구 이름 집합 (None이면 모든 도구 반환)
        require: True면 allow에 있는 모든 도구가 있어야 함

    Returns:
        필터링된 도구 리스트
    """
    if allow is None:
        return tools

    # 사용 가능한 도구 이름 수집
    available_names = {tool.name for tool in tools if hasattr(tool, "name")}

    # 누락된 필수 도구 확인
    missing = allow - available_names
    if require and missing:
        raise RuntimeError(f"Missing required MCP tools: {sorted(missing)}")

    # 필터링된 도구 반환
    return [tool for tool in tools if tool.name in allow]


async def load_tools_from_single_server(
    server_name: str,
    allow: set[str] | None = None,
    require: bool = False,
    auth_token: str | None = None,
) -> list[BaseTool]:
    """단일 MCP 서버에서 도구 로드 (필터링 및 복원력 제공)

    Args:
        server_name: 로드할 MCP 서버 이름
        allow: 허용할 도구 이름 집합 (None이면 모든 도구)
        require: True면 allow에 있는 모든 도구가 있어야 함
        auth_token: 인증 토큰 (필요한 경우)

    Returns:
        로드된 도구 리스트 (연결 실패시 빈 리스트)
    """
    try:
        server_url = get_mcp_server_url(server_name)
        logger.info(
            f"Attempting to connect to MCP server: {server_name} at {server_url}"
        )

        # 헤더 구성
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        # 단일 서버 연결 구성
        single_server_client = MultiServerMCPClient(
            {
                server_name: {
                    "transport": "streamable_http",
                    "url": server_url,
                    "headers": headers,
                }
            }
        )

        # 개별 서버 세션으로 도구 로드
        async with single_server_client.session(server_name) as session:
            tools = await load_mcp_tools(session)

        if tools:
            # 필터링 적용
            filtered_tools = _filter_tools(tools, allow, require)
            logger.info(
                f"Successfully loaded {len(tools)} tools, filtered to {len(filtered_tools)} tools from {server_name}"
            )
            return filtered_tools
        else:
            logger.warning(f"No tools found from server {server_name}")
            return []

    except Exception as e:
        logger.warning(f"Failed to connect to server {server_name}: {e}")
        return []


async def load_specific_mcp_tools_with_filter(
    server_names: list[str],
    allow: set[str] | None = None,
    require: bool = False,
    auth_token: str | None = None,
) -> list[BaseTool]:
    """특정 MCP 서버에서 도구 로드 (필터링 및 복원력 제공)

    Args:
        server_names: 로드할 MCP 서버 이름 리스트
        allow: 허용할 도구 이름 집합 (None이면 모든 도구)
        require: True면 allow에 있는 모든 도구가 있어야 함
        auth_token: 인증 토큰 (필요한 경우)

    Returns:
        로드된 도구 리스트 (성공한 서버의 도구들만)

    Note:
        개별 서버 연결 실패시에도 다른 서버들로부터 도구를 로드합니다.
        모든 서버가 실패한 경우에만 ConnectionError를 발생시킵니다.
    """
    logger.info(
        f"Attempting to load tools from {len(server_names)} MCP servers: {server_names}"
    )

    # 모든 서버에 대해 병렬로 연결 시도 (필터링 파라미터 포함)
    connection_tasks = [
        load_tools_from_single_server(server_name, allow, require, auth_token)
        for server_name in server_names
    ]

    # 모든 연결 시도를 병렬로 실행
    results = await asyncio.gather(*connection_tasks, return_exceptions=True)

    # 성공한 연결들로부터 도구 수집
    all_tools = []
    successful_servers = []
    failed_servers = []

    for server_name, result in zip(server_names, results, strict=False):
        if isinstance(result, Exception):
            # 예외가 발생한 경우
            logger.warning(f"Exception occurred for server {server_name}: {result}")
            failed_servers.append(server_name)
        elif isinstance(result, list) and result:
            # 성공적으로 도구를 로드한 경우
            all_tools.extend(result)
            successful_servers.append(server_name)
        else:
            # 빈 리스트가 반환된 경우
            logger.warning(f"No tools loaded from server {server_name}")
            failed_servers.append(server_name)

    # 결과 로깅
    if successful_servers:
        logger.info(
            f"Successfully connected to {len(successful_servers)} servers: {successful_servers}"
        )

    if failed_servers:
        logger.warning(
            f"Failed to connect to {len(failed_servers)} servers: {failed_servers}"
        )

    if all_tools:
        # Set을 사용하여 중복 도구 제거 (도구 이름 기준)
        unique_tools = {tool.name: tool for tool in all_tools}
        logger.info(
            f"Loaded {len(all_tools)} tools total, {len(unique_tools)} unique tools from {len(successful_servers)} successful connections"
        )
        return list(unique_tools.values())
    else:
        # 모든 서버가 실패한 경우에만 예외 발생
        error_msg = f"Failed to load tools from any of the servers: {server_names}. Please ensure MCP servers are running."
        logger.error(error_msg)
        raise ConnectionError(error_msg)


async def load_specific_mcp_tools(server_names: list[str]) -> list[BaseTool]:
    """특정 MCP 서버에서 도구 로드 - 개별 서버 연결 실패에 복원력 제공

    Note: 이 함수는 필터링 없이 모든 도구를 로드합니다.
    필터링이 필요한 경우 load_specific_mcp_tools_with_filter를 사용하세요.

    Args:
        server_names: 로드할 MCP 서버 이름 리스트

    Returns:
        로드된 도구 리스트 (성공한 서버의 도구들만)

    Note:
        개별 서버 연결 실패시에도 다른 서버들로부터 도구를 로드합니다.
        모든 서버가 실패한 경우에만 ConnectionError를 발생시킵니다.
    """
    logger.info(
        f"Attempting to load tools from {len(server_names)} MCP servers: {server_names}"
    )

    # 모든 서버에 대해 병렬로 연결 시도 (필터링 없음)
    connection_tasks = [
        load_tools_from_single_server(
            server_name, allow=None, require=False, auth_token=None
        )
        for server_name in server_names
    ]

    # 모든 연결 시도를 병렬로 실행
    results = await asyncio.gather(*connection_tasks, return_exceptions=True)

    # 성공한 연결들로부터 도구 수집
    all_tools = []
    successful_servers = []
    failed_servers = []

    for server_name, result in zip(server_names, results, strict=False):
        if isinstance(result, Exception):
            # 예외가 발생한 경우
            logger.warning(f"Exception occurred for server {server_name}: {result}")
            failed_servers.append(server_name)
        elif isinstance(result, list) and result:
            # 성공적으로 도구를 로드한 경우
            all_tools.extend(result)
            successful_servers.append(server_name)
        else:
            # 빈 리스트가 반환된 경우
            logger.warning(f"No tools loaded from server {server_name}")
            failed_servers.append(server_name)

    # 결과 로깅
    if successful_servers:
        logger.info(
            f"Successfully connected to {len(successful_servers)} servers: {successful_servers}"
        )

    if failed_servers:
        logger.warning(
            f"Failed to connect to {len(failed_servers)} servers: {failed_servers}"
        )

    if all_tools:
        # Set을 사용하여 중복 도구 제거 (도구 이름 기준)
        unique_tools = {tool.name: tool for tool in all_tools}
        logger.info(
            f"Loaded {len(all_tools)} tools total, {len(unique_tools)} unique tools from {len(successful_servers)} successful connections"
        )
        return list(unique_tools.values())
    else:
        # 모든 서버가 실패한 경우에만 예외 발생
        error_msg = f"Failed to load tools from any of the servers: {server_names}. Please ensure MCP servers are running."
        logger.error(error_msg)
        raise ConnectionError(error_msg)


async def test_mcp_connection(server_name: str) -> bool:
    """MCP 서버 연결 테스트

    Args:
        server_name: 테스트할 MCP 서버 이름

    Returns:
        연결 성공 여부
    """
    try:
        server_url = get_mcp_server_url(server_name)
        logger.info(f"Testing connection to MCP server: {server_name} at {server_url}")

        mcp_client = MultiServerMCPClient(
            {
                server_name: {
                    "transport": "streamable_http",
                    "url": server_url,
                }
            }
        )

        async with mcp_client.session(server_name) as session:
            tools = await load_mcp_tools(session)
            success = len(tools) > 0
            if success:
                logger.info(
                    f"Connection test successful for {server_name} - found {len(tools)} tools"
                )
            else:
                logger.warning(f"Connection test for {server_name} - no tools found")
            return success
    except Exception as e:
        logger.warning(f"Connection test failed for {server_name}: {e}")
        return False


async def test_all_mcp_connections(server_names: list[str]) -> dict[str, bool]:
    """모든 MCP 서버 연결 테스트

    Args:
        server_names: 테스트할 MCP 서버 이름 리스트

    Returns:
        서버명: 연결성공여부 딕셔너리
    """
    logger.info(f"Testing connections to {len(server_names)} MCP servers")

    # 모든 서버에 대해 병렬로 연결 테스트
    test_tasks = [test_mcp_connection(server_name) for server_name in server_names]
    results = await asyncio.gather(*test_tasks, return_exceptions=True)

    # 결과 정리
    connection_status = {}
    successful_count = 0

    for server_name, result in zip(server_names, results, strict=False):
        if isinstance(result, Exception):
            logger.warning(
                f"Exception during connection test for {server_name}: {result}"
            )
            connection_status[server_name] = False
        else:
            connection_status[server_name] = result
            if result:
                successful_count += 1

    logger.info(
        f"Connection test completed: {successful_count}/{len(server_names)} servers successful"
    )

    return connection_status


# 도구 이름 매핑 (Agent에서 사용하기 쉽도록)
TOOL_NAME_MAPPING = {
    # Market domain
    "get_price": "get_stock_basic_info",
    "get_orderbook": "get_stock_orderbook",
    "get_chart": "get_daily_chart",
    "get_minute_chart": "get_minute_chart",
    # Info domain
    "get_stock_info": "get_stock_detail_info",
    "get_stock_list": "get_stock_list",
    "get_ranking": "get_volume_top_ranking",
    # Trading domain
    "buy_stock": "place_buy_order",
    "sell_stock": "place_sell_order",
    "check_order": "get_order_status",
    # News
    "search_news": "search_news",
    "get_news": "get_stock_news",
    # Analysis
    "technical_analysis": "analyze_technical",
    "fundamental_analysis": "analyze_fundamental",
}


def get_tool_by_name(
    tools: list[BaseTool],
    name: str,
    cutoff: float = 0.6,
) -> BaseTool | None:
    """도구 이름으로 도구 조회 (difflib을 활용한 스마트 검색)

    Args:
        tools: 도구 리스트
        name: 조회할 도구 이름 (별칭 포함)
        cutoff: difflib 유사도 임계값 (0.0 ~ 1.0, 기본값: 0.6)

    Returns:
        찾은 도구 또는 None
    """
    # 1. 직접 이름으로 찾기 (정확한 일치)
    for tool in tools:
        if tool.name == name:
            return tool

    # 2. 매핑된 이름으로 찾기
    mapped_name = TOOL_NAME_MAPPING.get(name)
    if mapped_name:
        for tool in tools:
            if tool.name == mapped_name:
                return tool

    # 3. difflib을 사용한 유사도 기반 검색
    tool_names = [tool.name for tool in tools]
    close_matches = get_close_matches(name, tool_names, n=3, cutoff=cutoff)

    if close_matches:
        # 가장 유사한 도구 반환
        best_match = close_matches[0]
        logger.info(
            f"Found similar tool '{best_match}' for '{name}' (similarity: {cutoff})"
        )

        for tool in tools:
            if tool.name == best_match:
                return tool

    # 4. 부분 일치로 찾기 (fallback)
    for tool in tools:
        if name.lower() in tool.name.lower() or tool.name.lower() in name.lower():
            return tool

    # 5. 사용 가능한 도구 목록 로깅 (디버깅용)
    logger.warning(f"Tool '{name}' not found. Available tools: {sorted(tool_names)}")
    return None
