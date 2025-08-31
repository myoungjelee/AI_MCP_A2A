"""
A2A (Agent-to-Agent) Integration Module

Simplified integration between LangGraph agents and A2A protocol.
"""

# Core executor
# Client utilities
from src.a2a_integration.a2a_lg_client_utils_v2 import (
    A2AClientManagerV2,
)

# Server utilities
from src.a2a_integration.a2a_lg_utils import (
    create_agent_card,
    to_a2a_run_uvicorn,
    to_a2a_starlette_server,
)
from src.a2a_integration.executor import LangGraphAgentExecutor

# Configuration
from src.a2a_integration.models import LangGraphExecutorConfig

__all__ = [
    # Core
    "LangGraphAgentExecutor",
    # Client utilities
    "A2AClientManagerV2",
    # Server utilities
    "create_agent_card",
    "to_a2a_run_uvicorn",
    "to_a2a_starlette_server",
    # Configuration
    "LangGraphExecutorConfig",
]
