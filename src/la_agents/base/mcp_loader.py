"""
MCP 서버 로더 모듈

LangGraph 에이전트에서 MCP 서버들을 연결하고 관리하는 기능을 제공합니다.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class MCPLoader:
    """MCP 서버 로더"""
    
    def __init__(self, mcp_servers: List[str]):
        self.mcp_servers = mcp_servers
        self.connected_servers: Dict[str, Any] = {}
        self.mcp_tools: List[BaseTool] = []
        self.logger = logging.getLogger("mcp_loader")
    
    async def connect_all(self):
        """모든 MCP 서버 연결"""
        self.logger.info(f"MCP 서버 연결 시작: {self.mcp_servers}")
        
        for server_name in self.mcp_servers:
            try:
                await self._connect_server(server_name)
            except Exception as e:
                self.logger.error(f"MCP 서버 '{server_name}' 연결 실패: {e}")
        
        self.logger.info(f"MCP 서버 연결 완료: {len(self.connected_servers)}개")
    
    async def disconnect_all(self):
        """모든 MCP 서버 연결 해제"""
        self.logger.info("MCP 서버 연결 해제 시작")
        
        for server_name in list(self.connected_servers.keys()):
            try:
                await self._disconnect_server(server_name)
            except Exception as e:
                self.logger.error(f"MCP 서버 '{server_name}' 연결 해제 실패: {e}")
        
        self.logger.info("MCP 서버 연결 해제 완료")
    
    async def _connect_server(self, server_name: str):
        """개별 MCP 서버 연결"""
        try:
            # 실제 MCP 서버 연결 로직 (현재는 시뮬레이션)
            self.logger.info(f"MCP 서버 '{server_name}' 연결 중...")
            
            # 연결 시뮬레이션
            await asyncio.sleep(0.1)
            
            # 연결 성공 시 서버 정보 저장
            self.connected_servers[server_name] = {
                "name": server_name,
                "status": "connected",
                "tools": await self._load_server_tools(server_name)
            }
            
            self.logger.info(f"MCP 서버 '{server_name}' 연결 성공")
            
        except Exception as e:
            self.logger.error(f"MCP 서버 '{server_name}' 연결 실패: {e}")
            raise
    
    async def _disconnect_server(self, server_name: str):
        """개별 MCP 서버 연결 해제"""
        if server_name in self.connected_servers:
            self.logger.info(f"MCP 서버 '{server_name}' 연결 해제 중...")
            
            # 연결 해제 시뮬레이션
            await asyncio.sleep(0.1)
            
            del self.connected_servers[server_name]
            self.logger.info(f"MCP 서버 '{server_name}' 연결 해제 완료")
    
    async def _load_server_tools(self, server_name: str) -> List[BaseTool]:
        """서버에서 도구들 로딩"""
        # 실제 MCP 도구 로딩 로직 (현재는 시뮬레이션)
        tools = []
        
        # 서버별 도구 매핑
        server_tools = {
            "macroeconomic": ["collect_data", "analyze_trends", "get_statistics"],
            "financial_analysis": ["get_financial_data", "calculate_ratios", "perform_dcf"],
            "stock_analysis": ["analyze_data_trends", "calculate_indicators", "get_recommendations"],
            "naver_news": ["search_news", "get_news_content", "analyze_sentiment"],
            "tavily_search": ["search", "get_search_results", "summarize_results"],
            "kiwoom": ["get_stock_info", "place_order", "get_account_info"],
        }
        
        if server_name in server_tools:
            for tool_name in server_tools[server_name]:
                tool = self._create_mock_tool(server_name, tool_name)
                tools.append(tool)
        
        return tools
    
    def _create_mock_tool(self, server_name: str, tool_name: str) -> BaseTool:
        """목업 도구 생성"""
        from langchain_core.tools import tool
        
        @tool
        async def mock_tool(**kwargs):
            """목업 도구"""
            return f"Mock result from {server_name}.{tool_name}: {kwargs}"
        
        mock_tool.name = f"{server_name}_{tool_name}"
        mock_tool.description = f"Mock tool for {server_name}.{tool_name}"
        
        return mock_tool
    
    def get_connected_servers(self) -> List[str]:
        """연결된 서버 목록 반환"""
        return list(self.connected_servers.keys())
    
    def get_server_status(self, server_name: str) -> Optional[Dict[str, Any]]:
        """서버 상태 반환"""
        return self.connected_servers.get(server_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """모든 도구 반환"""
        all_tools = []
        for server_info in self.connected_servers.values():
            all_tools.extend(server_info.get("tools", []))
        return all_tools
    
    def get_server_tools(self, server_name: str) -> List[BaseTool]:
        """특정 서버의 도구들 반환"""
        server_info = self.connected_servers.get(server_name)
        if server_info:
            return server_info.get("tools", [])
        return []
    
    def is_server_connected(self, server_name: str) -> bool:
        """서버 연결 여부 확인"""
        return server_name in self.connected_servers
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """연결 요약 정보 반환"""
        return {
            "total_servers": len(self.mcp_servers),
            "connected_servers": len(self.connected_servers),
            "server_names": list(self.connected_servers.keys()),
            "total_tools": len(self.get_all_tools()),
        }


async def test_mcp_connection(server_name: str) -> bool:
    """MCP 서버 연결 테스트"""
    try:
        loader = MCPLoader([server_name])
        await loader.connect_all()
        is_connected = loader.is_server_connected(server_name)
        await loader.disconnect_all()
        return is_connected
    except Exception as e:
        logger.error(f"MCP 서버 '{server_name}' 연결 테스트 실패: {e}")
        return False


async def load_specific_mcp_tools(server_names: List[str]) -> List[BaseTool]:
    """특정 MCP 서버들의 도구들을 로딩"""
    try:
        loader = MCPLoader(server_names)
        await loader.connect_all()
        tools = loader.get_all_tools()
        await loader.disconnect_all()
        return tools
    except Exception as e:
        logger.error(f"MCP 도구 로딩 실패: {e}")
        return []
