"""
A2A SupervisorAgent 실행 모듈 - React 기반 간소화 버전
"""

import sys

import structlog

logger = structlog.get_logger("ReactSupervisorA2A")


if __name__ == "__main__":
    try:
        from src.a2a_agents.supervisor.supervisor_agent_a2a import (
            main as supervisor_main,
        )
        logger.info("A2A Supervisor Agent를 시작합니다.")
        supervisor_main()

    except Exception as e:
        logger.error(f"[Server] Error starting A2A Supervisor Agent: {e}")
        sys.exit(1)
