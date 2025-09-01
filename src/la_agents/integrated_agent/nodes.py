"""
통합 에이전트 노드들

단일 통합 에이전트의 워크플로우에서 사용되는 노드들을 정의합니다.
"""

import asyncio
import logging
from typing import Any, Dict, List

from .state import (
    IntegratedAgentState,
    add_analysis_result,
    add_collected_data,
    add_error,
    add_insight,
    add_step_log,
    set_action_taken,
    set_decision,
    update_progress,
    update_step,
)

logger = logging.getLogger(__name__)


async def conversational_response(
    state: IntegratedAgentState, agent
) -> IntegratedAgentState:
    """대화형 응답 생성 노드 - Ollama LLM을 활용한 자연스러운 대화"""
    try:
        update_step(state, "generating_response")
        add_step_log(state, "conversational_response", "대화형 응답 생성 시작")

        request = state["request"]
        user_message = request.get("question", request.get("message", ""))
        history = request.get("history", [])

        # 수집된 데이터와 분석 결과 정리
        collected_data = state.get("collected_data", [])
        analysis_results = state.get("analysis_results", [])
        insights = state.get("insights", [])

        # 컨텍스트 구성 - 실제 데이터 내용 포함
        context_summary = ""
        data_content = ""

        # 수집된 데이터의 실제 내용 정리 - 안전한 처리
        if collected_data and isinstance(collected_data, (list, tuple)):
            context_summary += f"수집된 데이터: {len(collected_data)}개 소스\n"
            data_content += "\n=== 수집된 데이터 ===\n"
            # 안전한 슬라이싱
            data_slice = list(collected_data)[:5] if collected_data else []
            for i, data in enumerate(data_slice):
                if isinstance(data, dict):
                    # 데이터 요약 생성
                    data_summary = str(data)[:500]  # 500자 제한
                    data_content += f"데이터 {i+1}: {data_summary}...\n\n"

        # 분석 결과의 실제 내용 정리 - 안전한 처리
        if analysis_results and isinstance(analysis_results, (list, tuple)):
            context_summary += f"분석 결과: {len(analysis_results)}개 항목\n"
            data_content += "\n=== 분석 결과 ===\n"
            # 안전한 슬라이싱
            results_slice = list(analysis_results)[:3] if analysis_results else []
            for i, result in enumerate(results_slice):
                if isinstance(result, dict):
                    result_summary = str(result)[:300]  # 300자 제한
                    data_content += f"분석 {i+1}: {result_summary}...\n\n"

        # 인사이트의 실제 내용 정리 - 안전한 처리
        if insights and isinstance(insights, (list, tuple)):
            context_summary += f"핵심 인사이트: {len(insights)}개\n"
            data_content += "\n=== 핵심 인사이트 ===\n"
            # 안전한 슬라이싱
            insights_slice = list(insights)[:3] if insights else []
            for i, insight in enumerate(insights_slice):
                if isinstance(insight, dict):
                    insight_summary = str(insight)[:200]  # 200자 제한
                    data_content += f"인사이트 {i+1}: {insight_summary}...\n\n"

        # 대화 이력 요약
        recent_history = ""
        if history and len(history) > 1:
            recent_messages = history[-6:]  # 최근 3턴 대화
            for msg in recent_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")[:100]  # 길이 제한
                recent_history += f"{role}: {content}\n"

        # LLM 프롬프트 구성 - 실제 데이터 포함
        system_prompt = f"""당신은 전문적인 AI 투자 분석가입니다.
사용자와 자연스럽고 친근하게 대화하면서 투자 관련 질문에 답변해주세요.

현재 상황:
{context_summary}

수집된 실제 데이터와 분석 결과:
{data_content}

최근 대화:
{recent_history}

지침:
1. 자연스럽고 친근한 톤으로 대화하세요 (ChatGPT 스타일)
2. 전문적이지만 이해하기 쉽게 설명하세요
3. 위의 실제 데이터와 분석 결과를 구체적으로 활용해서 답변하세요
4. 투자 조언은 참고용임을 명시하세요
5. 추가 질문을 유도하세요
6. 답변은 충분히 자세하고 구체적으로 해주세요 (최소 200자 이상)"""

        user_prompt = f"""사용자 질문: {user_message}

위 질문에 대해 수집된 실제 데이터와 분석 결과를 바탕으로 ChatGPT처럼 자세하고 유익한 답변을 해주세요.
단순한 상태 메시지가 아닌, 실제 분석 내용을 포함한 구체적인 답변을 원합니다."""

        # Ollama LLM 호출
        if agent.llm:
            try:
                # LLM에 전체 프롬프트 전달
                full_prompt = f"{system_prompt}\n\n{user_prompt}"

                response = agent.llm.invoke(full_prompt)

                # 응답 텍스트 추출
                if hasattr(response, "content"):
                    ai_response = response.content
                elif isinstance(response, str):
                    ai_response = response
                else:
                    ai_response = str(response)

                logger.info(f"Ollama LLM 응답 생성 완료: {len(ai_response)} 문자")

            except Exception as e:
                logger.error(f"Ollama LLM 호출 실패: {e}")
                ai_response = f"""앗, AI 응답 생성에 문제가 있었어요! 😅

하지만 분석은 완료했습니다:
• 수집된 데이터: {len(collected_data)}개
• 분석 결과: {len(analysis_results)}개
• 핵심 인사이트: {len(insights)}개

다시 질문해주시거나, 더 구체적인 내용을 물어보세요!"""

        else:
            # LLM이 없을 때 기본 응답
            ai_response = f"""분석이 완료되었습니다! 📊

📈 **수집 결과:**
• 데이터 소스: {len(collected_data)}개
• 분석 항목: {len(analysis_results)}개
• 핵심 인사이트: {len(insights)}개

더 자세한 내용이나 다른 종목에 대해서도 궁금하시면 언제든 물어보세요!"""

        # 상태에 응답 저장 (이제 TypedDict에 정의되어 있어서 최종 결과에 포함됨)
        state["ai_response"] = ai_response

        # 🔍 상태 저장 확인
        logger.info("🔍 conversational_response 노드 완료:")
        logger.info(f"  - ai_response 길이: {len(ai_response)} 문자")
        logger.info(f"  - ai_response가 state에 저장됨: {'ai_response' in state}")
        logger.info("  - TypedDict에 정의되어 있어서 최종 결과에 포함될 예정")

        add_step_log(
            state,
            "conversational_response",
            f"대화형 응답 생성 완료: {len(ai_response)} 문자",
        )
        update_progress(state, 1.0)  # 100% 완료

        return state

    except Exception as e:
        logger.error(f"대화형 응답 생성 실패: {e}")
        add_error(state, "conversational_response", f"응답 생성 실패: {e}")

        # 폴백 응답
        state[
            "ai_response"
        ] = """죄송해요, 응답 생성 중 문제가 발생했습니다. 😅

다시 시도해보시거나 다른 질문을 해주세요!"""

        return state


