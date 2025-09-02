#!/usr/bin/env python3
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.la_agents.base.mcp_config import MCPServerConfig


async def test_from_docker():
    """Docker 컨테이너 내에서 MCP 서버 테스트"""
    print("🔧 Docker 내부에서 MCP 서버 연결 테스트\n")

    server_configs = MCPServerConfig.get_standard_servers()

    print("📋 서버 설정:")
    for name, config in server_configs.items():
        print(f"  {name}: {config['url']}")
    print()

    # kiwoom 서버만 먼저 테스트
    kiwoom_config = {"kiwoom": server_configs["kiwoom"]}

    try:
        print("테스트 중: kiwoom")
        client = MultiServerMCPClient(kiwoom_config)
        tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
        print(f"✅ kiwoom 성공: {len(tools)}개 도구")

        for i, tool in enumerate(tools[:3]):
            print(f"  {i+1}. {tool.name}")

    except Exception as e:
        print(f"❌ kiwoom 실패: {type(e).__name__}: {e}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_from_docker())
