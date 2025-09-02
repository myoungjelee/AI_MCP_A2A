"""투자 질문 검증 모듈 - LLM 기반 의미 분석"""

import os
from typing import Tuple

from langchain_ollama import ChatOllama

from .state import IntegratedAgentState


class InvestmentQuestionValidator:
    """투자 질문 검증기 - LLM 기반 의미 분석"""

    def __init__(self, model_name: str = "gpt-oss:20b"):
        """초기화"""
        self.model_name = model_name
        self.llm = ChatOllama(
            model=model_name,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.1,  # 일관된 검증을 위해 낮은 온도
        )

        # 시스템 프롬프트 - 투자 관련 질문 검증용
        self.system_prompt = """당신은 투자 및 금융 질문을 분석하는 전문가입니다.

**역할**: 사용자의 질문이 투자, 금융, 주식, 경제와 관련된 질문인지 판단하세요.

**판단 기준**:
✅ **투자 관련 질문 (승인)**:
- 주식, 채권, 펀드, ETF 등 금융상품 관련
- 기업 분석, 재무제표, 투자 전략
- 경제 지표, 시장 동향, 경제 뉴스
- 포트폴리오 관리, 리스크 관리
- 투자 조언, 매매 타이밍, 가격 예측
- 거시경제, 금리, 환율, 인플레이션
- 업종별 분석, 기업 실적, 배당

❌ **투자 무관 질문 (거부)**:
- 일반 대화, 안부 인사
- 기술, 과학, 의학, 요리 등 비금융 분야
- 개인적인 상담, 생활 조언
- 학습, 교육 (금융 교육 제외)
- 엔터테인먼트, 스포츠, 문화
- 프로그래밍, 개발 (핀테크 제외)

**응답 형식**:
```json
{
    "is_investment_related": true/false,
    "confidence": 0.0~1.0,
    "reasoning": "판단 근거 설명"
}
```

**중요**: 키워드가 아닌 질문의 의미와 맥락을 종합적으로 분석하여 판단하세요."""

    async def validate_question(self, question: str) -> Tuple[bool, float, str]:
        """
        투자 관련 질문 검증

        Args:
            question: 사용자 질문

        Returns:
            Tuple[bool, float, str]: (투자관련여부, 신뢰도, 판단근거)
        """
        try:
            # LLM에게 질문 분석 요청
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"질문: {question}"},
            ]

            response = await self.llm.ainvoke(messages)
            result_text = response.content

            # JSON 파싱 시도
            import json

            try:
                # JSON 추출 (```json 블록에서)
                if "```json" in result_text:
                    start = result_text.find("```json") + 7
                    end = result_text.find("```", start)
                    json_text = result_text[start:end].strip()
                else:
                    json_text = result_text.strip()

                result = json.loads(json_text)

                is_related = result.get("is_investment_related", False)
                confidence = float(result.get("confidence", 0.0))
                reasoning = result.get("reasoning", "")

                # 신뢰도 검증 (0.0~1.0 범위)
                confidence = max(0.0, min(1.0, confidence))

                return is_related, confidence, reasoning

            except (json.JSONDecodeError, KeyError, ValueError):
                # JSON 파싱 실패 시 텍스트 분석으로 폴백
                return self._fallback_analysis(result_text, question)

        except Exception as e:
            # LLM 호출 실패 시 기본 키워드 기반 판단으로 폴백
            print(f"LLM 연결 실패, 키워드 기반 폴백 적용: {e}")
            return self._keyword_fallback_analysis(question)

    def _fallback_analysis(
        self, response_text: str, question: str
    ) -> Tuple[bool, float, str]:
        """LLM 응답이 JSON이 아닐 때 폴백 분석"""
        response_lower = response_text.lower()

        # 긍정적 키워드들
        positive_indicators = [
            "투자",
            "관련",
            "yes",
            "true",
            "승인",
            "금융",
            "주식",
            "경제",
        ]

        # 부정적 키워드들
        negative_indicators = [
            "무관",
            "관련없",
            "no",
            "false",
            "거부",
            "아니",
            "비금융",
        ]

        positive_count = sum(
            1 for indicator in positive_indicators if indicator in response_lower
        )
        negative_count = sum(
            1 for indicator in negative_indicators if indicator in response_lower
        )

        if positive_count > negative_count:
            return (
                True,
                0.6,
                f"LLM 응답에서 투자 관련 키워드 감지: {response_text[:100]}",
            )
        else:
            return False, 0.6, f"LLM 응답에서 투자 무관 판단: {response_text[:100]}"

    def _keyword_fallback_analysis(self, question: str) -> Tuple[bool, float, str]:
        """LLM 실패 시 키워드 기반 폴백 분석"""
        question_lower = question.lower()

        # 투자 관련 핵심 키워드들
        investment_keywords = [
            # 주식 관련
            "주식",
            "stock",
            "주가",
            "상장",
            "종목",
            "삼성전자",
            "애플",
            "테슬라",
            # 투자 관련
            "투자",
            "invest",
            "매수",
            "매도",
            "수익",
            "손실",
            "포트폴리오",
            # 금융상품
            "펀드",
            "etf",
            "채권",
            "bond",
            "코인",
            "비트코인",
            "암호화폐",
            # 경제/금융
            "경제",
            "금리",
            "인플레이션",
            "gdp",
            "환율",
            "달러",
            "원화",
            # 기업/분석
            "기업분석",
            "재무제표",
            "실적",
            "배당",
            "eps",
            "per",
            "pbr",
            # 시장
            "코스피",
            "나스닥",
            "증시",
            "시장",
            "거래소",
            "상승",
            "하락",
        ]

        # 키워드 매칭 점수 계산
        matched_keywords = [kw for kw in investment_keywords if kw in question_lower]

        if matched_keywords:
            confidence = min(0.8, 0.3 + len(matched_keywords) * 0.1)
            return (
                True,
                confidence,
                f"투자 관련 키워드 감지 (폴백): {matched_keywords[:3]}",
            )
        else:
            return False, 0.7, "투자 관련 키워드 없음 (폴백 분석)"