async def validate_request(state: IntegratedAgentState) -> IntegratedAgentState:
    """요청 검증 노드"""
    try:
        update_step(state, "validating_request")
        add_step_log(state, "validate_request", "요청 검증 시작")

        request = state["request"]
        task_type = state["task_type"]

        # 필수 필드 검증
        if not request:
            raise ValueError("요청 데이터가 없습니다")

        # 작업 타입 검증
        valid_task_types = [
            "comprehensive_analysis",
            "data_collection",
            "market_analysis",
            "investment_decision",
            "trading_execution",
        ]

        if task_type not in valid_task_types:
            raise ValueError(f"지원하지 않는 작업 타입: {task_type}")

        add_step_log(state, "validate_request", f"요청 검증 완료: {task_type}")
        update_progress(state, 0.05)

        return state

    except Exception as e:
        add_error(state, "validate_request", f"요청 검증 실패: {e}")
        add_step_log(state, "validate_request", f"요청 검증 실패: {e}", "error")
        raise


async def collect_comprehensive_data(
    state: IntegratedAgentState,
    mcp_client=None,
    mcp_tools=None,
) -> IntegratedAgentState:
    """종합 데이터 수집 노드"""
    try:
        update_step(state, "collecting_data")
        add_step_log(state, "collect_data", "종합 데이터 수집 시작")

        if mcp_tools and len(mcp_tools) > 0:
            # 실제 MCP 도구들을 사용하여 데이터 수집
            add_step_log(
                state,
                "collect_data",
                f"MCP 도구 {len(mcp_tools)}개 사용하여 데이터 수집",
            )

            # 도구별로 데이터 수집
            for tool in mcp_tools:
                try:
                    add_step_log(
                        state, "collect_data", f"도구 '{tool.name}' 실행 중..."
                    )

                    # 각 도구를 실행하여 데이터 수집 (올바른 파라미터 매핑)
                    symbol = _extract_symbol_from_request(state["request"])
                    logger.info(f"추출된 종목명: {symbol}")
                    add_step_log(state, "collect_data", f"대상 종목: {symbol}")

                    if "macroeconomic" in tool.name.lower():
                        # 거시경제 도구 - 경제 지표 요청
                        result = await tool.ainvoke({"query": "economic_indicators"})
                        add_collected_data(
                            state, "economic", result, "macroeconomic_mcp", "real"
                        )
                    elif "financial" in tool.name.lower():
                        # 재무분석 도구 - 기업 재무 데이터
                        result = await tool.ainvoke({"symbol": symbol})
                        add_collected_data(
                            state, "financial", result, "financial_analysis_mcp", "real"
                        )
                    elif (
                        "stock" in tool.name.lower()
                        and "kiwoom" not in tool.name.lower()
                    ):
                        # 주식분석 도구 - 기술적 분석
                        result = await tool.ainvoke({"symbol": symbol})
                        add_collected_data(
                            state, "stock", result, "stock_analysis_mcp", "real"
                        )
                    elif (
                        tool.name.lower()
                        in [
                            "get_stock_price",
                            "get_stock_info",
                            "get_market_status",
                            "search_stock_by_name",
                        ]
                        or "get_stock" in tool.name.lower()
                    ):
                        # 키움 도구 - stock_code 파라미터 사용
                        # 먼저 키움 API로 종목코드 검색 시도
                        stock_code = await _symbol_to_stock_code_async(
                            symbol, mcp_tools
                        )
                        logger.info(f"키움 도구용 종목코드: {symbol} -> {stock_code}")

                        if "price" in tool.name.lower():
                            params = {"stock_code": stock_code}
                            logger.info(f"키움 도구 '{tool.name}' 파라미터: {params}")
                            result = await tool.ainvoke(params)
                        elif "info" in tool.name.lower():
                            params = {"stock_code": stock_code}
                            logger.info(f"키움 도구 '{tool.name}' 파라미터: {params}")
                            result = await tool.ainvoke(params)
                        elif "market" in tool.name.lower():
                            result = await tool.ainvoke({})  # get_market_status 등
                        else:
                            # 다른 키움 도구들도 stock_code 사용
                            result = await tool.ainvoke({"stock_code": stock_code})
                        add_collected_data(
                            state, "stock_price", result, "kiwoom_mcp", "real"
                        )
                    elif "news" in tool.name.lower():
                        # 뉴스 검색 도구 - 더 구체적인 파라미터 매핑
                        if "stock_news" in tool.name.lower():
                            # get_stock_news 도구의 경우
                            result = await tool.ainvoke(
                                {"company": symbol, "max_results": 10}
                            )
                        else:
                            # 일반 뉴스 검색
                            result = await tool.ainvoke({"query": symbol})
                        add_collected_data(
                            state, "news", result, "naver_news_mcp", "real"
                        )
                    elif "search" in tool.name.lower() or "tavily" in tool.name.lower():
                        # 검색 도구
                        result = await tool.ainvoke({"query": f"{symbol} 분석"})
                        add_collected_data(
                            state, "search", result, "tavily_search_mcp", "real"
                        )

                    add_step_log(state, "collect_data", f"도구 '{tool.name}' 완료")

                except Exception as e:
                    add_step_log(
                        state,
                        "collect_data",
                        f"도구 '{tool.name}' 실행 실패: {e}",
                        "warning",
                    )
                    logger.warning(f"MCP 도구 실행 실패: {tool.name} - {e}")

        else:
            # 폴백: 시뮬레이션 데이터 사용
            add_step_log(
                state, "collect_data", "MCP 도구 없음 - 시뮬레이션 데이터 사용"
            )

            # 1. 거시경제 데이터 수집
            add_step_log(state, "collect_data", "거시경제 데이터 수집 중...")
            economic_data = await _collect_economic_data()
            add_collected_data(
                state, "economic", economic_data, "macroeconomic_mcp", "simulation"
            )

            # 2. 재무 데이터 수집
            add_step_log(state, "collect_data", "재무 데이터 수집 중...")
            financial_data = await _collect_financial_data()
            add_collected_data(
                state,
                "financial",
                financial_data,
                "financial_analysis_mcp",
                "simulation",
            )

            # 3. 주식 데이터 수집
            add_step_log(state, "collect_data", "주식 데이터 수집 중...")
            stock_data = await _collect_stock_data()
            add_collected_data(
                state, "stock", stock_data, "stock_analysis_mcp", "simulation"
            )

            # 4. 뉴스 데이터 수집
            add_step_log(state, "collect_data", "뉴스 데이터 수집 중...")
            news_data = await _collect_news_data()
            add_collected_data(state, "news", news_data, "naver_news_mcp", "simulation")

            # 5. 검색 데이터 수집
            add_step_log(state, "collect_data", "검색 데이터 수집 중...")
            search_data = await _collect_search_data()
            add_collected_data(
                state, "search", search_data, "tavily_search_mcp", "simulation"
            )

        add_step_log(state, "collect_data", "종합 데이터 수집 완료")
        update_progress(state, 0.3)

        return state

    except Exception as e:
        add_error(state, "collect_comprehensive_data", f"데이터 수집 실패: {e}")
        add_step_log(state, "collect_data", f"데이터 수집 실패: {e}", "error")
        return state


