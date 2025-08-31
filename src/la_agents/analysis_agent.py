from uuid import uuid4

import pytz
import structlog
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    filter_messages,
)
from langchain_core.messages.utils import convert_to_openai_messages
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from .util import load_env_file

load_env_file()

logger = structlog.get_logger(__name__)


async def create_analysis_agent(model=None, is_debug=False):
    """
    create_react_agent를 직접 반환하는 팩토리 함수

    LangGraph의 create_react_agent를 사용하여 데이터 통합 분석을 수행하는 agent를 생성합니다:
    1. 기술적 분석 (Technical Analysis)
    2. 기본적 분석 (Fundamental Analysis)
    3. 거시경제 분석 (Macroeconomic Analysis)
    4. 감성 분석 (Sentiment Analysis)

    create_react_agent의 강력한 도구 호출 능력을 활용하여
    각 차원별 MCP 도구들을 체계적으로 실행하고 통합 분석 결과를 제공합니다.

    Args:
        model: LLM 모델 (기본값: gpt-5-mini)
        is_debug: 디버그 모드 여부 - create_react_agent의 debug 파라미터로 전달

    Returns:
        create_react_agent 인스턴스 (LangGraph ReAct Agent)

    Raises:
        RuntimeError: MCP 도구 로딩 또는 create_react_agent 생성 실패

    사용 예:
        agent = await create_analysis_agent(is_debug=True)
        result = await analyze(agent, symbols=["005930"], user_question="투자 분석")
    """
    try:
        # LLM 모델 초기화
        llm_model = model or init_chat_model(
            model="gpt-5",
            temperature=0.1,
            model_provider="openai",
        )

        # MCP 도구 로딩
        from base.mcp_config import load_analysis_tools

        from .prompts import get_prompt

        # 분석용 MCP 도구 로딩 (기술적/기본적/거시경제/감성 분석)
        tools = await load_analysis_tools()
        logger.info(f"✅ create_react_agent용 MCP 도구 로딩 완료: {len(tools)}개")

        tool_names = [tool.name for tool in tools] if tools else []
        logger.info(f"📋 로딩된 도구 목록: {tool_names}")

        system_prompt = get_prompt("analysis", "system", tool_count=len(tools))

        check_pointer = MemorySaver()
        config = RunnableConfig(recursion_limit=10)

        agent = create_react_agent(
            model=llm_model,
            tools=tools,
            prompt=system_prompt,
            checkpointer=check_pointer,
            name="LangGraphAnalysisAgent",
            debug=is_debug,
            context_schema=config,
        )
        return agent

    except Exception as e:
        logger.error(f"❌ create_react_agent 초기화 실패: {e}")
        raise RuntimeError(f"Failed to initialize create_react_agent: {e}") from e


async def analyze(
    agent: CompiledStateGraph,
    symbols: list[str],
    collected_data: dict | None = None,
    user_question: str | None = None,
    context_id: str | None = None,
):
    """
    통합 주식 분석 Agent 를 통한 분석 실행

    이 함수는 create_react_agent의 핵심 기능을 활용하여 체계적인 분석을 수행합니다:

    1. 자동 도구 선택: create_react_agent가 분석에 필요한 MCP 도구를 자동 선택
    2. ReAct 패턴 실행: Think(사고) → Act(도구호출) → Observe(결과분석) 반복
    3. 4차원 통합: 기술적/기본적/거시경제/감성 분석을 순차적으로 수행
    4. 컨텍스트 유지: MemorySaver를 통해 이전 분석 결과를 기억하며 진행

    Args:
        agent: create_analysis_agent()로 생성된 create_react_agent 인스턴스
        symbols: list[str] - 분석할 종목 코드
        collected_data: dict - DataCollector에서 수집된 데이터
        user_question: str - 사용자 원본 질문

    Returns:
        dict: create_react_agent가 수행한 통합 분석 결과
    """
    try:
        user_prompt = f"""종목 코드: {symbols}
사용자 질문: {user_question or "종합적인 투자 분석"}

위 종목에 대해 가지고 있는 도구의 다양한 차원 통합 분석을 수행해주세요.
반드시 모든 차원의 도구를 사용하여 실제 데이터를 수집하고 분석한 후 최종 투자 신호를 도출해주세요."""

        messages = [HumanMessage(content=user_prompt)]

        result = await agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": context_id or str(uuid4())}},
        )

        # create_react_agent 실행 결과에서 최종 AI 메시지 추출
        ai_messages = filter_messages(
            result["messages"],
            include_types=[AIMessage],
        )

        if not ai_messages:
            logger.error("No AI messages found in the result")
            raise ValueError("No AI response generated")

        final_message: AIMessage = ai_messages[-1]

        try:
            from datetime import datetime

            # create_react_agent가 생성한 전체 메시지 히스토리 변환
            full_message_history = []
            msg_list: list[dict] = convert_to_openai_messages(result["messages"])
            full_message_history.extend(msg_list)

            logger.info(
                f"📝 create_react_agent 메시지 히스토리 구성 완료: {len(full_message_history)}개 메시지"
            )
        except Exception as e:
            logger.error(f"❌ create_react_agent 메시지 히스토리 구성 중 오류: {e}")
            full_message_history = []

        tool_calls_made = sum(
            len(msg.tool_calls)
            for msg in filter_messages(result["messages"], include_types=[AIMessage])
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )

        # 실행 결과 Dictionary 반환
        return {
            "success": True,
            "result": {
                "raw_analysis": final_message.content,
                "symbols_analyzed": symbols,
                "tool_calls_made": tool_calls_made,
                "total_messages_count": len(result["messages"]),
                "timestamp": datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat(),
            },
            "full_messages": full_message_history,
            "agent_type": "AnalysisLangGraphAgent",
            "workflow_status": "completed",
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ create_react_agent 기반 분석 실패: {e}")
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "agent_type": "AnalysisLangGraphAgent",
            "workflow_status": "failed",
        }
