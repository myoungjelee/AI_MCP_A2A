"""
주식 추천 에이전트 - 기존 MCP 서버들을 통합한 단순한 에이전트

기존 MCP 서버들(naver_news, stock_analysis, financial_analysis, macroeconomic, kiwoom, tavily_search)을
직접 통합하여 주식 추천 및 포트폴리오 제안을 제공합니다.

A2A 복잡성 없이 단순하게 구현하여 개발 기술 중심의 포트폴리오를 어필합니다.
"""

from typing import Any, Dict, List, Optional
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


async def create_stock_recommendation_agent(
    model=None, is_debug: bool = False, checkpointer=None
):
    """
    create_react_agent를 통한 주식 추천 에이전트

    모든 MCP 서버의 도구들을 로딩하고 프롬프트를 설정한 후 create_react_agent를 생성합니다.

    Args:
        model: LLM 모델 (기본값: gpt-5)
        is_debug: 디버그 모드 여부
        checkpointer: 체크포인터 (기본값: MemorySaver)

    Returns:
        create_react_agent로 생성된 LangGraph Agent

    Usage:
        agent = await create_stock_recommendation_agent()
        result = await agent.ainvoke({"messages": [...]})
    """
    try:
        # 1. 모든 MCP 도구 로딩
        from .base.mcp_config import (
            load_analysis_tools,
            load_data_collector_tools,
            load_portfolio_tools,
        )
        from .prompts import get_prompt

        # 모든 MCP 도구들을 통합
        data_tools = await load_data_collector_tools()
        analysis_tools = await load_analysis_tools()
        portfolio_tools = await load_portfolio_tools()

        all_tools = data_tools + analysis_tools + portfolio_tools

        logger.info(f"✅ Loaded {len(all_tools)} MCP tools for StockRecommendation")
        logger.info(f"   - Data tools: {len(data_tools)}개")
        logger.info(f"   - Analysis tools: {len(analysis_tools)}개")
        logger.info(f"   - Portfolio tools: {len(portfolio_tools)}개")

        # 주식 추천용 프롬프트 (portfolio 프롬프트 사용)
        system_prompt = get_prompt("portfolio", "system", tool_count=len(all_tools))

        model = model or init_chat_model(
            model="gpt-5",
            temperature=0,
            model_provider="openai",
        )

        checkpointer = MemorySaver()
        config = RunnableConfig(recursion_limit=15)  # 주식 추천은 더 많은 단계 필요

        agent = create_react_agent(
            model=model,
            tools=all_tools,
            prompt=system_prompt,
            checkpointer=checkpointer,
            name="StockRecommendationAgent",
            debug=is_debug,
            context_schema=config,
        )

        logger.info(
            "✅ StockRecommendation Agent created successfully with create_react_agent"
        )
        return agent
    except Exception as e:
        logger.error(f"Failed to create StockRecommendation Agent: {e}")
        raise RuntimeError(f"StockRecommendation Agent creation failed: {e}") from e


async def get_stock_recommendations(
    agent: CompiledStateGraph,
    user_preference: str = "",
    risk_tolerance: str = "moderate",
    investment_horizon: str = "medium",
    target_amount: Optional[float] = None,
    context_id: str | None = None,
) -> Dict[str, Any]:
    """
    주식 추천 실행 헬퍼 함수

    create_react_agent로 생성된 agent를 사용하여 주식 추천을 생성합니다.

    Args:
        agent: create_stock_recommendation_agent()로 생성된 에이전트
        user_preference: 사용자 투자 선호도 (예: "성장주", "배당주", "안전주")
        risk_tolerance: 리스크 허용도 (conservative, moderate, aggressive)
        investment_horizon: 투자 기간 (short, medium, long)
        target_amount: 목표 투자 금액 (선택적)
        context_id: 컨텍스트 ID (선택적)

    Returns:
        주식 추천 결과 딕셔너리
    """
    try:
        # 사용자 요청 구성
        user_prompt = f"""주식 추천 요청:
        투자 선호도: {user_preference or '성장성과 안정성의 균형'}
        리스크 허용도: {risk_tolerance}
        투자 기간: {investment_horizon}
        {f'목표 투자 금액: {target_amount:,.0f}원' if target_amount else ''}

        위 조건에 맞는 한국 주식들을 추천하고, 포트폴리오를 구성해주세요.
        다음 단계를 따라주세요:
        1. 시장 데이터 수집 및 분석
        2. 기술적/기본적/감성/거시경제 분석
        3. 조건에 맞는 주식 선별
        4. 포트폴리오 구성 및 최적화
        5. 리스크-수익률 분석
        6. 구체적인 투자 제안서 작성

        모든 분석 과정을 상세히 보여주고, 최종 추천을 명확하게 제시해주세요."""

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
                f"📝 create_react_agent 메시지 히스토리 구성 완료: {len(full_message_history)}개 메시지"
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

        logger.info("🎯 create_react_agent 실행 완료 - 주식 추천 요약:")
        logger.info(f"   → 총 도구 호출 횟수: {tool_calls_made}")
        logger.info(f"   → 총 메시지 수: {len(messages_list)}")
        logger.info(f"   → 투자 선호도: {user_preference}")
        logger.info(f"   → 리스크 허용도: {risk_tolerance}")

        # 실행 결과 Dictionary 반환
        return {
            "success": True,
            "result": {
                "raw_recommendation": final_message.content,
                "user_preference": user_preference,
                "risk_tolerance": risk_tolerance,
                "investment_horizon": investment_horizon,
                "target_amount": target_amount,
                "tool_calls_made": tool_calls_made,
                "total_messages_count": len(result["messages"]),
                "timestamp": datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat(),
            },
            "full_messages": full_message_history,
            "agent_type": "StockRecommendationLangGraphAgent",
            "workflow_status": "completed",
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ create_react_agent 기반 주식 추천 실패: {e}")
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "agent_type": "StockRecommendationLangGraphAgent",
            "agent_implementation": "create_react_agent",
            "workflow_status": "failed",
        }