async def perform_comprehensive_analysis(
    state: IntegratedAgentState,
) -> IntegratedAgentState:
    """종합 분석 노드"""
    try:
        update_step(state, "analyzing_data")
        add_step_log(state, "analyze_data", "종합 분석 시작")

        collected_data = state["collected_data"]

        # 1. 기술적 분석
        add_step_log(state, "analyze_data", "기술적 분석 수행 중...")
        technical_analysis = await _perform_technical_analysis(
            collected_data.get("stock", [])
        )
        add_analysis_result(state, "technical", technical_analysis)

        # 2. 기본적 분석
        add_step_log(state, "analyze_data", "기본적 분석 수행 중...")
        fundamental_analysis = await _perform_fundamental_analysis(
            collected_data.get("financial", [])
        )
        add_analysis_result(state, "fundamental", fundamental_analysis)

        # 3. 뉴스 감정 분석
        add_step_log(state, "analyze_data", "뉴스 감정 분석 수행 중...")
        sentiment_analysis = await _perform_sentiment_analysis(
            collected_data.get("news", [])
        )
        add_analysis_result(state, "sentiment", sentiment_analysis)

        # 4. 시장 환경 분석
        add_step_log(state, "analyze_data", "시장 환경 분석 수행 중...")
        market_analysis = await _perform_market_analysis(
            collected_data.get("economic", [])
        )
        add_analysis_result(state, "market", market_analysis)

        # 5. 종합 인사이트 도출
        add_step_log(state, "analyze_data", "종합 인사이트 도출 중...")
        insights = await _generate_comprehensive_insights(state["analysis_results"])
        for insight in insights:
            add_insight(state, insight)

        add_step_log(state, "analyze_data", "종합 분석 완료")
        update_progress(state, 0.6)

        return state

    except Exception as e:
        add_error(state, "perform_comprehensive_analysis", f"분석 실패: {e}")
        add_step_log(state, "analyze_data", f"분석 실패: {e}", "error")
        return state


