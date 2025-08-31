"""
Simplified LangGraph A2A Agent Executor V2.

This module provides a clean integration between LangGraph agents with A2A interface
and the A2A protocol, leveraging standardized output formats for both streaming and polling.
"""

from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional, Type, cast
from uuid import uuid4

import pytz
import structlog
from a2a.client.helpers import create_text_message_object
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore, TaskManager, TaskUpdater
from a2a.types import (
    Artifact,
    DataPart,
    Message,
    Part,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
)

from src.a2a_integration.models import LangGraphExecutorConfig
from src.lg_agents.base.a2a_interface import A2AOutput, BaseA2AAgent

logger = structlog.get_logger(__name__)


class LangGraphAgentExecutorV2(AgentExecutor):
    """
    Simplified A2A Agent Executor for LangGraph agents with A2A interface.

    This executor leverages the standardized A2A interface implemented by each
    LangGraph agent, eliminating the need for custom result extractors and
    complex streaming logic.
    """

    def __init__(
        self,
        agent_class: Type[BaseA2AAgent],
        config: Optional[LangGraphExecutorConfig] = None,
        **agent_kwargs
    ):
        """
        Initialize the LangGraph A2A Executor V2.

        Args:
            agent_class: The A2A-enabled agent class to instantiate
            config: Configuration for the executor
            **agent_kwargs: Additional arguments to pass to the agent constructor
        """
        self.agent_class = agent_class
        self.agent_kwargs = agent_kwargs
        self.config = config or LangGraphExecutorConfig()
        self.agent: Optional[BaseA2AAgent] = None
        self.task_store = InMemoryTaskStore()
        self.task_manager: Optional[TaskManager] = None
        self.updater: Optional[TaskUpdater] = None
        self.event_queue: Optional[EventQueue] = None

        logger.info(f"✅ LangGraphAgentExecutorV2 initialized for {agent_class.__name__}")

    async def _ensure_agent_initialized(self):
        """Ensure the agent is initialized."""
        if not self.agent:
            try:
                # Create agent instance
                self.agent = self.agent_class(**self.agent_kwargs)

                # Initialize if it has an initialize method
                if hasattr(self.agent, 'initialize'):
                    await self.agent.initialize()
                    logger.info(f"✅ Agent {self.agent.agent_type} initialized")

            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                raise RuntimeError(f"Agent initialization failed: {e}") from e

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        Execute the A2A request using the standardized agent interface.

        Args:
            context: A2A request context
            event_queue: Event queue for sending messages
        """
        try:
            logger.info(f"Starting A2A agent execution for {self.agent_class.__name__}")

            # Ensure agent is initialized
            await self._ensure_agent_initialized()

            # Process input
            input_dict = await self._process_input(context)
            logger.info(f"Processed input: {type(input_dict)}")

            # Setup task updater
            task_id = cast(str, context.task_id)
            context_id = getattr(context, "context_id", task_id)
            user_message = create_text_message_object(content=input_dict.get("messages", [{}])[0].get("content", ""))

            task = context.current_task
            logger.info(f"[Execute] Task: {task}")
            if not task:
                task = Task(
                    id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        message=user_message,
                        state=TaskState.submitted,
                        timestamp=datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat()
                    ),
                )
                await event_queue.enqueue_event(task)
                logger.info(f"New task created and enqueued: {task_id}")
            else:
                logger.info(f"Using existing task from context: {task_id}")

            self.task_manager = TaskManager(
                task_id=task_id,
                context_id=context_id,
                task_store=self.task_store,
                initial_message=user_message,
            )
            self.updater = TaskUpdater(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id
            )
            self.event_queue = event_queue

            is_blocking = self._is_blocking_mode(context)
            logger.info(
                f"Execution mode - blocking: {is_blocking}, "
                f"streaming enabled: {self.config.enable_streaming}"
            )

            await self.updater.update_status(TaskState.working)
            if is_blocking or not self.config.enable_streaming:
                output = await self._execute_blocking(input_dict, context_id)
                logger.info(f"Blocking execution output: {output}")
            else:
                output = await self._execute_streaming(input_dict, context_id)
                logger.info(f"Streaming execution output: {output}")

            artifact = Artifact(
                artifact_id=str(uuid4()),
                parts=output.parts,
            )
            task = Task(
                id=task_id,
                context_id=context_id,
                artifacts=[artifact],
                status=TaskStatus(
                    state=TaskState.completed,
                    timestamp=datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat()
                )
            )
            await self.event_queue.enqueue_event(task)
            await self.updater.complete()

        except Exception as e:
            logger.error(f"Critical error in executor: {e}")
            try:
                updater = TaskUpdater(
                    event_queue=event_queue,
                    task_id=cast(str, context.task_id),
                    context_id=str(getattr(context, "context_id", context.task_id))
                )
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"작업 중 오류가 발생했습니다: {str(e)}"),
                    final=True
                )
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")
            raise

    async def _execute_blocking(
        self,
        input_dict: Dict[str, Any],
        context_id: str,
    ) -> Message:
        """Execute in blocking mode (no streaming)."""
        logger.info("Using blocking execution mode")

        try:
            # Execute the agent using standardized interface
            config = {"configurable": {"thread_id": context_id}}
            result = await self.agent.execute_for_a2a(input_dict, config)

            logger.info(f"Agent execution completed, result type: {type(result)}")
            logger.info(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            logger.info(f"Agent execution completed, status: {result.get('status')}")
            logger.info(f"Result final flag: {result.get('final', 'Not set')}")
            logger.info("===========" * 10)
            logger.info(f"Result: {result}")
            logger.info("===========" * 10)

            # Send the result based on A2AOutput format
            # NOTE: 이 안에서 상태 변경 금지.
            last_message = await self._send_a2a_output(result)
            logger.info(f"Last message: {last_message}")

            return last_message

        except Exception as e:
            logger.error(f"Blocking execution failed: {e}")
            raise

    async def _execute_streaming(
        self,
        input_dict: Dict[str, Any],
        context_id: str,
    ) -> AsyncGenerator[Message, None]:
        """Execute with streaming support."""
        logger.info("Using streaming execution mode")

        try:
            # For streaming, we need to hook into the agent's graph events
            # This requires the agent to have a graph attribute
            if not hasattr(self.agent, 'graph'):
                logger.warning("Agent doesn't support streaming, falling back to blocking")
                await self._execute_blocking(input_dict, context_id)
                return

            # Track completion
            is_completed = False
            event_count = 0

            # Stream events from the graph
            async for event in self.agent.graph.astream_events(
                input_dict,
                config={"configurable": {"thread_id": context_id}}
            ):
                event_count += 1

                # Let the agent format the streaming event
                formatted_output = self.agent.format_stream_event(event)

                if formatted_output:
                    _message = await self._send_a2a_output(formatted_output)
                    yield _message

                    # Check if this is a completion event
                    if formatted_output.get("final", False):
                        is_completed = True
                        logger.info("🎯 Completion detected from agent")
                        break

                # Check for completion patterns in raw event
                if not is_completed and self._is_completion_event(event):
                    is_completed = True
                    logger.info("🎯 Completion detected from event pattern")
                    break

            # If not completed yet, get final state
            if not is_completed:
                logger.info("Streaming ended, extracting final state")

                # Get the final state from the graph
                state_snapshot = await self.agent.graph.aget_state(
                    config={"configurable": {"thread_id": context_id}}
                )

                if state_snapshot and state_snapshot.values:
                    # Extract final output using agent's method
                    final_output = self.agent.extract_final_output(state_snapshot.values)

                    # Send final output
                    _message = await self._send_a2a_output(final_output)
                    yield _message

            logger.info(f"📊 Streaming complete - Events: {event_count}")

        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            raise

    async def _send_a2a_output(
        self,
        output: A2AOutput,
    ) -> Message:
        """
        Send A2AOutput as appropriate A2A message parts.

        Args:
            output: Standardized A2A output from agent
        """
        try:
            # A2AOutput 내용 전체 로깅
            logger.info(f"Full A2AOutput received: {output}")

            status = output.get("status", "working")
            text_content = output.get("text_content")
            data_content = output.get("data_content")
            agent_type = output.get("agent_type", "Unknown")

            parts = []

            if text_content:
                parts.append(Part(root=TextPart(text=text_content)))

            if data_content:
                parts.append(Part(root=DataPart(data=data_content)))

            # Ensure we always send something - create fallback content if parts is empty
            if not parts:
                # Create fallback text with agent and status information
                agent_type = output.get("agent_type", "Agent")
                fallback_text = f"{agent_type} - {status}"

                # Include error message if available
                error_msg = output.get("error_message")
                if error_msg:
                    fallback_text += f": {error_msg}"

                parts.append(Part(root=TextPart(text=fallback_text)))
                logger.warning(f"No content provided, sending fallback text: {fallback_text}")

            result = new_agent_parts_message(parts)
            return result

        except Exception as e:
            logger.error(f"Failed to send A2A output: {e}")

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue
    ) -> None:
        """
        Cancel an ongoing task.

        Args:
            context: Request context
            event_queue: Event queue
        """
        logger.info(f"Cancelling task: {context.task_id}")

        if context.current_task:
            updater = TaskUpdater(
                event_queue=event_queue,
                task_id=context.current_task.id,
                context_id=str(context.context_id)
            )
            await updater.cancel()
            logger.info(f"Task {context.task_id} cancelled")

    # Helper methods

    async def _process_input(self, context: RequestContext) -> Dict[str, Any]:
        """Process input from request context."""
        query = context.get_user_input()

        # Try to get structured data from DataPart
        payload = {}
        if context.message and getattr(context.message, "parts", None):
            try:
                from a2a.utils import get_data_parts
                data_parts = get_data_parts(context.message.parts)
                if data_parts:
                    last_part = data_parts[-1]
                    if isinstance(last_part, dict):
                        payload = last_part
            except Exception as e:
                logger.debug(f"No DataPart found: {e}")

        # Return appropriate format
        if payload:
            return payload
        elif query:
            return {"messages": [{"role": "user", "content": query}]}
        else:
            return {"messages": []}

    def _is_blocking_mode(self, context: RequestContext) -> bool:
        """Check if blocking mode is requested."""
        if hasattr(context, "request") and context.request:
            if hasattr(context.request, "configuration") and context.request.configuration:
                return getattr(context.request.configuration, "blocking", False)
        return False

    def _is_completion_event(self, event: Dict[str, Any]) -> bool:
        """Check if an event indicates completion."""
        event_type = event.get("event", "")

        if event_type == "on_chain_end":
            node_name = event.get("name", "")
            if node_name in ["__end__", "aggregate", "complete"]:
                return True

        return False

    def _map_status_to_task_state(self, status: str) -> TaskState:
        """Map A2AOutput status to TaskState."""
        mapping = {
            "working": TaskState.working,
            "completed": TaskState.completed,
            "failed": TaskState.failed,
            "input_required": TaskState.input_required
        }
        mapped_state = mapping.get(status, TaskState.working)
        logger.info(f"Status mapping - input: '{status}' -> output: {mapped_state}")
        return mapped_state


# Factory functions for creating executors for specific agents

def create_data_collector_executor(
    config: Optional[LangGraphExecutorConfig] = None,
    **agent_kwargs
) -> LangGraphAgentExecutorV2:
    """Create executor for DataCollector agent."""
    from src.lg_agents.data_collector_agent_a2a import DataCollectorA2AAgent
    return LangGraphAgentExecutorV2(DataCollectorA2AAgent, config, **agent_kwargs)


def create_analysis_executor(
    config: Optional[LangGraphExecutorConfig] = None,
    **agent_kwargs
) -> LangGraphAgentExecutorV2:
    """Create executor for Analysis agent."""
    from src.lg_agents.analysis_agent_a2a import AnalysisA2AAgent
    return LangGraphAgentExecutorV2(AnalysisA2AAgent, config, **agent_kwargs)


def create_trading_executor(
    config: Optional[LangGraphExecutorConfig] = None,
    **agent_kwargs
) -> LangGraphAgentExecutorV2:
    """Create executor for Trading agent."""
    from src.lg_agents.trading_agent_a2a import TradingA2AAgent
    return LangGraphAgentExecutorV2(TradingA2AAgent, config, **agent_kwargs)
