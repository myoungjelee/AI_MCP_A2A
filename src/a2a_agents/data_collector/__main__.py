"""
A2A Data Collector Agent 실행 모듈
"""

import sys

import structlog

logger = structlog.get_logger("ReactDataCollectorA2A")


if __name__ == "__main__":
    try:
        from src.a2a_agents.data_collector.data_collector_agent_a2a import (
            main as data_collector_main,
        )
        logger.info("A2A Data Collector Agent를 시작합니다.")
        # uvicorn은 동기로 실행되어야 함
        data_collector_main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"[Main] Error starting A2A Data Collector Agent: {e}")
        sys.exit(1)
