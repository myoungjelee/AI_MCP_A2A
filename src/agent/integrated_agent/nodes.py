"""통합 에이전트 노드 구현 모듈 (FDR 최신 우선 + 동적 분석 서버 + as_of 주입)"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from ..base.mcp_config import MCPServerConfig
from ..base.mcp_tools_map import (
    SERVER_TOOLS_ALLOWLIST,
    select_servers_for_collection,
    select_tools_for_server,
)
from .prompts import AGENT_SYSTEM_PROMPT  # 중앙 관리 프롬프트
from .state import IntegratedAgentState, add_error, add_warning, update_current_step
from .validation import InvestmentQuestionValidator, validate_investment_question


class IntegratedAgentNodes:
    """통합 에이전트 노드 구현 클래스"""

    def __init__(self, model_name: str = "gpt-oss:20b"):
        self.model_name = model_name
        try:
            # Ollama LLM 초기화 (기본 로컬 엔드포인트)
            self.llm = ChatOllama(
                model=model_name,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0.7,
                timeout=30,
            )
            print(
                f"ChatOllama 초기화 완료: {model_name} @ {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}"
            )
        except Exception as e:
            print(f"ChatOllama 초기화 실패: {e}")
            raise

        # 투자 질문 검증기
        self.validator = InvestmentQuestionValidator(model_name)

        # MCP 클라이언트/도구 맵
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.mcp_tools_dict: Dict[str, Any] = {}

    # ---------------------------------------------------------------------
    # MCP 초기화
    # ---------------------------------------------------------------------
    async def initialize_mcp_tools(self) -> bool:
        """MCP 도구들 초기화 (안전한 버전)"""
        try:
            server_configs = MCPServerConfig.get_standard_servers()
            print(f"서버 설정 로딩 완료: {list(server_configs.keys())}")

            self.mcp_client = MultiServerMCPClient(server_configs)
            print("MCP 클라이언트 생성 완료")

            tools = await asyncio.wait_for(self.mcp_client.get_tools(), timeout=12.0)
            for tool in tools:
                self.mcp_tools_dict[tool.name] = tool

            print(f"도구 매핑 완료: {list(self.mcp_tools_dict.keys())}")
            return True
        except Exception as e:
            print(f"MCP 도구 초기화 실패: {e}")
            self.mcp_client = None
            return False

    # ---------------------------------------------------------------------
    # 1) 검증 노드
    # ---------------------------------------------------------------------
    async def validate_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        try:
            new_state = update_current_step(state, "validate")
            validated_state = await validate_investment_question(
                new_state, self.validator
            )
            return validated_state
        except Exception as e:
            error_state = add_error(
                state, f"질문 검증 중 오류: {str(e)}", "VALIDATION_ERROR"
            )
            error_state["is_investment_related"] = False
            error_state["final_response"] = (
                "질문 검증 중 오류가 발생했습니다. 다시 시도해주세요."
            )
            error_state["response_type"] = "error"
            return error_state

    # ---------------------------------------------------------------------
    # 2) 수집 노드 (FDR 최신 우선)
    # ---------------------------------------------------------------------
    async def collect_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        try:
            if not state["is_investment_related"]:
                return state

            new_state = update_current_step(state, "collect")

            # 질문 기반 서버 선택 (FDR 최우선)
            selected_servers = select_servers_for_collection(state["question"])
            selected_servers = ["financedatareader"] + [
                s for s in selected_servers if s != "financedatareader"
            ]
            new_state = update_current_step(new_state, "collect", selected_servers)

            # 서버 병렬 수집
            tasks = [
                self._collect_from_server(s, state["question"])
                for s in selected_servers
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            collected_data: Dict[str, Any] = {}
            for server, result in zip(selected_servers, results, strict=False):
                if isinstance(result, Exception):
                    new_state = add_warning(
                        new_state, f"{server} 서버에서 데이터 수집 실패: {str(result)}"
                    )
                    collected_data[server] = {"error": str(result), "status": "failed"}
                else:
                    collected_data[server] = result

            new_state["collected_data"] = collected_data
            new_state["data_collection_status"] = "completed"
            new_state["data_quality_score"] = self._calculate_data_quality(
                collected_data
            )
            return new_state

        except Exception as e:
            return add_error(
                state, f"데이터 수집 중 오류: {str(e)}", "COLLECTION_ERROR"
            )

    # ---------------------------------------------------------------------
    # 3) 분석 노드 (동적 서버 선택 + as_of 주입)
    # ---------------------------------------------------------------------
    async def analyze_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        try:
            if not state["is_investment_related"]:
                return state

            new_state = update_current_step(state, "analyze")

            # 질문 기반 동적 서버 선택
            analysis_servers = await self._select_mcp_servers_for_analysis(
                state.get("question", "")
            )
            new_state = update_current_step(new_state, "analyze", analysis_servers)

            collected_data = state.get("collected_data", {})

            # 서버별 분석 실행
            tasks = [
                self._analyze_with_server(
                    server, collected_data, state.get("question", "")
                )
                for server in analysis_servers
            ]
            analysis_results_list = await asyncio.gather(*tasks, return_exceptions=True)

            analysis_results: Dict[str, Any] = {}
            for server, result in zip(
                analysis_servers, analysis_results_list, strict=False
            ):
                if isinstance(result, Exception):
                    new_state = add_warning(
                        new_state, f"{server} 서버 분석 실패: {str(result)}"
                    )
                    analysis_results[server] = {
                        "error": str(result),
                        "status": "failed",
                    }
                else:
                    analysis_results[server] = result

            integrated_analysis = await self._integrate_analysis_results(
                analysis_results, state.get("question", "")
            )

            new_state["analysis_result"] = integrated_analysis
            new_state["analysis_confidence"] = integrated_analysis.get(
                "confidence", 0.7
            )
            new_state["key_insights"] = integrated_analysis.get("insights", [])
            return new_state

        except Exception as e:
            return add_error(state, f"데이터 분석 중 오류: {str(e)}", "ANALYSIS_ERROR")

    # ---------------------------------------------------------------------
    # 4) 의사결정 노드
    # ---------------------------------------------------------------------
    async def decide_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        try:
            if not state["is_investment_related"]:
                return state

            new_state = update_current_step(state, "decide")

            analysis_result = state.get("analysis_result", {})
            collected_data = state.get("collected_data", {})

            decision_prompt = self._create_decision_prompt(
                state["question"], analysis_result, collected_data
            )

            # ★ 시스템 메시지에 중앙 프롬프트 주입
            decision_response = await self.llm.ainvoke(
                [
                    SystemMessage(content=AGENT_SYSTEM_PROMPT),
                    HumanMessage(content=decision_prompt),
                ]
            )

            new_state.setdefault("analysis_result", {})
            new_state["analysis_result"]["decision"] = decision_response.content
            return new_state

        except Exception as e:
            return add_error(state, f"의사결정 중 오류: {str(e)}", "DECISION_ERROR")

    # ---------------------------------------------------------------------
    # 5) 응답 노드
    # ---------------------------------------------------------------------
    async def respond_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        try:
            if not state["is_investment_related"]:
                return state

            new_state = update_current_step(state, "respond")
            final_response = await self._generate_final_response(
                new_state,
                state["question"],
                state.get("analysis_result", {}),
                state.get("collected_data", {}),
                state.get("key_insights", []),
            )
            new_state["final_response"] = final_response
            new_state["response_type"] = "analysis"
            return new_state

        except Exception as e:
            error_state = add_error(
                state, f"응답 생성 중 오류: {str(e)}", "RESPONSE_ERROR"
            )
            error_state["final_response"] = (
                "응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            )
            error_state["response_type"] = "error"
            return error_state

    # =====================================================================
    # 내부 헬퍼
    # =====================================================================
    async def _select_mcp_servers_for_analysis(self, question: str) -> List[str]:
        """데이터 분석을 위한 MCP 서버 동적 선택 (FDR 우선 + 뉴스/웹/거시 조건부 추가)"""
        q = (question or "").lower()

        servers: List[str] = ["financedatareader"]  # 항상 최신 시세/기초 우선
        servers += ["financial_analysis", "stock_analysis"]  # 기본 보강

        # 뉴스/이벤트 관련 키워드면 뉴스 포함 (FDR 다음)
        if any(
            k in q
            for k in [
                "뉴스",
                "기사",
                "속보",
                "이벤트",
                "호재",
                "악재",
                "발표",
                "오늘",
                "최근",
                "방금",
            ]
        ):
            servers.insert(1, "naver_news")  # FDR 다음

        # 웹/해외/루머성 질문이면 웹 검색 포함
        if any(
            k in q
            for k in [
                "웹",
                "검색",
                "해외",
                "reddit",
                "트위터",
                "블로그",
                "링크",
                "link",
                "루머",
                "rumor",
            ]
        ):
            servers.append("tavily_search")

        # 거시 키워드면 거시 포함
        if any(
            k in q
            for k in [
                "금리",
                "cpi",
                "gdp",
                "실업률",
                "pmi",
                "환율",
                "유가",
                "연준",
                "fed",
                "frb",
                "경기",
                "거시",
                "물가",
            ]
        ):
            servers.append("macroeconomic")

        # 중복 제거 + 순서 보존
        seen = set()
        return [s for s in servers if not (s in seen or seen.add(s))]

    async def _collect_from_server(self, server: str, question: str) -> Dict[str, Any]:
        """선택 서버에서 데이터 수집 (수집 단계 freshness 강제)"""
        try:
            if not self.mcp_client:
                await self.initialize_mcp_tools()

            tools_to_use = select_tools_for_server(server, question)
            available_tools = [t for t in tools_to_use if t in self.mcp_tools_dict]

            collected_data: Dict[str, Any] = {}
            tasks = []
            names = []

            if available_tools:
                for tool_name in available_tools:
                    tool_params = self._create_tool_params(tool_name, question)
                    # freshness 강제 (수집 단계)
                    now_iso = datetime.now(timezone.utc).isoformat()
                    tool_params.setdefault("force_refresh", True)
                    tool_params.setdefault("no_cache", True)
                    tool_params.setdefault("as_of", now_iso)

                    tasks.append(self.mcp_tools_dict[tool_name].ainvoke(tool_params))
                    names.append(tool_name)

                tool_results = await asyncio.gather(*tasks, return_exceptions=True)
                for name, result in zip(names, tool_results, strict=False):
                    if isinstance(result, Exception):
                        collected_data[name] = {"error": str(result)}
                    else:
                        collected_data[name] = result

            return {
                "server": server,
                "timestamp": datetime.now().isoformat(),
                "data": collected_data,
                "status": "success" if collected_data else "partial",
                "tools_used": list(collected_data.keys()),
            }

        except Exception as e:
            return {
                "server": server,
                "timestamp": datetime.now().isoformat(),
                "data": {},
                "status": "error",
                "error": str(e),
            }

    async def _analyze_with_server(
        self, server: str, data: Dict[str, Any], question: str
    ) -> Dict[str, Any]:
        """특정 서버로 데이터 분석 (분석 단계에도 as_of 주입)"""
        try:
            if not self.mcp_client:
                await self.initialize_mcp_tools()

            analysis_tools = self._select_analysis_tools_for_server(server, question)

            analysis_results: Dict[str, Any] = {}
            for tool_name in analysis_tools:
                if tool_name in self.mcp_tools_dict:
                    try:
                        tool_params = self._create_analysis_params(
                            tool_name, data, question
                        )
                        # 최신성 기준 통일(as_of)
                        now_iso = datetime.now(timezone.utc).isoformat()
                        tool_params.setdefault("as_of", now_iso)

                        # ★ 필수 파라미터 부족 시 호출 건너뛰기
                        result = await self._safe_invoke(
                            self.mcp_tools_dict[tool_name], tool_params
                        )
                        analysis_results[tool_name] = result
                    except Exception as e:
                        print(f"분석 도구 {tool_name} 실행 실패: {e}")
                        analysis_results[tool_name] = {"error": str(e)}

            return {
                "server": server,
                "analysis": analysis_results,
                "confidence": 0.8 if analysis_results else 0.0,
                "insights": self._extract_insights_from_analysis(analysis_results),
                "tools_used": list(analysis_results.keys()),
            }

        except Exception as e:
            return {
                "server": server,
                "analysis": {},
                "confidence": 0.0,
                "error": str(e),
                "insights": [],
            }

    async def _integrate_analysis_results(
        self, results: Dict[str, Any], question: str
    ) -> Dict[str, Any]:
        """서버별 분석 결과 통합"""
        all_insights: List[str] = []
        total_confidence = 0.0
        count = 0
        for result in results.values():
            if "insights" in result:
                all_insights.extend(result["insights"])
            if "confidence" in result:
                total_confidence += result["confidence"]
                count += 1
        avg_confidence = total_confidence / count if count > 0 else 0.6
        return {
            "question": question,
            "integrated_insights": all_insights,
            "confidence": avg_confidence,
            "server_results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """수집 성공 서버 비율로 간단한 품질 점수 계산"""
        if not data:
            return 0.0
        successful_servers = sum(
            1 for v in data.values() if v.get("status") == "success"
        )
        total_servers = len(data)
        return successful_servers / total_servers if total_servers else 0.0

    def _create_decision_prompt(
        self, question: str, analysis: Dict[str, Any], data: Dict[str, Any]
    ) -> str:
        """결정용 사용자 프롬프트(간결 버전)"""
        return f"""