async def make_intelligent_decision(
    state: IntegratedAgentState,
    agent=None,
) -> IntegratedAgentState:
    """지능적 의사결정 노드 (로컬 LLM 활용)"""
    try:
        update_step(state, "making_decision")
        add_step_log(state, "make_decision", "지능적 의사결정 시작")

        # LLM이 사용 가능한 경우 복합적 추론 수행
        if agent and agent.llm:
            decision = await _make_llm_decision(agent.llm, state["analysis_results"])
        else:
            # LLM이 없는 경우 간단한 규칙 기반 결정
            decision = await _make_rule_based_decision(state["analysis_results"])

        set_decision(state, decision)
        add_step_log(state, "make_decision", f"최종 결정: {decision.get('action')}")
        update_progress(state, 75.0)

        return state

    except Exception as e:
        add_error(state, "make_decision", str(e))
        add_step_log(state, "make_decision", f"의사결정 실패: {e}", "error")
        return state


async def execute_action(state: IntegratedAgentState) -> IntegratedAgentState:
    """액션 실행 노드"""
    try:
        update_step(state, "executing_action")
        add_step_log(state, "execute_action", "액션 실행 시작")

        decision = state["decision"]

        if not decision:
            add_step_log(state, "execute_action", "실행할 결정이 없습니다")
            update_progress(state, 1.0)
            return state

        # 결정에 따른 액션 실행
        action_result = await _execute_decision_action(decision)

        # 실행 결과 설정
        set_action_taken(state, action_result, "completed")

        add_step_log(
            state, "execute_action", f"액션 실행 완료: {action_result['action_type']}"
        )
        update_progress(state, 1.0)

        return state

    except Exception as e:
        add_error(state, "execute_action", f"액션 실행 실패: {e}")
        add_step_log(state, "execute_action", f"액션 실행 실패: {e}", "error")
        set_action_taken(state, {"error": str(e)}, "failed")
        return state


