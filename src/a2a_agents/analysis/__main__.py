"""
A2A Analysis Agent 실행 모듈
"""

import sys

import structlog

logger = structlog.get_logger("ReactAnalysisA2A")


if __name__ == "__main__":
    try:
        from src.a2a_agents.analysis.analysis_agent_a2a import main as analysis_main
        logger.info("A2A Analysis Agent를 시작합니다.")
        # uvicorn은 동기로 실행되어야 함
        analysis_main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"[Server] Error starting A2A Analysis Agent: {e}")
        sys.exit(1)
