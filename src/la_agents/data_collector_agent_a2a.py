"""
DataCollector Agent with A2A Integration.

This module provides a DataCollector agent that implements the standardized
A2A interface for seamless integration with the A2A protocol.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import pytz
import structlog
from base.a2a_interface import A2AOutput, A2AStreamBuffer, BaseA2AAgent
from base.base_graph_agent import BaseGraphAgent
from base.mcp_config import load_data_collector_tools
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from .prompts import get_prompt
from .util import load_env_file

logger = structlog.get_logger(__name__)

load_env_file()


class DataCollectorA2AAgent(BaseA2AAgent, BaseGraphAgent):
    """
    DataCollector Agent with A2A integration support.

    This agent handles data collection from various sources (market data, news, etc.)
    and provides standardized A2A output for streaming and polling operations.
    """

    def __init__(self, model=None, is_debug: bool = False, checkpointer=None):
        """
        Initialize DataCollector A2A Agent.

        Args:
            model: LLM model (default: gpt-5)
            is_debug: Debug mode flag
            checkpointer: Checkpoint manager (default: MemorySaver)
        """
        BaseA2AAgent.__init__(self)

        self.model = model or init_chat_model(
            model="gpt-5", temperature=0, model_provider="openai"
        )
        self.checkpointer = checkpointer or MemorySaver()

        # Initialize BaseGraphAgent with required parameters
        BaseGraphAgent.__init__(
            self,
            model=self.model,
            checkpointer=self.checkpointer,
            is_debug=is_debug,
            lazy_init=True,  # Use lazy initialization for A2A agents
            agent_name="DataCollectorA2AAgent",
        )

        self.tools = []

        # Stream buffer for managing LLM output
        self.stream_buffer = A2AStreamBuffer(max_size=200)

        # Track collected data during execution
        self.collected_symbols = set()
        self.tool_calls_count = 0

    async def initialize(self):
        """Initialize the agent with MCP tools and create the graph."""
        try:
            # Load MCP tools
            self.tools = await load_data_collector_tools()
            logger.info(f"✅ Loaded {len(self.tools)} MCP tools for DataCollector")

            # Get system prompt
            system_prompt = get_prompt(
                "data_collector", "system", tool_count=len(self.tools)
            )

            # Create the reactive agent graph
            config = RunnableConfig(recursion_limit=10)
            self.graph = create_react_agent(
                model=self.model,
                tools=self.tools,
                prompt=system_prompt,
                checkpointer=self.checkpointer,
                name="DataCollectorAgent",
                debug=self.is_debug,
                context_schema=config,
            )

            logger.info("✅ DataCollector A2A Agent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize DataCollector Agent: {e}")
            raise RuntimeError(f"DataCollector Agent initialization failed: {e}") from e

    async def execute_for_a2a(
        self, input_dict: Dict[str, Any], config: Optional[Dict[str, Any]] = None
    ) -> A2AOutput:
        """
        Execute the agent with A2A-compatible input and output.

        Args:
            input_dict: Input data containing messages or structured request
            config: Optional configuration (thread_id, etc.)

        Returns:
            A2AOutput: Standardized output for A2A processing
        """
        if not self.graph:
            await self.initialize()

        try:
            # Reset tracking variables
            self.collected_symbols.clear()
            self.tool_calls_count = 0

            # Execute the graph
            result = await self.graph.ainvoke(
                input_dict,
                config=config or {"configurable": {"thread_id": str(uuid4())}},
            )

            logger.info(f"[DataCollectorA2AAgent] Result: {result}")

            # Extract final output
            return self.extract_final_output(result)

        except Exception as e:
            return self.format_error(e, context="execute_for_a2a")

    def format_stream_event(self, event: Dict[str, Any]) -> Optional[A2AOutput]:
        """
        Convert a streaming event to standardized A2A output.

        Args:
            event: Raw streaming event from LangGraph

        Returns:
            A2AOutput if the event should be forwarded, None otherwise
        """
        event_type = event.get("event", "")

        # Handle LLM streaming
        if event_type == "on_llm_stream":
            content = self.extract_llm_content(event)
            if content and self.stream_buffer.add(content):
                # Buffer is full, flush it
                return self.create_a2a_output(
                    status="working",
                    text_content=self.stream_buffer.flush(),
                    stream_event=True,
                    metadata={"event_type": "llm_stream"},
                )

        # Handle tool execution events
        elif event_type == "on_tool_start":
            tool_name = event.get("name", "unknown")
            self.tool_calls_count += 1

            # Extract symbols from tool inputs if available
            if "data" in event and "input" in event["data"]:
                tool_input = event["data"]["input"]
                if isinstance(tool_input, dict) and "symbol" in tool_input:
                    self.collected_symbols.add(tool_input["symbol"])

            return self.create_a2a_output(
                status="working",
                text_content=f"📊 데이터 수집 중: {tool_name}",
                stream_event=True,
                metadata={
                    "event_type": "tool_start",
                    "tool_name": tool_name,
                    "tool_call_number": self.tool_calls_count,
                },
            )

        # Handle tool completion
        elif event_type == "on_tool_end":
            tool_output = event.get("data", {}).get("output", {})

            # Only send structured data for significant tool outputs
            if tool_output and isinstance(tool_output, dict):
                return self.create_a2a_output(
                    status="working",
                    data_content={
                        "tool_result": tool_output,
                        "symbols_collected": list(self.collected_symbols),
                        "tool_calls_made": self.tool_calls_count,
                    },
                    stream_event=True,
                    metadata={"event_type": "tool_end"},
                )

        # Handle completion events
        elif self.is_completion_event(event):
            # Flush any remaining buffer content
            if self.stream_buffer.has_content():
                return self.create_a2a_output(
                    status="working",
                    text_content=self.stream_buffer.flush(),
                    stream_event=True,
                    metadata={"event_type": "buffer_flush"},
                )

        return None

    def extract_final_output(self, state: Dict[str, Any]) -> A2AOutput:
        """
        Extract final output from the agent's state.

        Args:
            state: Final state from the LangGraph execution

        Returns:
            A2AOutput: Final standardized output
        """
        try:
            # Extract messages from state
            messages = state.get("messages", [])

            # Get the last AI message as summary
            summary = ""
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.__class__.__name__ == "AIMessage":
                    summary = msg.content
                    break

            # Count total messages
            total_messages = len(messages)

            # Prepare structured data
            data_content = {
                "success": True,
                "result": {
                    "raw_response": summary,
                    "symbols_collected": list(self.collected_symbols),
                    "tool_calls_made": self.tool_calls_count,
                    "total_messages_count": total_messages,
                    "timestamp": datetime.now(pytz.UTC).isoformat(),
                },
                "agent_type": "DataCollectorA2AAgent",
                "workflow_status": "completed",
            }

            # Create final output
            return self.create_a2a_output(
                status="completed",
                text_content=summary or "데이터 수집이 완료되었습니다.",
                data_content=data_content,
                final=True,
                metadata={
                    "execution_complete": True,
                    "symbols_count": len(self.collected_symbols),
                    "tool_calls_count": self.tool_calls_count,
                },
            )

        except Exception as e:
            logger.error(f"Error extracting final output: {e}")
            return self.format_error(e, context="extract_final_output")

    # Helper methods for data collection

    async def collect_data(
        self,
        symbols: list[str] = None,
        data_types: list[str] | None = None,
        user_question: str | None = None,
        context_id: str | None = None,
    ) -> A2AOutput:
        """
        Helper method for data collection with specific parameters.

        Args:
            symbols: Stock symbols to collect data for
            data_types: Types of data to collect
            user_question: Original user question
            context_id: Context ID for threading

        Returns:
            A2AOutput: Standardized collection result
        """
        # Build the collection request
        request = self._build_collection_request(symbols, data_types, user_question)

        # Create input for the agent
        input_dict = {"messages": [HumanMessage(content=request)]}

        # Execute with A2A interface
        config = {"configurable": {"thread_id": context_id or "default"}}

        return await self.execute_for_a2a(input_dict, config)

    def _build_collection_request(
        self,
        symbols: list[str] = None,
        data_types: list[str] = None,
        user_question: str = None,
    ) -> str:
        """Build a structured collection request."""
        if user_question:
            return user_question

        parts = []

        if symbols:
            parts.append(f"다음 종목들의 데이터를 수집해주세요: {', '.join(symbols)}")

        if data_types:
            type_str = ", ".join(data_types)
            parts.append(f"수집할 데이터 유형: {type_str}")
        else:
            parts.append("시세, 뉴스, 재무정보 등 관련된 모든 데이터를 수집해주세요")

        return " ".join(parts) if parts else "시장 데이터를 수집해주세요"


# Factory function for backward compatibility
async def create_data_collector_a2a_agent(
    model=None, is_debug: bool = False, checkpointer=None
) -> DataCollectorA2AAgent:
    """
    Create and initialize a DataCollector A2A Agent.

    Args:
        model: LLM model (default: gpt-4o-mini)
        is_debug: Debug mode flag
        checkpointer: Checkpoint manager

    Returns:
        DataCollectorA2AAgent: Initialized agent instance
    """
    agent = DataCollectorA2AAgent(model, is_debug, checkpointer)
    await agent.initialize()
    return agent
