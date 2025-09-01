"""
통합 에이전트 HTTP 서버

LangGraph 에이전트를 HTTP API로 제공하는 서버입니다.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import IntegratedAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global agent

    # 시작 시 초기화
    try:
        logger.info("통합 에이전트 초기화 시작")

        # 환경 변수에서 MCP 서버 목록 가져오기
        mcp_servers = os.getenv("MCP_SERVERS", "").split(",")
        if mcp_servers == [""]:
            mcp_servers = [
                "macroeconomic",
                "financial_analysis",
                "stock_analysis",
                "naver_news",
                "tavily_search",
                "kiwoom",
            ]

        # 에이전트 초기화
        agent = IntegratedAgent(
            name="integrated_agent",
            mcp_servers=mcp_servers,
            config={
                "max_retries": 3,
                "timeout": 30,
                "enable_metrics": True,
            },
            llm_model=os.getenv("LLM_MODEL", "gpt-oss:20b"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

        logger.info(f"통합 에이전트 초기화 완료: {agent.name}")
        logger.info(f"MCP 서버 목록: {mcp_servers}")

    except Exception as e:
        logger.error(f"에이전트 초기화 실패: {e}")
        raise

    yield

    # 종료 시 정리
    if agent:
        try:
            await agent._disconnect_mcp_servers()
            logger.info("에이전트 정리 완료")
        except Exception as e:
            logger.error(f"에이전트 정리 실패: {e}")


# FastAPI 앱 생성 (lifespan 사용)
app = FastAPI(
    title="AI MCP A2A - 통합 에이전트 API",
    description="LangGraph 기반 통합 에이전트 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 에이전트 인스턴스
agent: IntegratedAgent = None
SESSIONS: Dict[str, List[Dict[str, str]]] = {}


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""

    request: Dict[str, Any]
    task_type: str = "comprehensive_analysis"


class ChatRequest(BaseModel):
    """대화형 요청 모델"""

    message: str
    session_id: Optional[str] = None
    task_type: str = "comprehensive_analysis"


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""

    status: str
    agent_name: str
    workflow_ready: bool
    mcp_servers: Dict[str, str]
    timestamp: float


# on_event 핸들러들이 lifespan으로 이동됨


@app.get("/", response_model=Dict[str, Any])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "AI MCP A2A - 통합 에이전트 API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        health = await agent.health_check()
        return HealthResponse(**health)
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/info", response_model=Dict[str, Any])
async def get_agent_info():
    """에이전트 정보 조회"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    return agent.get_agent_info()


@app.get("/stats", response_model=Dict[str, Any])
async def get_performance_stats():
    """성능 통계 조회"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        stats = await agent.get_performance_stats()
        return stats
    except Exception as e:
        logger.error(f"성능 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def _format_chat_reply(result: Dict[str, Any]) -> str:
    """결과를 간결한 대화 응답으로 포맷"""
    if not result.get("success"):
        return f"❌ 분석 실패: {result.get('error', 'Unknown error')}"

    # 결과 구조 전체 디버깅
    logger.info("🔍 결과 구조 전체 분석:")
    logger.info(f"  - 최상위 키들: {list(result.keys())}")
    if "result" in result:
        logger.info(f"  - result 내부: {type(result['result'])}")
        if isinstance(result["result"], dict):
            logger.info(f"  - result 키들: {list(result['result'].keys())}")

    # 먼저 AI 응답이 있는지 확인 - 여러 경로 시도
    ai_response = None

    # 경로 1: result.result.ai_response
    if (
        result.get("result")
        and isinstance(result["result"], dict)
        and result["result"].get("ai_response")
    ):
        logger.info("🎯 AI 응답 발견: 경로 1 (result.result.ai_response)")
        ai_response = result["result"]["ai_response"]
    # 경로 2: result.ai_response
    elif result.get("ai_response"):
        logger.info("🎯 AI 응답 발견: 경로 2 (result.ai_response)")
        ai_response = result["ai_response"]
    # 경로 3: result 안에서 더 깊이 검색
    else:
        logger.info("❌ AI 응답을 찾을 수 없음")
        # result 전체를 문자열로 변환해서 ai_response 포함 여부 확인
        result_str = str(result)
        if "ai_response" in result_str:
            logger.info("📝 결과 문자열에 'ai_response' 포함됨")
            # result 딕셔너리 안에서 직접 찾기
            if "result" in result and isinstance(result["result"], dict):
                # state가 result에 포함되어 있을 수 있음
                ai_response = result["result"].get("ai_response")
                if ai_response:
                    logger.info("🎯 AI 응답 발견: 경로 3 (깊은 검색)")
                    return (
                        ai_response.strip()
                        if isinstance(ai_response, str)
                        and len(ai_response.strip()) > 10
                        else None
                    )

    if ai_response and isinstance(ai_response, str) and len(ai_response.strip()) > 10:
        logger.info(f"✅ AI 응답 반환: {len(ai_response)} 문자")
        return ai_response.strip()
    else:
        logger.info("⚠️ AI 응답이 유효하지 않음 - 기본 포맷 사용")

    # AI 응답이 없으면 기존 요약 방식 사용
    summary = result.get("summary", {})
    if not summary:
        return "분석을 완료했지만 요약 정보를 생성하지 못했어요."

    progress = int(round(summary.get("progress", 0) * 100))
    decided = summary.get("decision_made", False)
    confidence = summary.get("confidence", 0)
    data_sources = summary.get("data_sources_count", 0)
    analyses = summary.get("analysis_results_count", 0)
    insights = summary.get("insights_count", 0)

    header = "✅ 분석 완료" if decided else "⏳ 분석 진행 결과"
    body = (
        f"진행률 {progress}% • 신뢰도 {confidence}%\n"
        f"데이터 {data_sources} • 분석 {analyses} • 인사이트 {insights}"
    )
    tail = "→ 더 궁금한 점이 있으면 이어서 물어보세요!"
    return f"{header}\n{body}\n{tail}"


@app.post("/analyze", response_model=Dict[str, Any])
async def run_analysis(request: AnalysisRequest):
    """종합 분석 실행"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        logger.info(f"분석 요청 수신: {request.task_type}")

        result = await agent.run_comprehensive_analysis(
            request=request.request, task_type=request.task_type
        )

        logger.info(f"분석 완료: {result.get('success', False)}")
        return result

    except Exception as e:
        logger.error(f"분석 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/chat", response_model=Dict[str, Any])