async def validate_investment_question(
    state: IntegratedAgentState, validator: InvestmentQuestionValidator = None
) -> IntegratedAgentState:
    """
    상태를 사용한 투자 질문 검증

    Args:
        state: 현재 상태
        validator: 검증기 인스턴스 (선택사항)

    Returns:
        IntegratedAgentState: 검증 결과가 반영된 상태
    """
    if validator is None:
        validator = InvestmentQuestionValidator()

    question = state["question"]

    # 검증 수행
    is_related, confidence, reasoning = await validator.validate_question(question)

    # 상태 업데이트
    new_state = state.copy()
    new_state["is_investment_related"] = is_related
    new_state["validation_confidence"] = confidence
    new_state["validation_reasoning"] = reasoning

    # 비투자 질문인 경우 거부 응답 설정
    if not is_related:
        new_state[
            "final_response"
        ] = """## 📋 질문 범위 안내

죄송합니다. 저는 **투자 및 금융 분야 전문 AI 분석가**입니다.

### 🔍 제가 도움드릴 수 있는 분야:
- 📈 **주식, 채권, 펀드** 등 금융상품 분석
- 🏢 **기업 분석** 및 재무제표 검토
- 📊 **경제 지표** 및 시장 동향 분석
- 💼 **포트폴리오 관리** 및 투자 전략
- 🌍 **거시경제** 동향 및 정책 영향

### 💡 투자 관련 질문 예시:
- "삼성전자 주식 분석해주세요"
- "현재 금리 인상이 주식시장에 미치는 영향은?"
- "반도체 업종 전망이 어떤가요?"

**투자나 금융과 관련된 질문을 다시 해주시면 성심껏 도와드리겠습니다!** 🚀"""
        new_state["response_type"] = "rejection"

    return new_state
