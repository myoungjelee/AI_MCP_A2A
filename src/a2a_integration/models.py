"""
Simplified configuration and models for A2A integration.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LangGraphExecutorConfig(BaseModel):
    """
    Simplified configuration for LangGraph A2A Executor.

    Focuses only on essential settings without over-engineering.
    """

    # Core settings
    enable_streaming: bool = Field(
        default=False,  # 스트리밍 비활성화 - blocking 모드 문제 해결
        description="Enable streaming responses"
    )

    enable_interrupt_handling: bool = Field(
        default=True,
        description="Enable Human-in-the-Loop interrupt handling"
    )

    task_timeout_seconds: int = Field(
        default=300,
        description="Task timeout in seconds",
        gt=0
    )

    # Text extraction
    custom_text_keys: Optional[list[str]] = Field(
        default=None,
        description="Custom keys for text extraction from results"
    )

    # Strategy configuration for custom processors
    strategy_config: Optional[dict] = Field(
        default=None,
        description="Additional configuration for custom strategies and processors"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