**질문**: {question}

**분석 결과**
- 신뢰도: {analysis.get('confidence', 0)}
- 통합 인사이트 수: {len(analysis.get('integrated_insights', []))}

**수집된 데이터 서버**: {list(data.keys())}

최신 시세(FDR)와 보강 분석을 바탕으로 명확하고 실행 가능한 권고안을 제시하세요.
"""

    async def _generate_final_response(
        self,
        state: IntegratedAgentState,
        question: str,
        analysis: Dict[str, Any],
        data: Dict[str, Any],
        insights: List[str],
    ) -> str:
        """최종 보고서 생성 (system=중앙 프롬프트 / user=짧은 지시)"""
        # user 프롬프트는 짧게: 질문만 전달하고, 출력 규격/톤/근거는 system(AGENT_SYSTEM_PROMPT)에 위임
        prompt = (
            f"사용자 질문: {question}\n위 원칙에 따라 마크다운 보고서를 작성하세요."
        )

        messages = state.get("messages", [])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(
                0,
                SystemMessage(
                    content="당신은 전문 투자 분석가입니다. 최신성과 근거를 명확히 제시하세요."
                ),
            )
        messages.append(HumanMessage(content=prompt))

        response = await self.llm.ainvoke(messages)
        new_state = state.copy()
        new_state["messages"] = messages + [AIMessage(content=response.content)]
        return response.content

    # ---------------------- 도구 선택/파라미터 ----------------------
    def _select_analysis_tools_for_server(
        self, server: str, question: str
    ) -> List[str]:
        """분석용 도구 선택 (서버별 기본 1~2개 보장)"""
        allow = SERVER_TOOLS_ALLOWLIST.get(server, [])
        q = (question or "").lower()

        if server == "financial_analysis":
            priority = ["analyze_financial_ratios", "calculate_valuation_metrics"]
            return [t for t in priority if t in allow] or allow[:2]

        if server == "stock_analysis":
            priority = ["analyze_stock_performance", "get_technical_indicators"]
            return [t for t in priority if t in allow] or allow[:2]

        if server == "naver_news":
            return [t for t in ["search_news_articles"] if t in allow] or allow[:1]

        if server == "tavily_search":
            return [t for t in ["search_web"] if t in allow] or allow[:1]

        if server == "macroeconomic":
            priority = ["get_macro_series", "search_macro_series"]
            return [t for t in priority if t in allow] or allow[:2]

        return allow[:2]

    # === [REPLACE] 수집 단계 파라미터 보강 ===
    def _create_tool_params(self, tool_name: str, question: str) -> Dict[str, Any]:
        """
        수집 단계 파라미터:
        - 뉴스/웹: query
        - 시세/체결/차트/호가: stock_code
        - 시장 개요/상태/랭킹: 대부분 파라미터 불필요
        """
        inferred = self._infer_symbols(question)
        stock_code = inferred["stock_code"]

        # 뉴스/웹 검색류
        if tool_name in {
            "search_news_articles",
            "search_news",
            "search_finance",
            "search_web",
        }:
            return {"query": question}

        # 시세/체결/차트/호가 등: 보통 stock_code 요구
        if tool_name in {
            "get_stock_basic_info",
            "get_stock_info",
            "get_daily_chart",
            "get_minute_chart",
            "get_stock_orderbook",
            "get_stock_execution_info",
        }:
            return {"stock_code": stock_code}

        # 시장 개요/상태/랭킹류
        if tool_name in {
            "get_market_overview",
            "get_market_status",
            "get_price_change_ranking",
            "get_volume_top_ranking",
            "get_foreign_trading_trend",
            "get_server_health",
            "get_server_metrics",
        }:
            return {}

        # 이름 검색
        if tool_name == "search_stock_by_name":
            return {"query": question}

        # 기본값
        return {}

    # === [REPLACE] 분석 단계 파라미터 보강 ===
    def _create_analysis_params(
        self, tool_name: str, data: Dict[str, Any], question: str
    ) -> Dict[str, Any]:
        """
        분석 단계 파라미터:
        - 재무/밸류/통계: symbol 우선
        - 기술/성과: stock_code
        - 데이터 기반 분석(analyze_data_trends): data_records 있을 때만 호출
        """
        inferred = self._infer_symbols(question)
        stock_code, symbol = inferred["stock_code"], inferred["symbol"]

        # 재무/밸류/통계
        if tool_name in {
            "get_financial_data",
            "calculate_financial_ratios",
            "perform_dcf_valuation",
        }:
            return {"symbol": symbol}

        if tool_name in {
            "calculate_statistical_indicators",
            "perform_pattern_recognition",
        }:
            return {"symbol": symbol}

        # 데이터 기반 추세 분석: data_records 필요 → 없으면 빈 dict(=스킵)
        if tool_name == "analyze_data_trends":
            series = self._extract_timeseries_from_collected(data)
            return {"symbol": symbol, "data_records": series} if series else {}

        # 기술/성과
        if tool_name == "analyze_stock_performance":
            return {"stock_code": stock_code, "period_days": 30}
        if tool_name == "get_technical_indicators":
            return {"stock_code": stock_code, "period_days": 60}

        # 밸류 계산
        if tool_name == "calculate_valuation_metrics":
            return {"stock_code": stock_code}

        # 뉴스 분석
        if tool_name in {"analyze_news_sentiment", "extract_stock_keywords"}:
            return {"query": question}

        return {}

    def _extract_insights_from_analysis(
        self, analysis_results: Dict[str, Any]
    ) -> List[str]:
        """분석 결과에서 간단한 인사이트 요약 추출"""
        insights: List[str] = []
        for tool_name, result in analysis_results.items():
            if isinstance(result, dict) and "error" in result:
                insights.append(f"{tool_name} 분석 실패: {result['error']}")
            elif isinstance(result, dict) and result.get("skipped"):
                insights.append(f"{tool_name} 호출 건너뜀: {result.get('reason')}")
            else:
                insights.append(f"{tool_name} 분석 완료")
        return insights

    # ===================== 여기서부터 추가 헬퍼 =====================

    # === [ADD] 질문에서 종목코드/티커 추론 (국내 6자리 or 영문 1~5자) ===
    def _infer_symbols(self, question: str) -> dict:
        """
        간단 추론 규칙:
        - 한국 6자리 숫자가 있으면 stock_code로 사용 (예: 005930)
        - 영문 대문자 1~5자 토큰이 있으면 symbol로 사용 (예: AAPL, TSLA)
        - 둘 다 없으면 기본값: 005930(삼성전자)로 채움
        """
        import re

        q = (question or "").upper()

        # 1) 한국식 6자리 종목코드
        m_code = re.search(r"\b\d{6}\b", q)
        stock_code = m_code.group(0) if m_code else "005930"  # 기본값

        # 2) 영문 티커(간단 검출: 1~5자 대문자)
        m_sym = re.search(r"\b[A-Z]{1,5}\b", q)
        symbol = m_sym.group(0) if m_sym else stock_code  # 없으면 코드로 대체

        return {"stock_code": stock_code, "symbol": symbol}

    # === [ADD] FDR 수집 결과에서 시계열을 꺼내 'data_records' 표준화 ===
    def _extract_timeseries_from_collected(
        self, collected: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        기대 포맷(예):
          collected["financedatareader"]["data"]["get_daily_chart"] -> {"rows": [...]} 또는 직접 list
        방어적으로 여러 케이스를 처리.
        """
        try:
            fdr = collected.get("financedatareader", {})
            data = fdr.get("data", {})
            chart = data.get("get_daily_chart") or data.get("get_minute_chart")
            if not chart:
                return []

            rows = chart.get(
                "rows", chart
            )  # dict에 rows가 있으면 rows, 없으면 리스트 가정
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "date": r.get("date") or r.get("timestamp"),
                        "open": r.get("open"),
                        "high": r.get("high"),
                        "low": r.get("low"),
                        "close": r.get("close"),
                        "volume": r.get("volume"),
                    }
                )
            # 날짜/종가 보유한 레코드만, 너무 길면 500개 컷
            return [x for x in out if x["date"] and x["close"] is not None][:500]
        except Exception:
            return []

    # === [ADD] 필수 파라미터 부족 시 호출 건너뛰기 ===
    async def _safe_invoke(self, tool, params: Dict[str, Any]) -> Any:
        """
        툴 이름 휴리스틱으로 필수 파라미터를 점검하고,
        비어 있으면 실패 대신 'skipped'로 처리하여 워크플로를 끊지 않음.
        """
        name = getattr(tool, "name", "")
        must = set()

        # 간단 휴리스틱(툴 이름으로 감지)
        if "stock" in name and (
            "info" in name
            or "chart" in name
            or "orderbook" in name
            or "execution" in name
        ):
            must.add("stock_code")
        if (
            "financial" in name
            or "valuation" in name
            or "statistical" in name
            or "pattern" in name
        ):
            must.add("symbol")
        if "news" in name or "search" in name:
            must.add("query")
        if "trends" in name and "analyze" in name:
            must.add("data_records")

        # 하나라도 빠졌으면 스킵
        if any(k not in params or params.get(k) in (None, "", []) for k in must):
            return {
                "skipped": True,
                "reason": f"missing required params {sorted(list(must))}",
            }

        # 정상 호출
        return await tool.ainvoke(params)
