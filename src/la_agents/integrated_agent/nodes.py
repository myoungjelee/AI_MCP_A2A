"""통합 에이전트 노드 구현 모듈"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from ..base.mcp_config import MCPServerConfig
from .state import IntegratedAgentState, add_error, add_warning, update_current_step
from .validation import InvestmentQuestionValidator, validate_investment_question


class IntegratedAgentNodes:
    """통합 에이전트 노드 구현 클래스"""

    def __init__(self, model_name: str = "gpt-oss:20b"):
        """초기화"""
        self.model_name = model_name
        # ChatOllama 공식 문서 기반 설정
        try:
            self.llm = ChatOllama(
                model=model_name,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0.7,
                timeout=30,  # 타임아웃 추가
            )
            print(
                f"ChatOllama 초기화 완료: {model_name} @ {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}"
            )
        except Exception as e:
            print(f"ChatOllama 초기화 실패: {e}")
            raise

        # 검증기 초기화
        self.validator = InvestmentQuestionValidator(model_name)

        # MCP 클라이언트 및 도구
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.mcp_tools_dict: Dict[str, Any] = {}

        # 서버별 실제 구현된 도구 매핑
        self.server_tools_map = {
            "macroeconomic": [
                "get_economic_indicators",
                "get_economic_calendar",
                "get_inflation_data",
                "get_gdp_data",
            ],
            "financial_analysis": [
                "analyze_financial_ratios",
                "calculate_valuation_metrics",
                "generate_financial_report",
            ],
            "stock_analysis": [
                "analyze_stock_performance",
                "get_technical_indicators",
                "calculate_risk_metrics",
            ],
            "naver_news": [
                "search_news_articles",
                "get_stock_news",
                "analyze_market_sentiment",
            ],
            "tavily_search": [
                "search_web",
                "get_company_info",
                "search_financial_news",
            ],
            "kiwoom": [
                "get_stock_price",
                "get_account_info",
                "get_stock_info",
                "get_market_status",
                "search_stock_by_name",
            ],
        }

    async def initialize_mcp_tools(self):
        """MCP 도구들 초기화 (안전한 버전)"""
        try:
            # 모든 서버 설정 가져오기
            server_configs = MCPServerConfig.get_standard_servers()
            print(f"서버 설정 로딩 완료: {list(server_configs.keys())}")
            print("✅ financial_analysis 서버 포트 수정 완료, 재포함")

            # MCP 클라이언트 생성
            self.mcp_client = MultiServerMCPClient(server_configs)
            print("MCP 클라이언트 생성 완료")

            # 도구 로딩 (타임아웃 설정)
            import asyncio

            try:
                tools = await asyncio.wait_for(
                    self.mcp_client.get_tools(), timeout=10.0
                )
                print(f"도구 로딩 완료: {len(tools)}개")
            except asyncio.TimeoutError:
                print("도구 로딩 타임아웃 - 일부 서버만 사용")
                # 타임아웃 시에도 기본 진행
                self.mcp_client = None
                return False

            # 도구를 이름으로 매핑
            for tool in tools:
                self.mcp_tools_dict[tool.name] = tool

            print(f"도구 매핑 완료: {list(self.mcp_tools_dict.keys())}")
            return True

        except Exception as e:
            print(f"MCP 도구 초기화 실패: {e}")
            print(f"에러 타입: {type(e).__name__}")
            # 초기화 실패해도 에이전트는 계속 동작하도록
            self.mcp_client = None
            return False

    async def validate_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        """투자 질문 검증 노드"""
        try:
            # 상태 업데이트
            new_state = update_current_step(state, "validate")

            # LLM 기반 검증 수행
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

    async def collect_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        """데이터 수집 노드"""
        try:
            # 투자 관련 질문이 아니면 건너뛰기
            if not state["is_investment_related"]:
                return state

            # 데이터 수집 단계로 전환
            new_state = update_current_step(state, "collect")

            # MCP 서버 선택 (질문 내용 기반)
            selected_servers = await self._select_mcp_servers_for_collection(
                state["question"]
            )
            new_state = update_current_step(new_state, "collect", selected_servers)

            # 각 선택된 서버에서 데이터 수집 (병렬 처리)
            # 모든 서버 동시 호출 태스크 생성
            collect_tasks = [
                self._collect_from_server(server, state["question"])
                for server in selected_servers
            ]

            # 병렬 실행 (에러 발생해도 다른 서버는 계속 진행)
            results = await asyncio.gather(*collect_tasks, return_exceptions=True)

            # 결과 처리
            collected_data = {}
            for server, result in zip(selected_servers, results, strict=False):
                if isinstance(result, Exception):
                    new_state = add_warning(
                        new_state, f"{server} 서버에서 데이터 수집 실패: {str(result)}"
                    )
                    collected_data[server] = {"error": str(result), "status": "failed"}
                else:
                    collected_data[server] = result

            # 수집된 데이터 저장
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

    async def analyze_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        """데이터 분석 노드"""
        try:
            # 투자 관련 질문이 아니면 건너뛰기
            if not state["is_investment_related"]:
                return state

            # 분석 단계로 전환
            new_state = update_current_step(state, "analyze")

            # 분석에 필요한 MCP 서버 선택
            analysis_servers = await self._select_mcp_servers_for_analysis(
                state["question"]
            )
            new_state = update_current_step(new_state, "analyze", analysis_servers)

            # 수집된 데이터 분석 (병렬 처리)
            collected_data = state["collected_data"]

            # 모든 분석 서버 동시 호출 태스크 생성
            analysis_tasks = [
                self._analyze_with_server(server, collected_data, state["question"])
                for server in analysis_servers
            ]

            # 병렬 분석 실행
            analysis_results_list = await asyncio.gather(
                *analysis_tasks, return_exceptions=True
            )

            # 분석 결과 처리
            analysis_results = {}
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

            # 분석 결과 통합
            integrated_analysis = await self._integrate_analysis_results(
                analysis_results, state["question"]
            )

            new_state["analysis_result"] = integrated_analysis
            new_state["analysis_confidence"] = integrated_analysis.get(
                "confidence", 0.7
            )
            new_state["key_insights"] = integrated_analysis.get("insights", [])

            return new_state

        except Exception as e:
            return add_error(state, f"데이터 분석 중 오류: {str(e)}", "ANALYSIS_ERROR")

    async def decide_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        """의사결정 노드"""
        try:
            # 투자 관련 질문이 아니면 건너뛰기
            if not state["is_investment_related"]:
                return state

            # 의사결정 단계로 전환
            new_state = update_current_step(state, "decide")

            # 의사결정에 필요한 서버 (주로 financial_analysis)
            decision_servers = ["financial_analysis"]
            new_state = update_current_step(new_state, "decide", decision_servers)

            # 분석 결과를 바탕으로 의사결정
            analysis_result = state["analysis_result"]
            collected_data = state["collected_data"]

            # LLM을 사용한 의사결정
            decision_prompt = self._create_decision_prompt(
                state["question"], analysis_result, collected_data
            )

            decision_response = await self.llm.ainvoke(
                [
                    SystemMessage(
                        content="당신은 투자 의사결정 전문가입니다. 데이터와 분석을 바탕으로 명확한 결론을 제시하세요."
                    ),
                    HumanMessage(content=decision_prompt),
                ]
            )

            # 의사결정 결과 저장
            new_state["analysis_result"]["decision"] = decision_response.content

            return new_state

        except Exception as e:
            return add_error(state, f"의사결정 중 오류: {str(e)}", "DECISION_ERROR")

    async def respond_node(self, state: IntegratedAgentState) -> IntegratedAgentState:
        """응답 생성 노드"""
        try:
            # 투자 관련 질문이 아니면 이미 거부 응답이 설정됨
            if not state["is_investment_related"]:
                return state

            # 응답 생성 단계로 전환
            new_state = update_current_step(state, "respond")

            # 최종 응답 생성
            final_response = await self._generate_final_response(
                state["question"],
                state["analysis_result"],
                state["collected_data"],
                state["key_insights"],
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

    # === 헬퍼 메서드들 ===

    async def _select_mcp_servers_for_collection(self, question: str) -> List[str]:
        """데이터 수집을 위한 MCP 서버 선택"""
        # 질문 내용 기반 서버 선택 로직
        selected = []

        question_lower = question.lower()

        # 경제 지표 관련
        if any(
            word in question_lower for word in ["경제", "gdp", "인플레이션", "금리"]
        ):
            selected.append("macroeconomic")

        # 주식 관련
        if any(word in question_lower for word in ["주식", "종목", "차트", "기술분석"]):
            selected.extend(["stock_analysis", "kiwoom"])

        # 뉴스 관련
        if any(word in question_lower for word in ["뉴스", "이슈", "동향"]):
            selected.append("naver_news")

        # 검색 관련
        if any(word in question_lower for word in ["정보", "조사", "연구"]):
            selected.append("tavily_search")

        # 기본적으로 최소 2개 서버 선택
        if not selected:
            selected = ["macroeconomic", "tavily_search"]

        return list(set(selected))  # 중복 제거

    async def _select_mcp_servers_for_analysis(self, question: str) -> List[str]:
        """데이터 분석을 위한 MCP 서버 선택"""
        # 분석에는 주로 financial_analysis와 stock_analysis 사용
        return ["financial_analysis", "stock_analysis"]

    async def _collect_from_server(self, server: str, question: str) -> Dict[str, Any]:
        """특정 서버에서 데이터 수집"""
        try:
            # MCP 클라이언트가 초기화되지 않았으면 초기화
            if not self.mcp_client:
                await self.initialize_mcp_tools()

            # 서버별 적절한 도구 선택
            tools_to_use = self._select_tools_for_server(server, question)

            # 도구 병렬 실행
            available_tools = [
                tool for tool in tools_to_use if tool in self.mcp_tools_dict
            ]

            if available_tools:
                # 모든 도구 동시 실행 태스크 생성
                tool_tasks = []
                for tool_name in available_tools:
                    tool_params = self._create_tool_params(tool_name, question)
                    task = self.mcp_tools_dict[tool_name].ainvoke(tool_params)
                    tool_tasks.append((tool_name, task))

                # 병렬 실행
                tool_results = await asyncio.gather(
                    *[task for _, task in tool_tasks], return_exceptions=True
                )

                # 결과 처리
                collected_data = {}
                for (tool_name, _), result in zip(
                    tool_tasks, tool_results, strict=False
                ):
                    if isinstance(result, Exception):
                        print(f"도구 {tool_name} 실행 실패: {result}")
                        collected_data[tool_name] = {"error": str(result)}
                    else:
                        collected_data[tool_name] = result
            else:
                collected_data = {}

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
        """특정 서버로 데이터 분석"""
        try:
            # MCP 클라이언트가 초기화되지 않았으면 초기화
            if not self.mcp_client:
                await self.initialize_mcp_tools()

            # 분석용 도구 선택
            analysis_tools = self._select_analysis_tools_for_server(server, question)

            analysis_results = {}
            for tool_name in analysis_tools:
                if tool_name in self.mcp_tools_dict:
                    try:
                        # 분석 도구 실행
                        tool_params = self._create_analysis_params(
                            tool_name, data, question
                        )
                        result = await self.mcp_tools_dict[tool_name].ainvoke(
                            tool_params
                        )
                        analysis_results[tool_name] = result

                    except Exception as e:
                        print(f"분석 도구 {tool_name} 실행 실패: {e}")
                        analysis_results[tool_name] = {"error": str(e)}

            return {
                "server": server,
                "analysis": analysis_results,
                "confidence": 0.8,
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
        """분석 결과 통합"""
        all_insights = []
        total_confidence = 0.0
        count = 0

        for result in results.values():
            if "insights" in result:
                all_insights.extend(result["insights"])
            if "confidence" in result:
                total_confidence += result["confidence"]
                count += 1

        avg_confidence = total_confidence / count if count > 0 else 0.5

        return {
            "question": question,
            "integrated_insights": all_insights,
            "confidence": avg_confidence,
            "server_results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """데이터 품질 점수 계산"""
        if not data:
            return 0.0

        # 성공적으로 수집된 서버 수를 기반으로 품질 점수 계산
        successful_servers = sum(
            1 for server_data in data.values() if server_data.get("status") == "success"
        )
        total_servers = len(data)

        return successful_servers / total_servers if total_servers > 0 else 0.0

    def _create_decision_prompt(
        self, question: str, analysis: Dict[str, Any], data: Dict[str, Any]
    ) -> str:
        """의사결정 프롬프트 생성"""
        return f"""