# 헬퍼 함수들
async def _collect_economic_data() -> Dict[str, Any]:
    """거시경제 데이터 수집"""
    # 실제로는 MCP 서버 호출
    await asyncio.sleep(0.1)  # 시뮬레이션
    return {
        "gdp": {"value": 2000000, "unit": "억원", "period": "2024"},
        "cpi": {"value": 2.5, "unit": "%", "period": "2024"},
        "interest_rate": {"value": 3.5, "unit": "%", "period": "2024"},
    }


async def _collect_financial_data() -> Dict[str, Any]:
    """재무 데이터 수집"""
    await asyncio.sleep(0.1)
    return {
        "revenue": {"value": 500000, "unit": "억원", "period": "2024"},
        "profit": {"value": 50000, "unit": "억원", "period": "2024"},
        "debt_ratio": {"value": 0.3, "unit": "ratio", "period": "2024"},
    }


async def _collect_stock_data() -> Dict[str, Any]:
    """주식 데이터 수집"""
    await asyncio.sleep(0.1)
    return {
        "price": {"value": 50000, "unit": "원", "period": "2024"},
        "volume": {"value": 1000000, "unit": "주", "period": "2024"},
        "market_cap": {"value": 1000000, "unit": "억원", "period": "2024"},
    }


async def _collect_news_data() -> Dict[str, Any]:
    """뉴스 데이터 수집"""
    await asyncio.sleep(0.1)
    return {
        "articles": [
            {"title": "경제 뉴스 1", "content": "내용 1", "date": "2024-01-01"},
            {"title": "경제 뉴스 2", "content": "내용 2", "date": "2024-01-02"},
        ]
    }


async def _collect_search_data() -> Dict[str, Any]:
    """검색 데이터 수집"""
    await asyncio.sleep(0.1)
    return {
        "search_results": [
            {"title": "검색 결과 1", "url": "http://example1.com", "snippet": "요약 1"},
            {"title": "검색 결과 2", "url": "http://example2.com", "snippet": "요약 2"},
        ]
    }


async def _perform_technical_analysis(stock_data: List[Any]) -> Dict[str, Any]:
    """기술적 분석"""
    await asyncio.sleep(0.1)
    return {
        "trend": "상승",
        "support_level": 48000,
        "resistance_level": 52000,
        "rsi": 65,
        "macd": "양수",
        "score": 0.75,
    }


async def _perform_fundamental_analysis(financial_data: List[Any]) -> Dict[str, Any]:
    """기본적 분석"""
    await asyncio.sleep(0.1)
    return {
        "pe_ratio": 15.5,
        "pb_ratio": 1.2,
        "roe": 0.12,
        "debt_ratio": 0.3,
        "score": 0.8,
    }


async def _perform_sentiment_analysis(news_data: List[Any]) -> Dict[str, Any]:
    """감정 분석"""
    await asyncio.sleep(0.1)
    return {
        "positive_ratio": 0.6,
        "negative_ratio": 0.2,
        "neutral_ratio": 0.2,
        "overall_sentiment": "긍정적",
        "score": 0.7,
    }


async def _perform_market_analysis(economic_data: List[Any]) -> Dict[str, Any]:
    """시장 환경 분석"""
    await asyncio.sleep(0.1)
    return {
        "market_condition": "안정적",
        "volatility": "낮음",
        "liquidity": "충분",
        "score": 0.85,
    }


async def _generate_comprehensive_insights(
    analysis_results: Dict[str, Any],
) -> List[str]:
    """종합 인사이트 도출"""
    await asyncio.sleep(0.1)
    return [
        "기술적 지표가 상승 추세를 보이고 있습니다",
        "기본적 지표도 양호한 수준을 유지하고 있습니다",
        "뉴스 감정이 전반적으로 긍정적입니다",
        "시장 환경이 안정적이어서 투자하기 좋은 시기입니다",
    ]


