"""
A2A Integration Interface for LangGraph Agents.

This module provides standardized interfaces and utilities for integrating
LangGraph agents with the A2A (Agent-to-Agent) protocol, ensuring consistent
data formats for both streaming and polling operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Literal, Optional, TypedDict

import structlog

logger = structlog.get_logger(__name__)


class A2AOutput(TypedDict):
    """
    Standardized output format for A2A integration.

    This format unifies streaming events and final results,
    enabling consistent handling in the A2A executor.
    """

    # Agent identification
    agent_type: str  # e.g., "DataCollector", "Analysis", "Trading", "Supervisor"

    # Status indication
    status: Literal["working", "completed", "failed", "input_required"]

    # Content for A2A message parts
    text_content: Optional[str]  # For TextPart
    data_content: Optional[Dict[str, Any]]  # For DataPart (structured data)

    # Metadata for processing
    metadata: Dict[str, Any]  # Additional context (timestamp, node_name, etc.)

    # Event type flags
    stream_event: bool  # True for streaming events, False for final results
    final: bool  # True when this is the last output

    # Optional fields for specific use cases
    error_message: Optional[str]  # Error details if status is "failed"
    requires_approval: Optional[bool]  # For Human-in-the-Loop scenarios


class BaseA2AAgent(ABC):
    """
    Abstract base class for LangGraph agents with A2A integration.

    This class defines the standard interface that all LangGraph agents
    must implement to support A2A protocol integration.
    """

    def __init__(self):
        """Initialize the base A2A agent."""
        self.agent_type = self.__class__.__name__.replace("Agent", "")
        logger.info(f"Initializing A2A agent: {self.agent_type}")

    @abstractmethod
    async def execute_for_a2a(
        self,
        input_dict: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> A2AOutput:
        """
        Execute the agent with A2A-compatible input and output.

        This method replaces direct graph.ainvoke() calls, providing
        a standardized interface for the A2A executor.

        Args:
            input_dict: Input data in standard format
            config: Optional configuration (thread_id, etc.)

        Returns:
            A2AOutput: Standardized output for A2A processing
        """
        pass

    @abstractmethod
    def format_stream_event(
        self,
        event: Dict[str, Any]
    ) -> Optional[A2AOutput]:
        """
        Convert a streaming event to standardized A2A output.

        This method handles various streaming event types:
        - on_llm_stream: LLM token streaming
        - on_chain_start/end: Node execution events
        - on_tool_start/end: Tool execution events

        Args:
            event: Raw streaming event from LangGraph

        Returns:
            A2AOutput if the event should be forwarded, None otherwise
        """
        pass

    @abstractmethod
    def extract_final_output(
        self,
        state: Dict[str, Any]
    ) -> A2AOutput:
        """
        Extract final output from the agent's state.

        This method is called when the agent execution completes,
        converting the final state to standardized A2A output.

        Args:
            state: Final state from the LangGraph execution

        Returns:
            A2AOutput: Final standardized output
        """
        pass

    # Common utility methods

    def create_a2a_output(
        self,
        status: Literal["working", "completed", "failed", "input_required"],
        text_content: Optional[str] = None,
        data_content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        stream_event: bool = False,
        final: bool = False,
        **kwargs
    ) -> A2AOutput:
        """
        Helper method to create standardized A2A output.

        Args:
            status: Current status of the agent
            text_content: Text content for TextPart
            data_content: Structured data for DataPart
            metadata: Additional metadata
            stream_event: Whether this is a streaming event
            final: Whether this is the final output
            **kwargs: Additional optional fields

        Returns:
            A2AOutput: Standardized output dictionary
        """
        output: A2AOutput = {
            "agent_type": self.agent_type,
            "status": status,
            "text_content": text_content,
            "data_content": data_content,
            "metadata": metadata or {},
            "stream_event": stream_event,
            "final": final,
            "error_message": kwargs.get("error_message"),
            "requires_approval": kwargs.get("requires_approval")
        }

        return output

    def format_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> A2AOutput:
        """
        Format an error as standardized A2A output.

        Args:
            error: The exception that occurred
            context: Optional context about where the error occurred

        Returns:
            A2AOutput: Error formatted as A2A output
        """
        error_message = f"{type(error).__name__}: {str(error)}"
        if context:
            error_message = f"{context}: {error_message}"

        logger.error(f"A2A Agent Error: {error_message}")

        return self.create_a2a_output(
            status="failed",
            text_content=f"에러가 발생했습니다: {str(error)}",
            metadata={"error_type": type(error).__name__, "context": context},
            final=True,
            error_message=error_message
        )

    def is_completion_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if a streaming event indicates completion.

        Args:
            event: Streaming event to check

        Returns:
            bool: True if this is a completion event
        """
        event_type = event.get("event", "")

        # Check for explicit end events
        if event_type == "on_chain_end":
            node_name = event.get("name", "")
            # Common completion node names
            if node_name in ["__end__", "final", "complete"]:
                return True

        # Check for completion in metadata
        metadata = event.get("metadata", {})
        if metadata.get("is_final", False):
            return True

        return False

    def extract_llm_content(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Extract LLM content from a streaming event.

        Args:
            event: Streaming event containing LLM output

        Returns:
            str: Extracted content, or None if not an LLM event
        """
        if event.get("event") != "on_llm_stream":
            return None

        data = event.get("data", {})
        chunk = data.get("chunk", {})

        # Handle AIMessageChunk
        if hasattr(chunk, "content"):
            return chunk.content
        # Handle dict-like chunk
        elif isinstance(chunk, dict):
            return chunk.get("content", "")

        return None


class A2AStreamBuffer:
    """
    Buffer for managing streaming content.

    This class helps accumulate streaming tokens and flush them
    at appropriate intervals for better user experience.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize the stream buffer.

        Args:
            max_size: Maximum buffer size before auto-flush
        """
        self.buffer: list[str] = []
        self.size: int = 0
        self.max_size = max_size

    def add(self, content: str) -> bool:
        """
        Add content to the buffer.

        Args:
            content: Content to add

        Returns:
            bool: True if buffer should be flushed
        """
        if not content:
            return False

        self.buffer.append(content)
        self.size += len(content)

        return self.size >= self.max_size

    def flush(self) -> str:
        """
        Flush the buffer and return accumulated content.

        Returns:
            str: Accumulated content
        """
        if not self.buffer:
            return ""

        content = "".join(self.buffer)
        self.buffer.clear()
        self.size = 0

        return content

    def has_content(self) -> bool:
        """Check if buffer has content."""
        return len(self.buffer) > 0
