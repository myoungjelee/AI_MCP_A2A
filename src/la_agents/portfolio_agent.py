"""
포트폴리오 구성 에이전트 - create_react_agent 기반

분석된 데이터를 바탕으로 최적의 포트폴리오를 구성합니다.
리스크-수익률 최적화, 섹터별 분산, 투자 스타일 균형을 고려합니다.
"""

from typing import Any
from uuid import uuid4

import pytz
import structlog
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    convert_to_openai_messages,
    filter_messages,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from .util import load_env_file

logger = structlog.get_logger(__name__)

load_env_file()


async def create_portfolio_agent(model=None, is_debug: bool = False, checkpointer=None):
    """
    create_react_agent를 통한 포트폴리오 관리 에이전트

    MCP 도구들을 로딩하고 프롬프트를 설정한 후 create_react_agent를 생성합니다.

    Args:
        model: LLM 모델 (기본값: gpt-5)
        is_debug: 디버그 모드 여부
        checkpointer: 체크포인터 (기본값: MemorySaver)

    Returns:
        create_react_agent로 생성된 LangGraph Agent

    Usage:
        agent = await create_portfolio_agent()
        result = await agent.ainvoke({"messages": [...]})
    """
    try:
        # 1. MCP 도구 로딩
        from .base.mcp_config import load_portfolio_tools
        from .prompts import get_prompt

        tools = await load_portfolio_tools()
        logger.info(f"✅ Loaded {len(tools)} MCP tools for Portfolio")

        system_prompt = get_prompt("portfolio", "system", tool_count=len(tools))

        model = model or init_chat_model(
            model="gpt-5",
            temperature=0,
            model_provider="openai",
        )

        checkpointer = MemorySaver()
        config = RunnableConfig(recursion_limit=10)

        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=system_prompt,
            checkpointer=checkpointer,
            name="PortfolioAgent",
            debug=is_debug,
            context_schema=config,
        )

        logger.info("✅ Portfolio Agent created successfully with create_react_agent")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Portfolio Agent: {e}")
        raise RuntimeError(f"Portfolio Agent creation failed: {e}") from e


