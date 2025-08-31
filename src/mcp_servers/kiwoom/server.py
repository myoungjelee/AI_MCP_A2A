"""
Kiwoom API 연동 MCP 서버 (개발 기술 중심)

키움증권 API를 연동하는 단순한 MCP 서버입니다.
실제 트레이딩 로직은 제거하고 API 연동 기술을 어필합니다.
"""

import logging
from typing import Any, Dict

from fastmcp import FastMCP

from .client import KiwoomClient, KiwoomError


class KiwoomMCPServer:
    """키움 API 연동 MCP 서버 (개발 기술 중심)"""

    def __init__(self, port: int = 8030, host: str = "0.0.0.0"):
        """서버 초기화"""
        self.port = port
        self.host = host
        self.logger = logging.getLogger("kiwoom_mcp_server")
        self._setup_logging()

        # FastMCP 인스턴스 생성
        self.fastmcp = FastMCP(
            name="kiwoom_api_server",
            description="키움 API 연동 시스템 - 주식 데이터 조회 및 계좌 정보 제공",
            instructions="""
            키움증권 API를 연동하여 다음 기능을 제공합니다:
            - 주식 가격 및 정보 조회
            - 계좌 정보 조회
            - 시장 상태 조회
            - 에러 처리 및 재시도
            - 캐싱 및 성능 최적화

            실제 트레이딩 기능은 제공하지 않으며, 데이터 조회 중심으로 동작합니다.
            """,
            tools=[
                {
                    "name": "get_stock_price",
                    "description": "특정 종목의 현재 가격 정보를 조회합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stock_code": {
                                "type": "string",
                                "description": "종목 코드 (예: 005930)",
                            }
                        },
                        "required": ["stock_code"],
                    },
                },
                {
                    "name": "get_account_info",
                    "description": "연결된 계좌의 기본 정보를 조회합니다",
                    "parameters": {"type": "object", "properties": {}},
                },
                {
                    "name": "get_stock_info",
                    "description": "특정 종목의 기본 정보를 조회합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stock_code": {
                                "type": "string",
                                "description": "종목 코드 (예: 005930)",
                            }
                        },
                        "required": ["stock_code"],
                    },
                },
                {
                    "name": "get_market_status",
                    "description": "현재 시장 상태를 조회합니다",
                    "parameters": {"type": "object", "properties": {}},
                },
            ],
        )

        # 키움 클라이언트 초기화
        self.kiwoom_client = KiwoomClient(name="mcp_server_client")

        # 도구 등록
        self._register_tools()

        self.logger.info(f"키움 MCP 서버 초기화 완료 (포트: {port})")

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _register_tools(self):
        """FastMCP 도구 등록"""

        @self.fastmcp.tool()
        async def get_stock_price(stock_code: str) -> Dict[str, Any]:
            """주식 가격 조회"""
            try:
                self.logger.info(f"주식 가격 조회 요청: {stock_code}")
                result = await self.kiwoom_client.get_stock_price(stock_code)
                self.logger.info(f"주식 가격 조회 성공: {stock_code}")
                return {
                    "success": True,
                    "data": result,
                    "message": f"{stock_code} 종목 가격 조회 완료",
                }
            except KiwoomError as e:
                self.logger.error(f"주식 가격 조회 실패: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"{stock_code} 종목 가격 조회 실패",
                }
            except Exception as e:
                self.logger.error(f"예상치 못한 에러: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "시스템 오류가 발생했습니다",
                }

        @self.fastmcp.tool()
        async def get_account_info() -> Dict[str, Any]:
            """계좌 정보 조회"""
            try:
                self.logger.info("계좌 정보 조회 요청")
                result = await self.kiwoom_client.get_account_info()
                self.logger.info("계좌 정보 조회 성공")
                return {
                    "success": True,
                    "data": result,
                    "message": "계좌 정보 조회 완료",
                }
            except KiwoomError as e:
                self.logger.error(f"계좌 정보 조회 실패: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "계좌 정보 조회 실패",
                }
            except Exception as e:
                self.logger.error(f"예상치 못한 에러: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "시스템 오류가 발생했습니다",
                }

        @self.fastmcp.tool()
        async def get_stock_info(stock_code: str) -> Dict[str, Any]:
            """주식 기본 정보 조회"""
            try:
                self.logger.info(f"주식 정보 조회 요청: {stock_code}")
                result = await self.kiwoom_client.get_stock_info(stock_code)
                self.logger.info(f"주식 정보 조회 성공: {stock_code}")
                return {
                    "success": True,
                    "data": result,
                    "message": f"{stock_code} 종목 정보 조회 완료",
                }
            except KiwoomError as e:
                self.logger.error(f"주식 정보 조회 실패: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"{stock_code} 종목 정보 조회 실패",
                }
            except Exception as e:
                self.logger.error(f"예상치 못한 에러: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "시스템 오류가 발생했습니다",
                }

        @self.fastmcp.tool()
        async def get_market_status() -> Dict[str, Any]:
            """시장 상태 조회"""
            try:
                self.logger.info("시장 상태 조회 요청")
                result = await self.kiwoom_client.get_market_status()
                self.logger.info("시장 상태 조회 성공")
                return {
                    "success": True,
                    "data": result,
                    "message": "시장 상태 조회 완료",
                }
            except KiwoomError as e:
                self.logger.error(f"시장 상태 조회 실패: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "시장 상태 조회 실패",
                }
            except Exception as e:
                self.logger.error(f"예상치 못한 에러: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "시스템 오류가 발생했습니다",
                }

    def run(self):
        """서버 실행"""
        try:
            self.logger.info(f"키움 MCP 서버 시작 중... (포트: {self.port})")
            self.fastmcp.run(
                transport="streamable-http", host=self.host, port=self.port
            )
        except Exception as e:
            self.logger.error(f"서버 실행 실패: {e}")
            raise
        finally:
            self.logger.info("키움 MCP 서버 종료")


if __name__ == "__main__":
    try:
        # 서버 생성 및 실행
        server = KiwoomMCPServer(port=8030)
        server.run()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중단되었습니다")
    except Exception as e:
        logger.error(f"서버 오류: {e}")
        raise
    finally:
        logger.info("키움 MCP 서버 종료")
