"""
MCP 서버 통합 관리 스크립트
모든 MCP 서버의 생명주기를 관리하고 모니터링합니다.
"""

import asyncio
import json
import logging
import signal
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_servers import (
    FDRMCPServer,
    FinancialAnalysisMCPServer,
    MacroeconomicMCPServer,
    NaverNewsMCPServer,
    StockAnalysisMCPServer,
    TavilySearchMCPServer,
)

logger = logging.getLogger(__name__)


@dataclass
class ServerStatus:
    """서버 상태 정보"""

    name: str
    port: int
    status: str  # running, stopped, error
    uptime_seconds: Optional[float] = None
    request_count: int = 0
    error_count: int = 0
    error_rate: float = 0.0
    last_health_check: Optional[str] = None
    health_status: str = "unknown"
    error_message: Optional[str] = None


class MCPServerManager:
    """MCP 서버 통합 관리자"""

    def __init__(self, debug: bool = False):
        """초기화"""
        self.debug = debug
        self.servers: Dict[str, Any] = {}
        self.server_status: Dict[str, ServerStatus] = {}
        self.running = False

        # 로깅 설정
        self._setup_logging()

        # 시그널 핸들러 설정
        self._setup_signal_handlers()

        # 서버 인스턴스 초기화
        self._initialize_servers()

        logger.info("MCP Server Manager initialized")

    def _setup_logging(self):
        """로깅 설정"""
        log_level = logging.DEBUG if self.debug else logging.INFO
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("mcp_server_manager.log", encoding="utf-8"),
            ],
        )

    def _setup_signal_handlers(self):
        """시그널 핸들러 설정"""

        def signal_handler(signum, frame):
            logger.info(f"시그널 {signum} 수신, 서버들을 정리합니다...")
            self.running = False
            asyncio.create_task(self.stop_all_servers())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _initialize_servers(self):
        """서버 인스턴스들을 초기화합니다"""
        try:
            # 각 서버 인스턴스 생성
            self.servers = {
                "macroeconomic": MacroeconomicMCPServer(port=8041, debug=self.debug),
                "naver_news": NaverNewsMCPServer(port=8050, debug=self.debug),
                "stock_analysis": StockAnalysisMCPServer(port=8042, debug=self.debug),
                "tavily_search": TavilySearchMCPServer(port=8043, debug=self.debug),
                "financedatareader": FDRMCPServer(port=8044, debug=self.debug),
                "financial_analysis": FinancialAnalysisMCPServer(
                    port=8045, debug=self.debug
                ),
            }

            # 서버 상태 초기화
            for name, server in self.servers.items():
                self.server_status[name] = ServerStatus(
                    name=name, port=server.port, status="stopped"
                )

            logger.info(f"{len(self.servers)}개 서버 인스턴스 초기화 완료")

        except Exception as e:
            logger.error(f"서버 초기화 실패: {e}")
            raise

    async def start_all_servers(self):
        """모든 서버를 시작합니다"""
        logger.info("모든 MCP 서버 시작 중...")

        start_tasks = []
        for name, server in self.servers.items():
            task = asyncio.create_task(self._start_single_server(name, server))
            start_tasks.append(task)

        # 모든 서버 시작 대기
        results = await asyncio.gather(*start_tasks, return_exceptions=True)

        # 결과 확인
        success_count = 0
        for name, result in zip(self.servers.keys(), results, strict=False):
            if isinstance(result, Exception):
                logger.error(f"서버 {name} 시작 실패: {result}")
                self.server_status[name].status = "error"
                self.server_status[name].error_message = str(result)
            else:
                logger.info(f"서버 {name} 시작 성공")
                self.server_status[name].status = "running"
                success_count += 1

        logger.info(f"서버 시작 완료: {success_count}/{len(self.servers)} 성공")
        return success_count == len(self.servers)

    async def _start_single_server(self, name: str, server: Any):
        """단일 서버를 시작합니다"""
        try:
            await server.start_server()
            logger.info(f"서버 {name} 시작 완료")
            return True
        except Exception as e:
            logger.error(f"서버 {name} 시작 실패: {e}")
            raise

    async def stop_all_servers(self):
        """모든 서버를 중지합니다"""
        logger.info("모든 MCP 서버 중지 중...")

        stop_tasks = []
        for name, server in self.servers.items():
            if self.server_status[name].status == "running":
                task = asyncio.create_task(self._stop_single_server(name, server))
                stop_tasks.append(task)

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info("모든 서버 중지 완료")

    async def _stop_single_server(self, name: str, server: Any):
        """단일 서버를 중지합니다"""
        try:
            await server.stop_server()
            self.server_status[name].status = "stopped"
            logger.info(f"서버 {name} 중지 완료")
        except Exception as e:
            logger.error(f"서버 {name} 중지 실패: {e}")

    async def restart_server(self, server_name: str):
        """특정 서버를 재시작합니다"""
        if server_name not in self.servers:
            logger.error(f"알 수 없는 서버: {server_name}")
            return False

        try:
            server = self.servers[server_name]

            # 서버 중지
            if self.server_status[server_name].status == "running":
                await server.stop_server()
                self.server_status[server_name].status = "stopped"

            # 잠시 대기
            await asyncio.sleep(1)

            # 서버 시작
            await server.start_server()
            self.server_status[server_name].status = "running"
            self.server_status[server_name].error_message = None

            logger.info(f"서버 {server_name} 재시작 완료")
            return True

        except Exception as e:
            logger.error(f"서버 {server_name} 재시작 실패: {e}")
            self.server_status[server_name].status = "error"
            self.server_status[server_name].error_message = str(e)
            return False

    async def health_check_all_servers(self):
        """모든 서버의 헬스 상태를 확인합니다"""
        logger.debug("모든 서버 헬스 체크 중...")

        health_tasks = []
        for name, server in self.servers.items():
            if self.server_status[name].status == "running":
                task = asyncio.create_task(
                    self._health_check_single_server(name, server)
                )
                health_tasks.append(task)

        if health_tasks:
            await asyncio.gather(*health_tasks, return_exceptions=True)

    async def _health_check_single_server(self, name: str, server: Any):
        """단일 서버의 헬스 상태를 확인합니다"""
        try:
            # 헬스 상태 조회
            health_status = server.get_health_status()

            # 상태 업데이트
            status = self.server_status[name]
            status.health_status = health_status.get("status", "unknown")
            status.last_health_check = datetime.now().isoformat()

            # 메트릭 업데이트
            if hasattr(server, "get_metrics"):
                metrics = server.get_metrics()
                status.request_count = metrics.get("request_count", 0)
                status.error_count = metrics.get("error_count", 0)
                status.error_rate = metrics.get("error_rate", 0.0)

            # 업타임 업데이트
            if hasattr(server, "get_server_status"):
                server_status = server.get_server_status()
                status.uptime_seconds = server_status.get("uptime_seconds")

            logger.debug(f"서버 {name} 헬스 체크 완료: {status.health_status}")

        except Exception as e:
            logger.error(f"서버 {name} 헬스 체크 실패: {e}")
            self.server_status[name].health_status = "unhealthy"

    def get_overall_status(self) -> Dict[str, Any]:
        """전체 서버 상태를 반환합니다"""
        running_count = sum(
            1 for status in self.server_status.values() if status.status == "running"
        )
        error_count = sum(
            1 for status in self.server_status.values() if status.status == "error"
        )
        stopped_count = sum(
            1 for status in self.server_status.values() if status.status == "stopped"
        )

        total_requests = sum(
            status.request_count for status in self.server_status.values()
        )
        total_errors = sum(status.error_count for status in self.server_status.values())
        overall_error_rate = (total_errors / max(total_requests, 1)) * 100

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": (
                "healthy"
                if error_count == 0
                else "degraded" if running_count > 0 else "unhealthy"
            ),
            "server_count": {
                "total": len(self.server_status),
                "running": running_count,
                "stopped": stopped_count,
                "error": error_count,
            },
            "performance": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_error_rate": overall_error_rate,
            },
            "servers": {
                name: asdict(status) for name, status in self.server_status.items()
            },
        }

    async def run_monitoring_loop(self, interval: int = 30):
        """모니터링 루프를 실행합니다"""
        logger.info(f"모니터링 루프 시작 (간격: {interval}초)")

        while self.running:
            try:
                # 헬스 체크 실행
                await self.health_check_all_servers()

                # 상태 로깅
                overall_status = self.get_overall_status()
                logger.info(
                    f"전체 상태: {overall_status['overall_status']}, "
                    f"실행 중: {overall_status['server_count']['running']}/{overall_status['server_count']['total']}"
                )

                # 에러가 있는 서버 자동 재시작 (선택적)
                if self.debug:
                    for name, status in self.server_status.items():
                        if (
                            status.status == "error"
                            and status.health_status == "unhealthy"
                        ):
                            logger.warning(f"서버 {name} 자동 재시작 시도...")
                            await self.restart_server(name)

                # 대기
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                await asyncio.sleep(interval)

    async def run(self):
        """메인 실행 루프"""
        try:
            # 모든 서버 시작
            success = await self.start_all_servers()
            if not success:
                logger.warning("일부 서버 시작 실패, 계속 진행합니다...")

            self.running = True

            # 모니터링 루프 시작 (백그라운드에서 실행)
            asyncio.create_task(self.run_monitoring_loop())

            # 메인 루프
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단되었습니다.")
        except Exception as e:
            logger.error(f"실행 중 오류 발생: {e}")
        finally:
            self.running = False
            await self.stop_all_servers()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP 서버 통합 관리자")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    parser.add_argument("--health-check", action="store_true", help="헬스 체크만 실행")
    parser.add_argument("--status", action="store_true", help="상태 조회만 실행")

    args = parser.parse_args()

    # 관리자 인스턴스 생성
    manager = MCPServerManager(debug=args.debug)

    if args.health_check:
        # 헬스 체크만 실행
        asyncio.run(manager.health_check_all_servers())
        overall_status = manager.get_overall_status()
        print(json.dumps(overall_status, indent=2, ensure_ascii=False))
        return

    if args.status:
        # 상태 조회만 실행
        overall_status = manager.get_overall_status()
        print(json.dumps(overall_status, indent=2, ensure_ascii=False))
        return

    # 전체 관리자 실행
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"관리자 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