async def manage_portfolio(
    agent: CompiledStateGraph,
    analysis_results: dict | None = None,
    risk_tolerance: str = "moderate",
    target_return: float = 0.10,
    max_risk: float = 0.15,
    portfolio_size: int = 15,
    user_question: str | None = None,
    context_id: str | None = None,
) -> dict[str, Any]:
    """
    포트폴리오 관리 실행 헬퍼 함수

    create_react_agent로 생성된 agent를 사용하여 포트폴리오를 관리합니다.

    Args:
        agent: create_portfolio_agent()로 생성된 에이전트
        analysis_results: 분석 에이전트의 결과 (선택적)
        risk_tolerance: 리스크 허용도 (conservative, moderate, aggressive)
        target_return: 목표 수익률 (예: 0.10 = 10%)
        max_risk: 최대 허용 리스크 (예: 0.15 = 15%)
        portfolio_size: 포트폴리오 종목 수
        user_question: 사용자 원본 질문 (선택적)
        context_id: 컨텍스트 ID (선택적)

    Returns:
        포트폴리오 관리 결과 딕셔너리
    """
    try:
        # 분석 결과 요약 (긴 내용은 잘라서 전달)
        analysis_summary = ""
        if analysis_results:
            analysis_str = str(analysis_results)
            analysis_summary = (
                f"분석 결과: {analysis_str[:300]}..."
                if len(analysis_str) > 300
                else f"분석 결과: {analysis_str}"
            )

        user_prompt = f"""포트폴리오 관리 요청:
        리스크 허용도: {risk_tolerance}
        목표 수익률: {target_return:.1%}
        최대 리스크: {max_risk:.1%}
        종목 수: {portfolio_size}개
        {analysis_summary}
        사용자 질문: {user_question or '포트폴리오 최적화 및 관리'}

        위 조건에 맞는 포트폴리오를 구성하고 관리해주세요."""

        messages = [HumanMessage(content=user_prompt)]

        result = await agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": context_id or str(uuid4())}},
        )

        # Debug: print result structure
        logger.info(f"Debug - result type: {type(result)}")
        logger.info(
            f"Debug - result keys: {list(result.keys()) if hasattr(result, 'keys') else 'No keys'}"
        )

        # create_react_agent 실행 결과에서 최종 AI 메시지 추출
        if "messages" not in result:
            logger.error(f"❌ result에 'messages' 키가 없습니다. result: {result}")
            # Try to extract messages differently
            if hasattr(result, "messages"):
                messages_list = result.messages
            else:
                messages_list = [result] if hasattr(result, "content") else []
        else:
            messages_list = result["messages"]

        ai_messages = filter_messages(
            messages_list,
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
            msg_list: list[dict] = convert_to_openai_messages(messages_list)
            full_message_history.extend(msg_list)

            logger.info(
                f"�� create_react_agent 메시지 히스토리 구성 완료: {len(full_message_history)}개 메시지"
            )
        except Exception as e:
            logger.error(f"❌ create_react_agent 메시지 히스토리 구성 중 오류: {e}")
            full_message_history = []

        # create_react_agent가 수행한 도구 호출 횟수 계산
        tool_calls_made = sum(
            len(msg.tool_calls)
            for msg in filter_messages(messages_list, include_types=[AIMessage])
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )

        logger.info("�� create_react_agent 실행 완료 - 포트폴리오 관리 요약:")
        logger.info(f"   → 총 도구 호출 횟수: {tool_calls_made}")
        logger.info(f"   → 총 메시지 수: {len(messages_list)}")
        logger.info(f"   → 리스크 허용도: {risk_tolerance}")
        logger.info(f"   → 목표 수익률: {target_return:.1%}")

        # 실행 결과 Dictionary 반환
        return {
            "success": True,
            "result": {
                "raw_response": final_message.content,
                "portfolio_config": {
                    "risk_tolerance": risk_tolerance,
                    "target_return": target_return,
                    "max_risk": max_risk,
                    "portfolio_size": portfolio_size,
                },
                "tool_calls_made": tool_calls_made,
                "total_messages_count": len(result["messages"]),
                "timestamp": datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat(),
            },
            "full_messages": full_message_history,
            "agent_type": "PortfolioLangGraphAgent",
            "workflow_status": "completed",
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ create_react_agent 기반 포트폴리오 관리 실패: {e}")
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "agent_type": "PortfolioLangGraphAgent",
            "agent_implementation": "create_react_agent",
            "workflow_status": "failed",
        }


async def optimize_portfolio(
    agent: CompiledStateGraph,
    stock_scores: dict[str, float] | None = None,
    current_weights: dict[str, float] | None = None,
    risk_constraints: dict[str, Any] | None = None,
    user_question: str | None = None,
    context_id: str | None = None,
) -> dict[str, Any]:
    """
    포트폴리오 최적화 실행 헬퍼 함수

    Args:
        agent: create_portfolio_agent()로 생성된 에이전트
        stock_scores: 종목별 점수 (선택적)
        current_weights: 현재 포트폴리오 가중치 (선택적)
        risk_constraints: 리스크 제약 조건 (선택적)
        user_question: 사용자 질문 (선택적)
        context_id: 컨텍스트 ID (선택적)

    Returns:
        포트폴리오 최적화 결과 딕셔너리
    """
    try:
        # 제약 조건 요약
        constraints_summary = ""
        if risk_constraints:
            constraints_str = str(risk_constraints)
            constraints_summary = (
                f"리스크 제약: {constraints_str[:200]}..."
                if len(constraints_str) > 200
                else f"리스크 제약: {constraints_str}"
            )

        user_prompt = f"""포트폴리오 최적화 요청:
        {f'종목별 점수: {stock_scores}' if stock_scores else ''}
        {f'현재 가중치: {current_weights}' if current_weights else ''}
        {constraints_summary}
        사용자 질문: {user_question or '포트폴리오 최적화'}

        위 조건에 맞게 포트폴리오를 최적화해주세요."""

        messages = [HumanMessage(content=user_prompt)]

        result = await agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": context_id or str(uuid4())}},
        )

        # 결과 처리 (collect_data와 동일한 패턴)
        if "messages" not in result:
            logger.error(f"❌ result에 'messages' 키가 없습니다. result: {result}")
            if hasattr(result, "messages"):
                messages_list = result.messages
            else:
                messages_list = [result] if hasattr(result, "content") else []
        else:
            messages_list = result["messages"]

        ai_messages = filter_messages(messages_list, include_types=[AIMessage])
        if not ai_messages:
            raise ValueError("No AI response generated")

        final_message: AIMessage = ai_messages[-1]

        # 메시지 히스토리 구성
        try:
            from datetime import datetime

            full_message_history = []
            msg_list: list[dict] = convert_to_openai_messages(messages_list)
            full_message_history.extend(msg_list)
        except Exception as e:
            logger.error(f"❌ 메시지 히스토리 구성 중 오류: {e}")
            full_message_history = []

        # 도구 호출 횟수 계산
        tool_calls_made = sum(
            len(msg.tool_calls)
            for msg in filter_messages(messages_list, include_types=[AIMessage])
            if hasattr(msg, "tool_calls") and msg.tool_calls
        )

        logger.info("🎯 포트폴리오 최적화 완료:")
        logger.info(f"   → 총 도구 호출 횟수: {tool_calls_made}")
        logger.info(f"   → 총 메시지 수: {len(messages_list)}")

        return {
            "success": True,
            "result": {
                "raw_response": final_message.content,
                "optimization_config": {
                    "stock_scores": stock_scores,
                    "current_weights": current_weights,
                    "risk_constraints": risk_constraints,
                },
                "tool_calls_made": tool_calls_made,
                "total_messages_count": len(result["messages"]),
                "timestamp": datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat(),
            },
            "full_messages": full_message_history,
            "agent_type": "PortfolioLangGraphAgent",
            "workflow_status": "completed",
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ 포트폴리오 최적화 실패: {e}")
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "agent_type": "PortfolioLangGraphAgent",
            "agent_implementation": "create_react_agent",
            "workflow_status": "failed",
        }