async def chat(request: ChatRequest):
    """대화형 질의/응답(간단 세션 메모리 포함)"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message는 필수입니다")

    # 세션 준비
    session_id = request.session_id or str(uuid4())
    history = SESSIONS.setdefault(session_id, [])

    # 사용자 메시지 저장
    history.append({"role": "user", "content": request.message.strip()})

    try:
        # 에이전트 실행 - 질문 전체를 전달
        result = await agent.run_comprehensive_analysis(
            request={
                "question": request.message.strip(),
                "history": history,
                "include_news": True,
                "include_sentiment": True,
            },
            task_type=request.task_type,
        )

        reply_text = _format_chat_reply(result)
        history.append({"role": "assistant", "content": reply_text})

        return {
            "success": True,
            "session_id": session_id,
            "message": reply_text,
            "summary": result.get("summary"),
        }

    except Exception as e:
        err = f"대화 처리 실패: {e}"
        history.append({"role": "assistant", "content": f"❌ {err}"})
        raise HTTPException(status_code=500, detail=err) from e


@app.get("/chat/{session_id}", response_model=Dict[str, Any])
async def get_chat_history(session_id: str):
    """세션 히스토리 조회"""
    if session_id not in SESSIONS:
        return {"session_id": session_id, "messages": []}
    return {"session_id": session_id, "messages": SESSIONS[session_id]}


@app.post("/collect", response_model=Dict[str, Any])
async def run_data_collection(request: AnalysisRequest):
    """데이터 수집만 실행"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        logger.info("데이터 수집 요청 수신")

        result = await agent.run_data_collection(request=request.request)

        logger.info(f"데이터 수집 완료: {result.get('success', False)}")
        return result

    except Exception as e:
        logger.error(f"데이터 수집 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/analyze-market", response_model=Dict[str, Any])
async def run_market_analysis(request: AnalysisRequest):
    """시장 분석만 실행"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        logger.info("시장 분석 요청 수신")

        result = await agent.run_market_analysis(request=request.request)

        logger.info(f"시장 분석 완료: {result.get('success', False)}")
        return result

    except Exception as e:
        logger.error(f"시장 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/decide", response_model=Dict[str, Any])
async def run_investment_decision(request: AnalysisRequest):
    """투자 의사결정만 실행"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        logger.info("투자 의사결정 요청 수신")

        result = await agent.run_investment_decision(request=request.request)

        logger.info(f"투자 의사결정 완료: {result.get('success', False)}")
        return result

    except Exception as e:
        logger.error(f"투자 의사결정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/execute", response_model=Dict[str, Any])
async def run_trading_execution(request: AnalysisRequest):
    """거래 실행만 실행"""
    if not agent:
        raise HTTPException(status_code=503, detail="에이전트가 초기화되지 않았습니다")

    try:
        logger.info("거래 실행 요청 수신")

        result = await agent.run_trading_execution(request=request.request)

        logger.info(f"거래 실행 완료: {result.get('success', False)}")
        return result

    except Exception as e:
        logger.error(f"거래 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    # 환경 변수에서 포트 가져오기
    port = int(os.getenv("AGENT_PORT", 8000))
    host = os.getenv("AGENT_HOST", "0.0.0.0")

    logger.info(f"통합 에이전트 서버 시작: {host}:{port}")

    uvicorn.run(
        "src.la_agents.integrated_agent.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )
