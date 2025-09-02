#!/usr/bin/env python3
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.la_agents.base.mcp_config import MCPServerConfig


async def test_all_servers_individually():
    """모든 MCP 서버를 개별적으로 테스트"""
    print("🔧 Docker 내부에서 개별 MCP 서버 연결 테스트\n")

    server_configs = MCPServerConfig.get_standard_servers()

    working_servers = []
    failing_servers = []

    for server_name, config in server_configs.items():
        try:
            print(f"테스트 중: {server_name} ({config['url']})")

            # 개별 서버만으로 클라이언트 생성
            single_config = {server_name: config}
            client = MultiServerMCPClient(single_config)

            # 10초 타임아웃으로 도구 로딩 시도
            tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
            print(f"  ✅ 성공: {len(tools)}개 도구")
            working_servers.append(server_name)

            # 도구 이름들 출력 (처음 3개만)
            if tools:
                tool_names = [tool.name for tool in tools[:3]]
                print(f"  🛠️ 도구 예시: {tool_names}")

        except asyncio.TimeoutError:
            print(f"  ❌ 타임아웃: {server_name}")
            failing_servers.append(f"{server_name} (timeout)")
        except Exception as e:
            print(f"  ❌ 실패: {server_name} - {type(e).__name__}: {e}")
            failing_servers.append(f"{server_name} ({type(e).__name__})")

        print()  # 빈 줄 추가

    print("📊 테스트 결과 요약:")
    print(f"  ✅ 정상 작동: {len(working_servers)}개 - {working_servers}")
    print(f"  ❌ 문제 발생: {len(failing_servers)}개 - {failing_servers}")

    # 정상 작동하는 서버들로만 연결 테스트
    if working_servers:
        print(f"\n🔄 정상 서버들 ({len(working_servers)}개)로 통합 연결 테스트...")
        try:
            working_configs = {name: server_configs[name] for name in working_servers}
            combined_client = MultiServerMCPClient(working_configs)
            all_tools = await asyncio.wait_for(
                combined_client.get_tools(), timeout=15.0
            )
            print(f"  ✅ 통합 연결 성공: {len(all_tools)}개 도구 로딩")
        except Exception as e:
            print(f"  ❌ 통합 연결 실패: {type(e).__name__}: {e}")

    return working_servers, failing_servers


if __name__ == "__main__":
    asyncio.run(test_all_servers_individually())
