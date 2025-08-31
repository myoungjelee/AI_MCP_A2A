"""
Deprecated LangGraph A2A Agent Executor.

This module provides a clean integration between LangGraph and A2A protocol,
removing unnecessary abstractions and over-engineering.
"""
import asyncio
import json
from typing import Any, Callable, cast

import structlog
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    TaskState,
    TextPart,
)
from a2a.utils import (
    get_data_parts,
    new_agent_parts_message,
    new_agent_text_message,
)
from langchain_core.messages import (
    message_to_dict,
    messages_to_dict,
)
from langgraph.graph.state import CompiledStateGraph

from src.a2a_integration.models import LangGraphExecutorConfig

logger = structlog.get_logger(__name__)


class LangGraphAgentExecutor(AgentExecutor):
    """
    A2A Agent Executor for LangGraph.

    This executor provides a clean bridge between LangGraph state machines
    and the A2A protocol, focusing on simplicity and SDK compliance.
    """

    def __init__(
        self,
        graph: CompiledStateGraph | None = None,
        result_extractor: Callable[[dict[str, Any]], str] | None = None,
        config: LangGraphExecutorConfig | None = None,
    ):
        """
        Initialize the LangGraph A2A Executor.

        Simplified to work directly with create_react_agent graphs.

        Args:
            graph: The compiled LangGraph from create_react_agent
            result_extractor: Optional function to extract and structure results for A2A
            config: Configuration for the executor
        """
        self.graph = graph
        self.config = config or LangGraphExecutorConfig()
        self.result_extractor = self._get_result_extractor(result_extractor)
        self._active_tasks: dict[str, asyncio.Task] = {}

        if graph:
            logger.info("✅ LangGraphAgentExecutor: Graph 기반 초기화")
        else:
            logger.warning("⚠️ LangGraphAgentExecutor: Graph가 제공되지 않음")

    def _get_result_extractor(self, custom_extractor: Callable[[dict[str, Any]], str] | None) -> Callable[[dict[str, Any]], str]:
        """Get the appropriate result extractor based on agent type."""
        if custom_extractor:
            return custom_extractor

        return self._default_extract_text

    async def _send_result(
        self,
        updater: TaskUpdater,
        result: Any,
        event_queue: EventQueue,
        complete_task: bool = True,
    ) -> None:
        """Send result as TextPart, DataPart, or both based on content type."""
        logger.info(f"🔧 _send_result called with result type: {type(result)}")
        logger.info(f"🔧 _send_result - result is dict: {isinstance(result, dict)}")
        logger.info(f"🔧 _send_result - result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

        if isinstance(result, dict) and result:
            # For structured data, send both text description and data
            parts = []

            # result가 이미 result_extractor에서 추출된 경우를 판단
            # extracted_result인 경우 'success', 'collected_data' 등의 키를 포함
            is_already_extracted = any(key in result for key in ['success', 'collected_data', 'analysis_result', 'trading_result'])

            if not is_already_extracted and self.result_extractor:
                try:
                    logger.info(f"🔧 Calling result_extractor with result: {type(result)}")
                    extracted = self.result_extractor(result)
                    logger.info(f"🔧 result_extractor returned: {type(extracted)}")

                    # result_extractor가 dict를 반환하면 DataPart용이고, str이면 TextPart용
                    if isinstance(extracted, str) and extracted:
                        logger.info(f"🔧 result_extractor returned text: {extracted[:100]}...")
                        parts.append(Part(root=TextPart(text=extracted)))
                        logger.info("✅ Added TextPart to response")
                    elif isinstance(extracted, dict):
                        logger.info(f"🔧 result_extractor returned dict: {list(extracted.keys())}")
                        # dict를 반환한 경우, 이것을 result로 사용
                        result = extracted
                        logger.info("🔧 Using extracted dict as result")
                    else:
                        logger.info(f"🔧 result_extractor returned unexpected type: {type(extracted)}")
                except Exception as e:
                    logger.error(f"❌ result_extractor failed: {e}")
                    pass
            else:
                logger.info("🔧 Result is already extracted or no result_extractor, using as-is")

            # Add structured data
            # Clean the result to ensure it's JSON serializable
            logger.info("🔧 Cleaning result for JSON serialization...")
            clean_result = self._clean_for_json(result)
            logger.info(f"🔧 clean_result: {clean_result}")
            if clean_result:
                parts.append(Part(root=DataPart(data=clean_result)))
                logger.info("✅ Added DataPart to response")
            else:
                logger.warning("⚠️ clean_result is empty, no DataPart added")

            # Create and enqueue message
            logger.info(f"🔧 Total parts created: {len(parts)}")
            if parts:
                message = new_agent_parts_message(parts)
                logger.info(f"🔧 Enqueuing message with {len(parts)} parts")
                await event_queue.enqueue_event(message)
                logger.info("✅ Message enqueued successfully")
            else:
                logger.warning("⚠️ No parts created, no message sent")
        elif result:
            # For simple text results
            text = (
                self.result_extractor(result)
                if callable(self.result_extractor)
                else str(result)
            )
            if text:
                message = new_agent_text_message(text)
                await event_queue.enqueue_event(message)
                logger.info("✅ Text message enqueued successfully")

        # Handle task completion based on complete_task parameter
        if complete_task:
            await updater.complete()
            logger.info("✅ Task completed via _send_result")

    def _clean_for_json(self, obj: Any) -> Any:
        """Clean object to be JSON serializable."""
        # LangChain 메시지 객체 처리
        if hasattr(obj, '__class__') and 'langchain_core.messages' in str(obj.__class__):
            try:
                return message_to_dict(obj)
            except Exception:
                return str(obj)
        elif isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # LangChain 메시지 리스트 처리
            if obj and hasattr(obj[0], '__class__') and 'langchain_core.messages' in str(obj[0].__class__):
                try:
                    return messages_to_dict(obj)
                except Exception:
                    return [self._clean_for_json(item) for item in obj]
            else:
                return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    def _default_extract_text(self, result: dict[str, Any]) -> str:
        """Default method to extract text from LangGraph output."""
        if isinstance(result, str):
            return result

        # Try common patterns
        for key in ["response", "output", "answer", "result", "messages", "message"]:
            if key in result:
                value = result[key]
                if isinstance(value, str):
                    return value
                elif isinstance(value, list) and value:
                    # Handle message list
                    last_msg = value[-1]
                    if isinstance(last_msg, dict):
                        return str(last_msg.get("content", last_msg))
                    return str(last_msg)
                elif isinstance(value, dict):
                    return str(value.get("content", value))

        # Fallback to JSON
        return json.dumps(result, ensure_ascii=False, indent=2)

    async def _extract_final_message(self, result: dict[str, Any], collected_messages: list[str] | None = None) -> str:
        """
        최종 메시지 추출을 result_extractor에게 위임합니다.

        Args:
            result: LangGraph 실행 결과
            collected_messages: 스트리밍 중 수집된 메시지 리스트 (옵션)

        Returns:
            추출된 최종 메시지 문자열
        """
        try:
            logger.debug("=== 최종 메시지 추출 시작 ===")

            # 1. result_extractor가 있으면 사용 (에이전트별 특화 로직)
            if self.result_extractor:
                extracted = self.result_extractor(result)
                if extracted and extracted.strip():
                    logger.info(f"✅ Result extractor 사용: {extracted[:100]}...")
                    return extracted

            # 2. 스트리밍 중 수집된 메시지 사용
            if collected_messages:
                collected_text = "".join(collected_messages)
                if collected_text.strip():
                    logger.info(f"✅ 스트리밍 메시지 사용: {collected_text[:100]}...")
                    return collected_text

            # 3. 기본 텍스트 추출 (폴백)
            text_result = self._default_extract_text(result)
            if text_result and text_result.strip():
                logger.info(f"✅ 기본 텍스트 추출: {text_result[:100]}...")
                return text_result

            # 4. 최종 폴백
            logger.warning("⚠️ 메시지 추출 실패, 폴백 메시지 사용")
            return "작업이 완료되었습니다."

        except Exception as e:
            logger.error(f"❌ 메시지 추출 중 오류: {e}")
            if collected_messages:
                return "".join(collected_messages)
            return "작업이 완료되었습니다."

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        A2A 요청을 처리하고 LangGraph 에이전트를 실행합니다.

        Args:
            context: A2A 요청 컨텍스트
            event_queue: 이벤트 큐
        """
        try:
            logger.info("Starting A2A agent execution")
            logger.info(f"High-level interface: {self.use_high_level_interface}")

            # EventQueue 상태 확인
            logger.info(f"EventQueue received: {event_queue}")
            logger.info(f"EventQueue type: {type(event_queue)}")
            if hasattr(event_queue, "_closed"):
                logger.info(f"EventQueue._closed: {event_queue._closed}")
            if hasattr(event_queue, "closed"):
                logger.info(f"EventQueue.closed: {event_queue.closed}")

            # 입력 처리
            processed_input = await self._process_input(context)
            logger.info(f"Processed input: {processed_input}")

            task_id = cast(str, context.task_id)
            context_id = getattr(context, "context_id", task_id)

            logger.info(f"Using context task_id: {task_id}")
            logger.info(f"Creating TaskUpdater for task_id: {task_id}")
            updater = TaskUpdater(
                event_queue=event_queue,
                task_id=task_id,
                context_id=str(context_id),
            )
            logger.info("TaskUpdater created successfully")

            # Graph 기반 실행 (create_react_agent에서 생성된 graph 사용)
            logger.info("🔄 Using graph-based execution")

            # RequestContext.configuration.blocking 확인
            is_blocking = False  # 기본적으로 스트리밍 모드 사용
            if hasattr(context, "request") and context.request:
                if (
                    hasattr(context.request, "configuration")
                    and context.request.configuration
                ):
                    is_blocking = getattr(
                        context.request.configuration, "blocking", False  # 기본값은 False (스트리밍)
                    )

            logger.info(
                f"Execution mode - blocking: {is_blocking}, config.enable_streaming: {self.config.enable_streaming}"
            )

            # 작업 시작 상태 업데이트 (상태만 변경, 메시지 없이)
            try:
                await updater.update_status(TaskState.working)
                logger.info("Initial working status update sent")
            except Exception as e:
                logger.warning(f"Failed to send initial status update: {e}")

            # EventQueue 상태 재확인
            if hasattr(event_queue, "_closed"):
                logger.info(
                    f"After TaskUpdater creation - EventQueue._closed: {event_queue._closed}"
                )

            # 완료 상태를 추적하는 플래그
            is_completed = False
            collected_messages = []

            # Blocking 모드이거나 스트리밍이 비활성화된 경우 동기 실행
            if is_blocking or not self.config.enable_streaming:
                logger.info("Using synchronous execution (ainvoke)")

                try:
                    logger.info(f"🚀 Starting ainvoke with processed_input: {type(processed_input)}")
                    logger.info(f"🚀 Graph type: {type(self.graph)}")
                    logger.info(f"🚀 Config: configurable thread_id: {context_id}")

                    # TODO: 이 부분을 각 호출 함수들로 바꿔야함
                    result = await self.graph.ainvoke(
                        processed_input,
                        config={"configurable": {"thread_id": context_id}},
                        stream_mode="messages",
                    )

                    logger.info(f"✅ ainvoke completed successfully, result type: {type(result)}")
                    logger.info(f"✅ Result is None: {result is None}")
                    if result:
                        logger.info(f"✅ Result keys: {list(result.keys()) if hasattr(result, 'keys') else 'Not a dict'}")

                    # ainvoke 결과가 None인 경우 최종 상태 가져오기
                    if result is None:
                        logger.info("ainvoke returned None, getting final state...")
                        state_snapshot = await self.graph.aget_state(
                            config={"configurable": {"thread_id": context_id}}
                        )
                        result = state_snapshot.values if state_snapshot else None
                        logger.info(f"Got final state: {type(result)}")

                    # result_extractor로 DataPart 추출 시도
                    try:
                        logger.info("Attempting to extract result using result_extractor...")
                        logger.info(f"result type before extractor: {type(result)}")
                        logger.info(f"result keys: {result.keys() if hasattr(result, 'keys') else 'Not a dict'}")
                        logger.info(f"result content (first 200 chars): {str(result)[:200] if result else 'None'}")
                        extracted_result = self.result_extractor(result)
                        logger.info(f"result_extractor returned type: {type(extracted_result)}")

                        if isinstance(extracted_result, dict) and extracted_result:
                            logger.info("result_extractor returned dict, sending DataPart")
                            await self._send_result(updater, extracted_result, event_queue)

                            # DataPart 전송 후 클라이언트가 수신할 시간을 확보
                            logger.info("⏳ DataPart 전송 후 클라이언트 수신 대기 중...")
                            await asyncio.sleep(0.5)  # 500ms 대기
                            logger.info("✅ 클라이언트 수신 대기 완료")

                            await updater.complete()
                            logger.info("✅ [Sync Mode] Task completed with DataPart response")
                            return
                        elif isinstance(extracted_result, str) and extracted_result:
                            logger.info("📝 [Sync Mode] result_extractor returned text")
                            # 텍스트가 반환된 경우 TextPart로 전송
                            await updater.update_status(
                                TaskState.completed,
                                new_agent_text_message(extracted_result, context_id, task_id),
                                final=True,
                            )
                            logger.info("✅ [Sync Mode] Task completed with text response")
                            return
                        else:
                            logger.info(f"ℹ️ [Sync Mode] result_extractor returned {type(extracted_result)}, falling back to text extraction")
                    except Exception as e:
                        logger.debug(f"[Sync Mode] result_extractor failed or not applicable: {e}")

                    # 폴백: 기존 텍스트 메시지 처리
                    final_message = await self._extract_final_message(result, collected_messages=None)

                    # 완료 상태로 업데이트
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(final_message, context_id, task_id),
                        final=True,
                    )

                    logger.debug("Task completed after synchronous execution (text fallback)")
                    return

                except Exception as e:
                    # 에러 발생 시 failed 상태로 업데이트
                    await updater.update_status(
                        TaskState.failed,
                        new_agent_text_message(
                            f"작업 중 오류가 발생했습니다: {str(e)}",
                            context_id,
                            task_id,
                        ),
                        final=True,
                    )
                    logger.error(f"Synchronous execution failed: {e}")
                    raise

            # 스트리밍 실행 (astream_events 사용)
            logger.info("🚀 Starting streaming execution with astream_events")
            logger.info(f"Thread ID: {context_id}, Task ID: {task_id}")

            # EventQueue 상태 확인
            if hasattr(event_queue, "_closed"):
                logger.debug(f"EventQueue._closed before streaming: {event_queue._closed}")

            # 스트리밍 상태 추적 변수
            event_count = 0
            node_count = 0

            # 메시지 버퍼링 관리
            message_buffer = []  # 실시간 스트리밍용 버퍼
            buffer_size = 0
            MAX_BUFFER_SIZE = 100  # 100자마다 전송하여 실시간성 향상

            # 스트리밍 진행 상태 추적
            streaming_start_time = asyncio.get_event_loop().time()
            last_heartbeat_time = streaming_start_time
            HEARTBEAT_INTERVAL = 10.0  # 10초마다 heartbeat 전송

            # 노드 결과 수집 (스트리밍 중에 직접 수집)
            process_collection_result = None  # DataCollector 결과 직접 저장

            try:
                async for event in self.graph.astream_events(
                    processed_input,
                    config={"configurable": {"thread_id": context_id}},
                ):
                    event_count += 1
                    # 이벤트 타입 확인
                    event_type = event.get("event", "")

                    # Heartbeat 메시지 전송 (연결 유지용)
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat_time > HEARTBEAT_INTERVAL:
                        try:
                            # 작업 진행 중임을 알리는 상태 업데이트
                            await updater.update_status(TaskState.working)
                            logger.debug(f"💓 Heartbeat sent after {HEARTBEAT_INTERVAL}s")
                            last_heartbeat_time = current_time
                        except Exception as e:
                            logger.warning(f"Failed to send heartbeat: {e}")

                    # 첫 몇 개의 이벤트에서만 EventQueue 상태 확인
                    if event_count <= 3 and hasattr(event_queue, "_closed"):
                        logger.debug(
                            f"Event {event_count} - EventQueue._closed: {event_queue._closed}"
                        )

                    # 노드 시작/종료 추적
                    if event_type == "on_chain_start":
                        node_name = event.get("name", "unknown")
                        node_count += 1
                        logger.debug(f"📍 [{node_count}] Starting node: {node_name}")

                    elif event_type == "on_chain_end":
                        node_name = event.get("name", "unknown")
                        logger.debug(f"✓ Node completed: {node_name}")

                        # DataCollector 노드 결과 직접 캐치
                        if node_name == "process_collection":
                            output = event.get("data", {}).get("output", {})
                            if output and isinstance(output, dict):
                                process_collection_result = output
                                logger.info(f"🎯 [Direct Capture] DataCollector result: {list(output.keys())}")
                                logger.info(f"🎯 [Direct Capture] DataCollector success: {output.get('success', False)}")

                        # 완료 노드 감지: __end__, process_collection
                        # process_collection: DataCollectorAgentA2A 메인 노드
                        completion_nodes = ["__end__", "process_collection"]
                        if node_name in completion_nodes and not is_completed:
                            is_completed = True
                            logger.info(f"🎯 Graph completion detected at node: {node_name}")

                            # 현재 상태에서 최종 메시지 추출 (수집된 메시지 포함)
                            try:
                                logger.info(f"🔍 Getting state for thread_id: {context_id}")
                                current_state = await self.graph.aget_state(
                                    config={"configurable": {"thread_id": context_id}}
                                )

                                logger.info(f"🔍 State retrieval result: {current_state is not None}")
                                if current_state:
                                    logger.info(f"🔍 State.values: {current_state.values is not None}")
                                    if current_state.values:
                                        logger.info(f"🔍 State.values keys: {list(current_state.values.keys()) if isinstance(current_state.values, dict) else type(current_state.values)}")
                                        logger.info(f"🔍 State.values content: {current_state.values}")

                                if current_state and current_state.values:
                                    # 수집된 메시지를 _extract_final_message에 전달
                                    final_text = await self._extract_final_message(
                                        current_state.values,
                                        collected_messages=collected_messages
                                    )
                                    logger.info(f"✅ Extracted final message from state: {final_text[:100]}...")
                                else:
                                    # 상태가 없는 경우 수집된 메시지만으로 처리
                                    logger.warning("No state values found, using collected messages")
                                    final_text = await self._extract_final_message(
                                        {},
                                        collected_messages=collected_messages
                                    )

                            except Exception as e:
                                logger.warning(f"⚠️ Failed to extract state result: {e}")
                                # 에러 시에도 수집된 메시지를 활용
                                final_text = await self._extract_final_message(
                                    {},
                                    collected_messages=collected_messages
                                )

                            # result_extractor를 사용해서 실제 결과 추출 및 A2A 메시지 전송
                            result_to_use = None

                            # 1순위: 직접 캐치한 DataCollector 결과 사용
                            if process_collection_result and isinstance(process_collection_result, dict):
                                logger.info("🎯 Using directly captured DataCollector result")
                                result_to_use = process_collection_result
                            # 2순위: LangGraph 상태 사용
                            elif current_state and current_state.values:
                                logger.info("🎯 Using LangGraph state result")
                                result_to_use = current_state.values

                            if result_to_use:
                                logger.info("🔧 Extracting result using result_extractor...")
                                try:
                                    # result_extractor가 Dict를 반환한다면 _send_result 사용
                                    extracted_result = self.result_extractor(result_to_use)
                                    if isinstance(extracted_result, dict):
                                        logger.info("✅ result_extractor returned dict, using _send_result")
                                        await self._send_result(updater, extracted_result, event_queue, complete_task=True)
                                        # 완료 플래그 설정 (스트리밍 루프 정상 종료)
                                        is_completed = True
                                        logger.info("✅ DataPart response sent, task completed")
                                        break  # 스트리밍 루프 정상 종료
                                    else:
                                        logger.info("ℹ️ result_extractor returned text, using text message")
                                        await updater.update_status(
                                            TaskState.completed,
                                            new_agent_text_message(final_text, context_id, task_id),
                                            final=True,
                                        )
                                        # 완료 플래그 설정
                                        is_completed = True
                                        logger.info("✅ Text response sent, task completed")
                                        break
                                except Exception as e:
                                    logger.error(f"❌ Failed to extract result: {e}")
                                    # 폴백으로 텍스트 메시지 사용
                                    await updater.update_status(
                                        TaskState.completed,
                                        new_agent_text_message(final_text, context_id, task_id),
                                        final=True,
                                    )
                                    is_completed = True
                                    logger.info("✅ Error handled with text fallback, task completed")
                                    break
                            else:
                                # 결과가 없는 경우 텍스트 메시지만 사용
                                await updater.update_status(
                                    TaskState.completed,
                                    new_agent_text_message(final_text, context_id, task_id),
                                    final=True,
                                )
                                is_completed = True
                                logger.info("✅ Fallback text response sent, task completed")
                                break

                            # 이미 return 했으므로 여기는 도달하지 않음
                            logger.info("✅ Task completed after streaming")
                            break

                    # 상태 업데이트 이벤트 처리
                    elif event_type == "on_chain_stream":
                        if "data" in event and event["data"]:
                            chunk = event["data"].get("chunk")
                            if chunk:
                                # 청크에서 내용 추출
                                if hasattr(chunk, "content"):
                                    content = chunk.content
                                else:
                                    content = (
                                        chunk.get("content", "")
                                        if isinstance(chunk, dict)
                                        else ""
                                    )

                                if content:
                                    collected_messages.append(content)

                    # LLM 스트리밍 이벤트 (토큰 단위) - LLM 응답만 스트리밍
                    elif event_type == "on_llm_stream":
                        if "data" in event and event["data"]:
                            chunk = event["data"].get("chunk")
                            if chunk:
                                # AIMessageChunk 처리
                                if hasattr(chunk, "content"):
                                    content = chunk.content
                                else:
                                    content = (
                                        chunk.get("content", "")
                                        if isinstance(chunk, dict)
                                        else ""
                                    )

                                if content:
                                    # 토큰을 버퍼에 추가
                                    message_buffer.append(content)
                                    buffer_size += len(content)
                                    collected_messages.append(content)

                                    # 버퍼가 가득 차면 LLM 응답 전송 (실시간 스트리밍)
                                    if buffer_size >= MAX_BUFFER_SIZE:
                                        buffer_content = "".join(message_buffer)
                                        try:
                                            await updater.update_status(
                                                TaskState.working,
                                                new_agent_text_message(
                                                    buffer_content,
                                                    context_id,
                                                    task_id,
                                                ),
                                            )
                                            logger.debug(f"📤 Sent buffered message ({buffer_size} chars)")
                                            message_buffer.clear()
                                            buffer_size = 0
                                        except Exception as e:
                                            logger.warning(f"⚠️ Failed to send buffered message: {e}")

                    # LLM 완료 이벤트
                    elif event_type == "on_llm_end":
                        logger.debug(
                            f"LLM response completed for node: {event.get('name', 'unknown')}"
                        )

                        # 남은 버퍼 내용이 있으면 전송 (LLM 응답 마지막 부분)
                        if message_buffer:
                            buffer_content = "".join(message_buffer)
                            try:
                                await updater.update_status(
                                    TaskState.working,
                                    new_agent_text_message(
                                        buffer_content, context_id, task_id
                                    ),
                                )
                                message_buffer.clear()
                                buffer_size = 0
                            except Exception as e:
                                logger.warning(f"Failed to send remaining buffer: {e}")

                # 스트리밍 완료 통계
                streaming_duration = asyncio.get_event_loop().time() - streaming_start_time
                logger.info("📊 Streaming Statistics:")
                logger.info(f"  - Total events: {event_count}")
                logger.info(f"  - Nodes executed: {node_count}")
                logger.info(f"  - Messages collected: {len(collected_messages)}")
                logger.info(f"  - Duration: {streaming_duration:.2f}s")
                logger.info(f"  - Completed: {is_completed}")

                # 스트리밍이 완료되었는데 __end__ 노드를 못 만난 경우
                if not is_completed:
                    logger.info("⚠️ Streaming ended without explicit completion node")

                    # LangGraph의 현재 상태를 가져와서 결과 추출
                    try:
                        logger.info(f"🔍 [Fallback] Getting state for thread_id: {context_id}")
                        current_state = await self.graph.aget_state(
                            config={"configurable": {"thread_id": context_id}}
                        )

                        logger.info(f"🔍 [Fallback] State retrieval result: {current_state is not None}")
                        if current_state:
                            logger.info(f"🔍 [Fallback] State.values: {current_state.values is not None}")
                            if current_state.values:
                                logger.info(f"🔍 [Fallback] State.values keys: {list(current_state.values.keys()) if isinstance(current_state.values, dict) else type(current_state.values)}")
                                logger.info(f"🔍 [Fallback] State.values content: {current_state.values}")

                        # 상태에서 최종 메시지 추출 (수집된 메시지 포함)
                        if current_state and current_state.values:
                            final_text = await self._extract_final_message(
                                current_state.values,
                                collected_messages=collected_messages
                            )
                            logger.info(f"✅ Extracted final message from graph state: {final_text[:100]}...")
                        else:
                            # 상태가 없어도 수집된 메시지로 시도
                            logger.warning("No state values found, using only collected messages")
                            final_text = await self._extract_final_message(
                                {},
                                collected_messages=collected_messages
                            )

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract state result: {e}")
                        # 에러 시에도 수집된 메시지를 활용
                        final_text = await self._extract_final_message(
                            {},
                            collected_messages=collected_messages
                        )

                    # 폴백 완료에서도 _send_result 사용 시도
                    current_state = None
                    try:
                        current_state = await self.graph.aget_state(
                            config={"configurable": {"thread_id": context_id}}
                        )
                    except Exception as e:
                        logger.debug(f"Failed to get fallback state: {e}")

                    if current_state and current_state.values:
                        logger.info("🔧 [Fallback] Extracting result using result_extractor...")
                        try:
                            extracted_result = self.result_extractor(current_state.values)
                            if isinstance(extracted_result, dict):
                                logger.info("✅ [Fallback] result_extractor returned dict, using _send_result")
                                await self._send_result(updater, extracted_result, event_queue, complete_task=True)
                                # 완료 플래그 설정
                                is_completed = True
                                logger.info("✅ [Fallback] DataPart response sent, task completed")
                            else:
                                logger.info("ℹ️ [Fallback] result_extractor returned text, using text message")
                                await updater.update_status(
                                    TaskState.completed,
                                    new_agent_text_message(final_text, context_id, task_id),
                                    final=True,
                                )
                                is_completed = True
                                logger.info("✅ [Fallback] Text response sent, task completed")
                        except Exception as e:
                            logger.error(f"❌ [Fallback] Failed to extract result: {e}")
                            await updater.update_status(
                                TaskState.completed,
                                new_agent_text_message(final_text, context_id, task_id),
                                final=True,
                            )
                            is_completed = True
                            logger.info("✅ [Fallback] Error handled with text response, task completed")
                    else:
                        # 폴백: 텍스트 메시지만 사용
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_text_message(final_text, context_id, task_id),
                            final=True,
                        )
                        is_completed = True
                        logger.info("✅ [Fallback] Text-only response sent, task completed")

                    logger.info("✅ Task completed after streaming (fallback completion)")

            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                # 에러 상태로 업데이트
                try:
                    await updater.update_status(
                        TaskState.failed,
                        new_agent_text_message(
                            f"작업 중 오류가 발생했습니다: {str(e)}",
                            context_id,
                            task_id,
                        ),
                        final=True,
                    )
                except Exception as update_error:
                    logger.error(f"Failed to update error status: {update_error}")
                raise

        except Exception as e:
            logger.error(f"Critical error in executor: {e}")
            raise

    async def _process_input(self, context: RequestContext) -> dict[str, Any]:
        """Extract and process input from request context."""
        query = context.get_user_input()

        # Try to get structured data from DataPart
        payload = {}
        if context.message and getattr(context.message, "parts", None):
            try:
                data_parts = get_data_parts(context.message.parts)
                if data_parts:
                    last_part = data_parts[-1]
                    if isinstance(last_part, dict):
                        payload = last_part
            except Exception as e:
                logger.debug(f"No DataPart found: {e}")

        # Build input for LangGraph
        if payload:
            # Always use payload directly for structured data - Dict 형태로 반환
            # A2A DataPart에서 온 구조화된 데이터는 항상 Dict로 처리
            logger.debug(f"Using structured payload: {payload}")
            return payload
        elif query:
            # 텍스트 쿼리만 있는 경우에만 messages로 래핑
            return {"messages": [{"role": "user", "content": query}]}
        else:
            return {"messages": []}

    async def _is_resume_operation(self, context: RequestContext) -> bool:
        """Check if this is a resume operation (Human-in-the-Loop)."""
        if not context.current_task:
            return False

        # Check if task is in input_required state
        if context.current_task.status == TaskState.input_required:
            return True

        # Check for explicit resume signal
        query = context.get_user_input().lower()
        return any(word in query for word in ["resume", "continue", "proceed"])

    def _extract_resume_value(self, context: RequestContext) -> Any:
        """Extract the value to resume with."""
        return context.get_user_input()

    async def _execute_with_streaming_events(
        self,
        invoke_input: Any,
        config: dict[str, Any],
        updater: TaskUpdater,
        task: Any,
        event_queue: EventQueue,
    ) -> dict[str, Any] | None:
        """
        Execute graph with streaming using astream_events for detailed event tracking.

        This method provides fine-grained event streaming, allowing us to track:
        - Chain starts and ends
        - Individual node executions
        - LLM token streaming
        - Tool calls and responses
        """
        accumulated_text = ""
        last_result = None
        current_node = None
        queue_closed = False

        try:
            # Use astream_events for detailed event streaming
            async for event in self.graph.astream_events(
                invoke_input, config, version="v2"
            ):
                # Skip if queue is already closed
                if queue_closed:
                    continue
                event_type = event.get("event", "")

                # Track which node is currently executing
                if event_type == "on_chain_start":
                    # Chain or node starting
                    metadata = event.get("metadata", {})
                    if "langgraph_node" in metadata:
                        current_node = metadata["langgraph_node"]
                        logger.debug(f"Starting node: {current_node}")

                        # Check if we reached the end node
                        if current_node == "__end__":
                            logger.debug("Reached __end__ node, completing task")
                            try:
                                await updater.complete()
                                queue_closed = True
                            except Exception as e:
                                logger.debug(f"Error completing task: {e}")
                            break

                elif event_type == "on_chain_stream":
                    # Streaming output from a chain/node
                    chunk = event.get("data", {}).get("chunk", {})

                    if isinstance(chunk, dict):
                        # Handle interrupt
                        if "__interrupt__" in chunk:
                            logger.info(
                                "Interrupt detected, switching to input_required"
                            )
                            interrupt_info = chunk["__interrupt__"]

                            # Create message requesting input
                            msg_text = (
                                "Human input required. Please provide your response."
                            )
                            if isinstance(interrupt_info, dict):
                                msg_text = interrupt_info.get("message", msg_text)

                            message = new_agent_text_message(msg_text)
                            try:
                                await event_queue.enqueue_event(message)
                                await updater.update_status(TaskState.input_required)
                            except Exception as e:
                                logger.debug(
                                    f"Could not send message (queue may be closed): {e}"
                                )
                                queue_closed = True
                            return last_result

                        # Store result
                        last_result = chunk

                        # Send structured data if present
                        if "data" in chunk:
                            try:
                                data_part = Part(
                                    root=DataPart(
                                        data=self._clean_for_json(chunk["data"])
                                    )
                                )
                                message = new_agent_parts_message([data_part])
                                try:
                                    await event_queue.enqueue_event(message)
                                except Exception as e:
                                    logger.debug(
                                        f"Could not send data part (queue may be closed): {e}"
                                    )
                                    queue_closed = True
                            except Exception as e:
                                logger.debug(f"Could not send DataPart: {e}")

                elif event_type == "on_chat_model_stream":
                    # Direct LLM token streaming
                    # event["data"]["chunk"] is an AIMessageChunk object, not a dict
                    try:
                        data = event.get("data", {})
                        chunk = data.get("chunk") if isinstance(data, dict) else None

                        # AIMessageChunk has a .content attribute
                        if chunk:
                            if hasattr(chunk, "content"):
                                content = chunk.content
                            else:
                                # Fallback for dict-like objects
                                content = (
                                    chunk.get("content", "")
                                    if isinstance(chunk, dict)
                                    else ""
                                )

                            if content:
                                # Stream text tokens as they arrive
                                message = new_agent_text_message(content)
                                try:
                                    await event_queue.enqueue_event(message)
                                except Exception as e:
                                    logger.debug(
                                        f"Could not stream text (queue may be closed): {e}"
                                    )
                                    queue_closed = True
                                accumulated_text += content
                    except Exception as e:
                        logger.debug(f"Error processing chat model stream: {e}")

                elif event_type == "on_tool_start":
                    # Tool execution starting
                    tool_name = event.get("name", "unknown")
                    logger.debug(f"Tool {tool_name} starting")

                    # Optionally notify about tool execution
                    if self.config.enable_interrupt_handling:
                        message = new_agent_text_message(
                            f"\n🔧 Executing tool: {tool_name}\n"
                        )
                        try:
                            await event_queue.enqueue_event(message)
                        except Exception as e:
                            logger.debug(
                                f"Could not send tool notification (queue may be closed): {e}"
                            )
                            queue_closed = True

                elif event_type == "on_tool_end":
                    # Tool execution completed
                    output = event.get("data", {}).get("output", {})
                    if output and isinstance(output, dict):
                        # Send tool output as DataPart
                        try:
                            data_part = Part(
                                root=DataPart(data=self._clean_for_json(output))
                            )
                            message = new_agent_parts_message([data_part])
                            try:
                                await event_queue.enqueue_event(message)
                            except Exception as e:
                                logger.debug(f"Could not send tool output: {e}")
                        except Exception as e:
                            logger.debug(f"Could not send tool output: {e}")

                elif event_type == "on_chain_end":
                    # Chain or node completed
                    output = event.get("data", {}).get("output", {})
                    if output and current_node:
                        logger.debug(f"Node {current_node} completed")
                        # Process final output from node
                        if isinstance(output, dict):
                            last_result = output

                            # Try to extract and send text
                            try:
                                text = self.result_extractor(output)
                                if text and text != accumulated_text:
                                    delta = text[len(accumulated_text) :]
                                    if delta:
                                        message = new_agent_text_message(delta)
                                        try:
                                            await event_queue.enqueue_event(message)
                                        except Exception as e:
                                            logger.debug(
                                                f"Could not send text delta (queue may be closed): {e}"
                                            )
                                            queue_closed = True
                                        accumulated_text = text
                            except Exception as e:
                                logger.debug(f"Could not extract text: {e}")

                elif event_type == "on_chat_model_end":
                    # LLM call completed
                    response = event.get("data", {}).get("output", {})
                    if response:
                        logger.debug(f"LLM response completed for node: {current_node}")

        except Exception as e:
            logger.error(f"Streaming events execution error: {e}")
            raise
        finally:
            # Complete the task if not already completed
            if not queue_closed:
                try:
                    await updater.complete()
                    logger.debug("Task completed after streaming")
                except Exception as e:
                    logger.debug(f"Error during completion: {e}")

        return last_result

    async def _execute_with_streaming(
        self,
        invoke_input: Any,
        config: dict[str, Any],
        updater: TaskUpdater,
        task: Any,
        event_queue: EventQueue,
    ) -> dict[str, Any] | None:
        """Execute graph with basic streaming using astream."""
        accumulated_text = ""
        last_result = None
        queue_closed = False

        try:
            async for chunk in self.graph.astream(invoke_input, config):
                if isinstance(chunk, dict):
                    # Handle interrupt
                    if "__interrupt__" in chunk:
                        logger.info("Interrupt detected, switching to input_required")
                        interrupt_info = chunk["__interrupt__"]

                        # Create message requesting input
                        msg_text = "Human input required. Please provide your response."
                        if isinstance(interrupt_info, dict):
                            msg_text = interrupt_info.get("message", msg_text)

                        message = new_agent_text_message(msg_text)
                        try:
                            await event_queue.enqueue_event(message)
                            await updater.update_status(TaskState.input_required)
                        except Exception as e:
                            logger.debug(
                                f"Could not send message (queue may be closed): {e}"
                            )
                        return last_result

                    # Process normal chunk
                    last_result = chunk

                    # Extract and stream text/data
                    try:
                        # For streaming, prefer text-only for incremental updates
                        text = self.result_extractor(chunk)
                        if text and text != accumulated_text:
                            # Send incremental text update
                            delta = text[len(accumulated_text) :]
                            if delta:
                                message = new_agent_text_message(delta)
                                await event_queue.enqueue_event(message)
                                accumulated_text = text
                    except Exception as e:
                        logger.debug(f"Could not extract text from chunk: {e}")

                    # If chunk contains structured data, also send as DataPart
                    if isinstance(chunk, dict) and "data" in chunk:
                        try:
                            data_part = Part(
                                root=DataPart(data=self._clean_for_json(chunk["data"]))
                            )
                            message = new_agent_parts_message([data_part])
                            try:
                                await event_queue.enqueue_event(message)
                            except Exception as e:
                                logger.debug(f"Could not send tool output: {e}")
                        except Exception as e:
                            logger.debug(f"Could not send DataPart: {e}")

        except Exception as e:
            logger.error(f"Streaming execution error: {e}")
            raise
        finally:
            # Complete the task if not already completed
            if not queue_closed:
                try:
                    await updater.complete()
                    logger.debug("Task completed after streaming")
                except Exception as e:
                    logger.debug(f"Error during completion: {e}")

        return last_result

    async def _execute_without_streaming(
        self,
        invoke_input: Any,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute graph without streaming using asyncio.to_thread()."""
        # asyncio.to_thread()를 사용하여 ainvoke를 스레드에서 실행
        # 스레드 내에서 새로운 이벤트 루프를 생성하여 MCP 도구 호환성 유지
        def run_ainvoke():
            return asyncio.run(self.graph.ainvoke(invoke_input, config))

        return await asyncio.to_thread(run_ainvoke)

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Cancel an ongoing task.

        This is called when the user requests to cancel a running task.
        """
        logger.info(f"Cancelling task: {context.task_id}")

        # Cancel any active asyncio tasks
        if context.task_id in self._active_tasks:
            task = self._active_tasks.pop(context.task_id)
            if not task.done():
                task.cancel()

        # Update task state
        if context.current_task:
            updater = TaskUpdater(
                event_queue=event_queue,
                task_id=context.current_task.id,
                context_id=str(context.context_id),
            )
            await updater.cancel()
            logger.info(f"Task {context.task_id} cancelled")