**질문**: {question}

**분석 결과**:
- 신뢰도: {analysis.get('confidence', 0)}
- 핵심 인사이트: {analysis.get('integrated_insights', [])}

**수집된 데이터**:
{data}

위 정보를 종합하여 명확한 투자 의사결정 및 권고사항을 제시해주세요.
"""

    async def _generate_final_response(
        self,
        question: str,
        analysis: Dict[str, Any],
        data: Dict[str, Any],
        insights: List[str],
    ) -> str:
        """최종 마크다운 응답 생성"""

        response_prompt = f"""
사용자 질문: {question}

분석 결과와 데이터를 바탕으로 전문적인 투자 분석 보고서를 마크다운 형식으로 작성해주세요.

**포함할 내용**:
1. 📊 **핵심 요약**
2. 📈 **상세 분석**
3. 💡 **주요 인사이트**
4. ⚠️ **리스크 요인**
5. 🎯 **투자 권고**

**분석 데이터**: {analysis}
**수집 데이터**: {data}
**핵심 인사이트**: {insights}

전문적이고 구체적인 분석을 제공하되, 이해하기 쉽게 작성해주세요.
"""

        # ChatOllama 공식 문서 기반 호출 패턴
        try:
            print(f"LLM 호출 시작: model={self.model_name}")

            # 메시지 구성 (대화 히스토리 포함)
            messages = [
                SystemMessage(
                    content="당신은 전문 투자 분석가입니다. 마크다운 형식으로 체계적이고 이해하기 쉬운 투자 분석 보고서를 작성하세요. 이전 대화 맥락을 고려하여 자연스럽게 답변하세요."
                ),
            ]

            # 이전 대화 히스토리 추가
            conversation_history = state.get("conversation_history", [])
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(SystemMessage(content=msg["content"]))

            # 현재 질문 추가
            messages.append(HumanMessage(content=response_prompt))

            # ainvoke 호출 (공식 문서 패턴)
            response = await self.llm.ainvoke(messages)

            print(f"LLM 호출 성공: {len(response.content)} 문자")

            # 대화 히스토리에 현재 대화 추가
            response_content = response.content
            state["conversation_history"].append(
                {"role": "user", "content": state["question"]}
            )
            state["conversation_history"].append(
                {"role": "assistant", "content": response_content}
            )

            return response_content

        except Exception as e:
            print(f"LLM 호출 실패: {type(e).__name__}: {e}")
            # 연결 문제인지 확인
            if "connect" in str(e).lower() or "timeout" in str(e).lower():
                print(
                    f"Ollama 연결 문제 감지. BASE_URL: {os.getenv('OLLAMA_BASE_URL')}"
                )
            import traceback

            print(f"Full traceback: {traceback.format_exc()}")
            raise

    def _select_tools_for_server(self, server: str, question: str) -> List[str]:
        """서버별 적절한 도구 선택"""
        available_tools = self.server_tools_map.get(server, [])

        # 질문 내용에 따라 적절한 도구 선택
        selected_tools = []
        question_lower = question.lower()

        if server == "macroeconomic":
            if any(word in question_lower for word in ["경제", "gdp", "성장률"]):
                selected_tools.append("get_gdp_data")
            if any(word in question_lower for word in ["인플레이션", "물가"]):
                selected_tools.append("get_inflation_data")
            if any(word in question_lower for word in ["지표", "경제지표"]):
                selected_tools.append("get_economic_indicators")
            if not selected_tools:
                selected_tools = ["get_economic_indicators"]

        elif server == "kiwoom":
            if any(word in question_lower for word in ["주식", "종목", "가격"]):
                selected_tools.extend(["get_stock_price", "get_stock_info"])
            if any(word in question_lower for word in ["시장", "상태"]):
                selected_tools.append("get_market_status")
            if not selected_tools:
                selected_tools = ["get_market_status"]

        elif server == "naver_news":
            selected_tools = ["search_news_articles"]

        elif server == "tavily_search":
            selected_tools = ["search_web"]

        elif server == "financial_analysis":
            selected_tools = ["analyze_financial_ratios"]

        elif server == "stock_analysis":
            selected_tools = ["analyze_stock_performance"]

        # 사용 가능한 도구만 반환
        return [tool for tool in selected_tools if tool in available_tools]

    def _create_tool_params(self, tool_name: str, question: str) -> Dict[str, Any]:
        """도구별 파라미터 생성"""
        if tool_name in ["search_news_articles", "search_web"]:
            return {"query": question}
        elif tool_name == "get_stock_price":
            # 질문에서 종목코드 추출 (간단한 예시)
            return {"stock_code": "005930"}  # 삼성전자 기본값
        elif tool_name == "get_stock_info":
            return {"stock_code": "005930"}
        else:
            return {}

    def _select_analysis_tools_for_server(
        self, server: str, question: str
    ) -> List[str]:
        """분석용 도구 선택"""
        available_tools = self.server_tools_map.get(server, [])

        if server == "financial_analysis":
            return ["analyze_financial_ratios", "calculate_valuation_metrics"]
        elif server == "stock_analysis":
            return ["analyze_stock_performance", "get_technical_indicators"]
        else:
            return available_tools[:1]  # 첫 번째 도구만 사용

    def _create_analysis_params(
        self, tool_name: str, data: Dict[str, Any], question: str
    ) -> Dict[str, Any]:
        """분석 도구 파라미터 생성"""
        if tool_name == "analyze_financial_ratios":
            return {"company_code": "005930", "period": "quarterly"}
        elif tool_name == "analyze_stock_performance":
            return {"stock_code": "005930", "period_days": 30}
        elif tool_name == "calculate_valuation_metrics":
            return {"stock_code": "005930"}
        else:
            return {}

    def _extract_insights_from_analysis(
        self, analysis_results: Dict[str, Any]
    ) -> List[str]:
        """분석 결과에서 인사이트 추출"""
        insights = []
        for tool_name, result in analysis_results.items():
            if isinstance(result, dict) and "error" not in result:
                insights.append(f"{tool_name} 분석 완료")
            elif isinstance(result, dict) and "error" in result:
                insights.append(f"{tool_name} 분석 실패: {result['error']}")
        return insights
