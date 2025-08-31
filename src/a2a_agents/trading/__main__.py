"""
A2A Trading Agent 실행 모듈
"""

import sys

import structlog

logger = structlog.get_logger("ReactTradingA2A")


if __name__ == "__main__":
    try:
        from src.a2a_agents.trading.trading_agent_a2a import main as trading_main
        logger.info("A2A Trading Agent를 시작합니다.")
        # uvicorn은 동기로 실행되어야 함
        trading_main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"[Main] Error starting A2A Trading Agent: {e}")
        sys.exit(1)