async def analyze_market_trends(
    agent: CompiledStateGraph,
    sectors: List[str] = None,
    market_cap_range: str = "all",
    context_id: str | None = None,
) -> Dict[str, Any]:
    """
    시장 트렌드 분석 실행 헬퍼 함수

    Args:
        agent: create_stock_recommendation_agent()로 생성된 에이전트
        sectors: 분석할 섹터 목록 (예: ["IT", "반도체", "바이오"])
        market_cap_range: 시가총액 범위 (small, medium, large, all)
        context_id: 컨텍스트 ID (선택적)

    Returns:
        시장 트렌드 분석 결과 딕셔너리
    """
    try:
        sectors_str = ", ".join(sectors) if sectors else "전체 시장"

        user_prompt = f"""시장 트렌드 분석 요청:
        분석 섹터: {sectors_str}
        시가총액 범위: {market_cap_range}
        
        현재 시장 상황을 종합적으로 분석하고 다음을 제시해주세요:
        1. 전반적인 시장 동향
        2. 섹터별 성과 분석
        3. 주요 이슈 및 뉴스 영향
        4. 향후 전망 및 투자 기회
        5. 리스크 요인 분석
        
        구체적인 데이터와 근거를 바탕으로 분석해주세요."""

        messages = [HumanMessage(content=user_prompt)]

        result = await agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": context_id or str(uuid4())}},
        )

        # 결과 처리 (get_stock_recommendations와 동일한 패턴)
        if "messages" not in result:
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

        logger.info("📊 시장 트렌드 분석 완료:")
        logger.info(f"   → 총 도구 호출 횟수: {tool_calls_made}")
        logger.info(f"   → 분석 섹터: {sectors_str}")

        return {
            "success": True,
            "result": {
                "raw_analysis": final_message.content,
                "sectors_analyzed": sectors,
                "market_cap_range": market_cap_range,
                "tool_calls_made": tool_calls_made,
                "total_messages_count": len(result["messages"]),
                "timestamp": datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat(),
            },
            "full_messages": full_message_history,
            "agent_type": "StockRecommendationLangGraphAgent",
            "workflow_status": "completed",
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ 시장 트렌드 분석 실패: {e}")
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "agent_type": "StockRecommendationLangGraphAgent",
            "agent_implementation": "create_react_agent",
            "workflow_status": "failed",
        }


async def create_custom_portfolio(
    agent: CompiledStateGraph,
    investment_goals: List[str],
    risk_profile: str,
    time_horizon: str,
    budget: float,
    context_id: str | None = None,
) -> Dict[str, Any]:
    """
    맞춤형 포트폴리오 생성 실행 헬퍼 함수

    Args:
        agent: create_stock_recommendation_agent()로 생성된 에이전트
        investment_goals: 투자 목표 (예: ["성장", "배당", "안정성"])
        risk_profile: 리스크 프로필 (conservative, moderate, aggressive)
        time_horizon: 투자 기간 (short, medium, long)
        budget: 투자 예산
        context_id: 컨텍스트 ID (선택적)

    Returns:
        맞춤형 포트폴리오 생성 결과 딕셔너리
    """
    try:
        goals_str = ", ".join(investment_goals)

        user_prompt = f"""맞춤형 포트폴리오 생성 요청:
        투자 목표: {goals_str}
        리스크 프로필: {risk_profile}
        투자 기간: {time_horizon}
        투자 예산: {budget:,.0f}원
        
        위 조건에 맞는 맞춤형 포트폴리오를 생성해주세요:
        1. 목표에 맞는 주식 선별
        2. 자산 배분 비율 계산
        3. 리스크-수익률 분석
        4. 구체적인 매수 전략
        5. 포트폴리오 모니터링 계획
        
        실용적이고 실행 가능한 포트폴리오를 제시해주세요."""

        messages = [HumanMessage(content=user_prompt)]

        result = await agent.ainvoke(
            {"messages": messages},
            config={"configurable": {"thread_id": context_id or str(uuid4())}},
        )

        # 결과 처리 (동일한 패턴)
        if "messages" not in result:
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

        logger.info("💼 맞춤형 포트폴리오 생성 완료:")
        logger.info(f"   → 총 도구 호출 횟수: {tool_calls_made}")
        logger.info(f"   → 투자 목표: {goals_str}")

        return {
            "success": True,
            "result": {
                "raw_portfolio": final_message.content,
                "investment_goals": investment_goals,
                "risk_profile": risk_profile,
                "time_horizon": time_horizon,
                "budget": budget,
                "tool_calls_made": tool_calls_made,
                "total_messages_count": len(result["messages"]),
                "timestamp": datetime.now(tz=pytz.timezone("Asia/Seoul")).isoformat(),
            },
            "full_messages": full_message_history,
            "agent_type": "StockRecommendationLangGraphAgent",
            "workflow_status": "completed",
            "error": None,
        }

    except Exception as e:
        logger.error(f"❌ 맞춤형 포트폴리오 생성 실패: {e}")
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "agent_type": "StockRecommendationLangGraphAgent",
            "agent_implementation": "create_react_agent",
            "workflow_status": "failed",
        }