async def _make_llm_decision(llm, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """로컬 LLM을 사용한 복합적 의사결정"""
    try:
        # 분석 결과를 요약
        analysis_summary = _summarize_analysis_results(analysis_results)

        # LLM 프롬프트 구성
        prompt = f"""
당신은 전문 투자 분석가입니다. 다음 분석 결과를 바탕으로 투자 결정을 내려주세요.

## 분석 결과 요약
{analysis_summary}

## 투자 결정 가이드라인
- 기술적 분석이 강한 매수 신호를 보이면 BUY 고려
- 기본적 분석에서 재무 상태가 양호하면 BUY 고려
- 감성 분석이 부정적이면 SELL 고려
- 시장 분석에서 리스크가 높으면 HOLD 고려
- 모든 지표가 중립적이면 HOLD 권장

## 출력 형식
다음 JSON 형식으로 응답해주세요:
{{
    "action": "BUY|SELL|HOLD",
    "confidence": 0.0-100.0,
    "reasoning": "결정 근거 설명",
    "risk_level": "LOW|MEDIUM|HIGH",
    "recommended_position_size": "SMALL|MEDIUM|LARGE"
}}

투자 결정을 내려주세요:
"""

        # LLM 호출
        response = await llm.ainvoke(prompt)

        # 응답 파싱
        try:
            import json

            decision = json.loads(response)
            return decision
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 결정
            return {
                "action": "HOLD",
                "confidence": 50.0,
                "reasoning": "LLM 응답 파싱 실패로 기본 결정",
                "risk_level": "MEDIUM",
                "recommended_position_size": "SMALL",
            }

    except Exception as e:
        logger.error(f"LLM 의사결정 실패: {e}")
        return await _make_rule_based_decision(analysis_results)


def _summarize_analysis_results(analysis_results: Dict[str, Any]) -> str:
    """분석 결과를 요약하는 함수"""
    summary = []

    # 기술적 분석
    if "technical" in analysis_results:
        tech = analysis_results["technical"]
        summary.append(
            f"기술적 분석: RSI={tech.get('rsi', 'N/A')}, MACD={tech.get('macd', 'N/A')}"
        )

    # 기본적 분석
    if "fundamental" in analysis_results:
        fund = analysis_results["fundamental"]
        summary.append(
            f"기본적 분석: PER={fund.get('per', 'N/A')}, ROE={fund.get('roe', 'N/A')}"
        )

    # 감성 분석
    if "sentiment" in analysis_results:
        sent = analysis_results["sentiment"]
        summary.append(
            f"감성 분석: {sent.get('overall_sentiment', 'N/A')}, 점수={sent.get('score', 'N/A')}"
        )

    # 시장 분석
    if "market" in analysis_results:
        market = analysis_results["market"]
        summary.append(
            f"시장 분석: 트렌드={market.get('market_trend', 'N/A')}, 리스크={market.get('risk_level', 'N/A')}"
        )

    return "\n".join(summary) if summary else "분석 데이터 없음"


async def _make_rule_based_decision(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """규칙 기반 의사결정 (LLM 없을 때 폴백)"""
    # 간단한 규칙 기반 로직
    technical_score = 0.5
    fundamental_score = 0.5
    sentiment_score = 0.5
    market_score = 0.5

    # 기술적 분석 점수 계산
    if "technical" in analysis_results:
        tech = analysis_results["technical"]
        if tech.get("macd") == "buy_signal":
            technical_score = 0.8
        elif tech.get("macd") == "sell_signal":
            technical_score = 0.2

    # 기본적 분석 점수 계산
    if "fundamental" in analysis_results:
        fund = analysis_results["fundamental"]
        per = fund.get("per", 15)
        if per < 10:
            fundamental_score = 0.8
        elif per > 20:
            fundamental_score = 0.3

    # 감성 분석 점수 계산
    if "sentiment" in analysis_results:
        sent = analysis_results["sentiment"]
        sentiment = sent.get("overall_sentiment", "neutral")
        if sentiment == "positive":
            sentiment_score = 0.8
        elif sentiment == "negative":
            sentiment_score = 0.2

    # 가중 평균 계산
    weighted_score = (
        technical_score * 0.4
        + fundamental_score * 0.3
        + sentiment_score * 0.2
        + market_score * 0.1
    )

    # 결정 로직
    if weighted_score > 0.7:
        action = "BUY"
        confidence = weighted_score * 100
    elif weighted_score < 0.3:
        action = "SELL"
        confidence = (1 - weighted_score) * 100
    else:
        action = "HOLD"
        confidence = 50.0

    return {
        "action": action,
        "confidence": confidence,
        "reasoning": f"규칙 기반 결정 (점수: {weighted_score:.2f})",
        "risk_level": "MEDIUM",
        "recommended_position_size": "SMALL",
    }


async def _execute_decision_action(decision: Dict[str, Any]) -> Dict[str, Any]:
    """결정에 따른 액션 실행"""
    await asyncio.sleep(0.1)

    action = decision.get("action", "HOLD")

    if action == "BUY":
        return {
            "action_type": "BUY_ORDER",
            "status": "executed",
            "details": "매수 주문 실행됨",
        }
    elif action == "SELL":
        return {
            "action_type": "SELL_ORDER",
            "status": "executed",
            "details": "매도 주문 실행됨",
        }
    else:
        return {
            "action_type": "HOLD",
            "status": "completed",
            "details": "관망 상태 유지",
        }


# ============================================================================
# MCP 도구 사용 헬퍼 함수들
# ============================================================================


async def _use_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """MCP 도구 사용 헬퍼"""
    try:
        # 실제 MCP 도구 사용 로직 (현재는 시뮬레이션)
        # TODO: 실제 MCP 클라이언트에서 도구 호출
        logger.info(f"MCP 도구 사용: {tool_name} with {kwargs}")

        # 시뮬레이션된 결과 반환
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "tool_name": tool_name,
            "result": f"Mock result from {tool_name}",
            "data": {"mock": True, "params": kwargs},
        }

    except Exception as e:
        logger.error(f"MCP 도구 사용 실패: {tool_name} - {e}")
        return {"success": False, "tool_name": tool_name, "error": str(e)}


async def _collect_data_with_mcp(
    server_name: str, tool_name: str, **kwargs
) -> Dict[str, Any]:
    """MCP 서버를 통한 데이터 수집"""
    try:
        full_tool_name = f"{server_name}_{tool_name}"
        result = await _use_mcp_tool(full_tool_name, **kwargs)

        if result["success"]:
            logger.info(f"MCP 데이터 수집 성공: {server_name}.{tool_name}")
            return result["data"]
        else:
            logger.warning(f"MCP 데이터 수집 실패: {server_name}.{tool_name}")
            return {"error": result["error"]}

    except Exception as e:
        logger.error(f"MCP 데이터 수집 예외: {server_name}.{tool_name} - {e}")
        return {"error": str(e)}


async def _analyze_with_mcp(
    server_name: str, tool_name: str, data: Dict[str, Any]
) -> Dict[str, Any]:
    """MCP 서버를 통한 데이터 분석"""
    try:
        full_tool_name = f"{server_name}_{tool_name}"
        result = await _use_mcp_tool(full_tool_name, data=data, **data)

        if result["success"]:
            logger.info(f"MCP 분석 성공: {server_name}.{tool_name}")
            return result["data"]
        else:
            logger.warning(f"MCP 분석 실패: {server_name}.{tool_name}")
            return {"error": result["error"]}

    except Exception as e:
        logger.error(f"MCP 분석 예외: {server_name}.{tool_name} - {e}")
        return {"error": str(e)}


# 헬퍼 함수들
def _extract_symbol_from_request(request: Dict[str, Any]) -> str:
    """사용자 요청에서 종목명 추출"""
    # 우선순위: symbol > question 키워드 추출 > 기본값
    if "symbol" in request:
        return request["symbol"]

    question = request.get("question", request.get("message", ""))

    # 확장된 종목명 매핑 (kiwoom_mcp 방식 참고)
    stock_keywords = {
        # 삼성 그룹
        "삼성전자": "삼성전자",
        "삼성": "삼성전자",
        "005930": "삼성전자",
        "samsung": "삼성전자",
        "삼성sdi": "삼성SDI",
        "삼성SDI": "삼성SDI",
        "006400": "삼성SDI",
        "삼성바이오": "삼성바이오로직스",
        "삼성바이오로직스": "삼성바이오로직스",
        "207940": "삼성바이오로직스",
        # IT 플랫폼
        "네이버": "네이버",
        "naver": "네이버",
        "035420": "네이버",
        "카카오": "카카오",
        "kakao": "카카오",
        "035720": "카카오",
        # 반도체
        "sk하이닉스": "SK하이닉스",
        "하이닉스": "SK하이닉스",
        "000660": "SK하이닉스",
        "sk hynix": "SK하이닉스",
        # 화학/소재
        "lg화학": "LG화학",
        "051910": "LG화학",
        # 자동차
        "현대차": "현대자동차",
        "현대자동차": "현대자동차",
        "005380": "현대자동차",
        "hyundai": "현대자동차",
        "기아": "기아",
        "kia": "기아",
        "000270": "기아",
        "현대모비스": "현대모비스",
        "012330": "현대모비스",
        # 철강/화학
        "포스코": "포스코홀딩스",
        "포스코홀딩스": "포스코홀딩스",
        "005490": "포스코홀딩스",
        "posco": "포스코홀딩스",
        # 바이오/제약
        "셀트리온": "셀트리온",
        "068270": "셀트리온",
        "celltrion": "셀트리온",
        # 금융
        "kb금융": "KB금융",
        "KB금융": "KB금융",
        "kb": "KB금융",
        "105560": "KB금융",
        "신한": "신한지주",
        "신한지주": "신한지주",
        "055550": "신한지주",
        "shinhan": "신한지주",
        "우리금융": "우리금융지주",
        "우리금융지주": "우리금융지주",
        "316140": "우리금융지주",
        "하나금융": "하나금융지주",
        "하나금융지주": "하나금융지주",
        "086790": "하나금융지주",
        # 전자/가전
        "lg전자": "LG전자",
        "066570": "LG전자",
        # 통신
        "sk텔레콤": "SK텔레콤",
        "skt": "SK텔레콤",
        "017670": "SK텔레콤",
        "kt": "KT",
        "030200": "KT",
        "lg유플러스": "LG유플러스",
        "lgu+": "LG유플러스",
        "032640": "LG유플러스",
        # 공기업/유틸리티
        "한국전력": "한국전력",
        "한전": "한국전력",
        "015760": "한국전력",
        "kepco": "한국전력",
        # 해외 주요 종목
        "테슬라": "테슬라",
        "tesla": "테슬라",
        "tsla": "테슬라",
        "애플": "애플",
        "apple": "애플",
        "aapl": "애플",
        "구글": "구글",
        "google": "구글",
        "googl": "구글",
        "마이크로소프트": "마이크로소프트",
        "microsoft": "마이크로소프트",
        "msft": "마이크로소프트",
        "아마존": "아마존",
        "amazon": "아마존",
        "amzn": "아마존",
        "메타": "메타",
        "meta": "메타",
        "facebook": "메타",
        # 암호화폐
        "비트코인": "비트코인",
        "bitcoin": "비트코인",
        "btc": "비트코인",
        "이더리움": "이더리움",
        "ethereum": "이더리움",
        "eth": "이더리움",
    }

    question_lower = question.lower()
    for keyword, symbol in stock_keywords.items():
        if keyword in question_lower:
            return symbol

    # 기본값
    return "삼성전자"


def _symbol_to_stock_code(symbol: str) -> str:
    """종목명을 종목코드로 변환 (키움 API 사용 시뮬레이션)"""
    # 실제로는 키움 MCP 서버의 search_stock_by_name 도구를 사용해야 함
    # 현재는 로컬 매핑으로 시뮬레이션
    symbol_to_code = {
        "삼성전자": "005930",
        "네이버": "035420",
        "NAVER": "035420",
        "카카오": "035720",
        "KAKAO": "035720",
        "SK하이닉스": "000660",
        "LG화학": "051910",
        "현대자동차": "005380",
        "현대차": "005380",
        "포스코": "005490",
        "셀트리온": "068270",
        "KB금융": "105560",
        "신한지주": "055550",
        "LG전자": "066570",
        "한국전력": "015760",
        "기아": "000270",
    }

    return symbol_to_code.get(symbol, "005930")  # 기본값: 삼성전자


async def _symbol_to_stock_code_async(symbol: str, mcp_tools=None) -> str:
    """종목명을 종목코드로 비동기 변환 (키움 API 사용)"""
    try:
        # 키움 검색 도구 찾기
        if mcp_tools:
            for tool in mcp_tools:
                if "search_stock_by_name" in tool.name.lower():
                    result = await tool.ainvoke({"company_name": symbol})
                    if result.get("success") and result.get("stock_code"):
                        logger.info(
                            f"키움 API 검색 성공: {symbol} -> {result['stock_code']}"
                        )
                        return result["stock_code"]
                    break

        # 폴백: 로컬 매핑 사용
        return _symbol_to_stock_code(symbol)

    except Exception as e:
        logger.warning(f"키움 API 검색 실패: {e}, 로컬 매핑 사용")
        return _symbol_to_stock_code(symbol)
