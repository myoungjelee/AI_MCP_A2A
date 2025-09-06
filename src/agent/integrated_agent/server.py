"""통합 에이전트 FastAPI 서버"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent import IntegratedAgent

# === 요청/응답 모델 ===


class AnalyzeRequest(BaseModel):
    """분석 요청 모델"""

    question: str
    session_id: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """분석 응답 모델"""

    success: bool
    response: str
    response_type: str
    is_investment_related: bool
    validation_confidence: float
    processing_time: Optional[float] = None
    used_servers: list = []
    step_usage: dict = {}
    session_id: str
    error: Optional[str] = None


# === FastAPI 앱 초기화 ===

app = FastAPI(
    title="통합 투자 분석 에이전트",
    description="LangGraph 기반 투자 질문 분석 및 의사결정 시스템",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # 로컬 개발 프론트엔드
        "https://ai-mcp-a2a.vercel.app",  # Vercel 배포 도메인
        "https://*.ngrok.io",  # TODO: eu.org 도메인 나오면 Cloudflare Tunnel로 전환
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 전역 에이전트 인스턴스
_AGENT: Optional[IntegratedAgent] = None


async def get_agent() -> IntegratedAgent:
    """에이전트 인스턴스 반환 (지연 초기화)"""
    global _AGENT
    if _AGENT is None:
        _AGENT = IntegratedAgent()
    return _AGENT


# === API 엔드포인트 ===


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "통합 투자 분석 에이전트 API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze",
            "stream": "/analyze/stream",
            "health": "/health",
            "mcp_status": "/mcp/status",
            "mcp_servers": "/mcp/servers",
            "validate": "/validate/investment/json",
        },
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    agent = await get_agent()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "available_servers": agent.get_available_mcp_servers(),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_question(request: AnalyzeRequest):
    """투자 질문 분석 (동기 방식)"""
    try:
        agent = await get_agent()

        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())

        # 질문 처리
        result = await agent.process_question(request.question, session_id)

        return AnalyzeResponse(
            success=result["success"],
            response=result["response"],
            response_type=result["response_type"],
            is_investment_related=result.get("is_investment_related", False),
            validation_confidence=result.get("validation_confidence", 0.0),
            processing_time=result.get("processing_time"),
            used_servers=result.get("used_servers", []),
            step_usage=result.get("step_usage", {}),
            session_id=session_id,
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/analyze/stream")
async def stream_analyze_question(request: AnalyzeRequest):
    """투자 질문 분석 (스트리밍 방식)"""
    try:
        agent = await get_agent()

        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())

        async def event_stream():
            """서버-센트 이벤트 스트림"""
            try:
                # 시작 이벤트
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'question': request.question})}\n\n"

                # 에이전트 스트리밍 처리
                async for update in agent.stream_process_question(
                    request.question, session_id
                ):
                    event_data = {
                        **update,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                    # 짧은 지연으로 프론트엔드가 이벤트를 처리할 시간 제공
                    await asyncio.sleep(0.1)

                # 완료 이벤트
                yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id})}\n\n"

            except Exception as e:
                # 에러 이벤트
                error_data = {
                    "type": "error",
                    "error": str(e),
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # nginx 버퍼링 비활성화
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/validate/investment/json")
async def validate_investment_question(request: dict):
    """투자 질문 검증 (프론트엔드용)"""
    try:
        question = request.get("question", "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="질문을 입력해주세요")

        # 기존 검증 로직 활용
        from .validation import InvestmentQuestionValidator

        validator = InvestmentQuestionValidator()

        is_related, confidence, reasoning = await validator.validate_question(question)

        return {
            "success": True,
            "is_investment_related": is_related,
            "confidence": confidence,
            "reasoning": reasoning,
            "message": "투자 관련 질문" if is_related else "투자 무관 질문",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검증 오류: {str(e)}") from e


@app.get("/mcp/status")
async def get_mcp_status():
    """MCP 서버 상태 조회 (프론트엔드용)"""
    try:
        agent = await get_agent()
        available_servers = agent.get_available_mcp_servers()

        # MCP 서버 연결 상태 확인
        mcp_servers = {}
        connected_servers = []
        disconnected_servers = []
        total_tools = 0

        for server in available_servers:
            try:
                tools = agent.get_mcp_server_tools(server)
                if tools:
                    mcp_servers[server] = "connected"
                    connected_servers.append(server)
                    total_tools += len(tools)
                else:
                    mcp_servers[server] = "disconnected"
                    disconnected_servers.append(server)
            except Exception:
                mcp_servers[server] = "disconnected"
                disconnected_servers.append(server)

        return {
            "mcp_servers": mcp_servers,
            "connected_count": len(connected_servers),
            "total_count": len(available_servers),
            "connected_servers": connected_servers,
            "disconnected_servers": disconnected_servers,
            "available_tools": total_tools,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/mcp/servers")
async def get_mcp_servers():
    """사용 가능한 MCP 서버 목록 조회"""
    try:
        agent = await get_agent()
        servers = agent.get_available_mcp_servers()

        server_details = {}
        for server in servers:
            tools = agent.get_mcp_server_tools(server)
            server_details[server] = {
                "name": server,
                "tools": tools,
                "tool_count": len(tools) if tools else 0,
            }

        return {"servers": servers, "count": len(servers), "details": server_details}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """세션 대화 기록 조회 (LangGraph 표준)"""
    try:
        agent = await get_agent()
        history = agent.get_conversation_history(session_id)

        if history.get("exists"):
            return {
                "success": True,
                "session_id": session_id,
                "messages": history.get("messages", []),
                "message_count": len(history.get("messages", [])),
            }
        else:
            return {
                "success": False,
                "session_id": session_id,
                "message": "대화 기록이 없습니다.",
                "messages": [],
                "message_count": 0,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/session/{session_id}/history")
async def clear_session_history(session_id: str):
    """세션 대화 기록 삭제 (LangGraph 표준)"""
    try:
        agent = await get_agent()
        success = agent.clear_conversation_history(session_id)

        return {
            "success": success,
            "session_id": session_id,
            "message": "대화 기록이 삭제되었습니다." if success else "삭제 실패",
            "note": "LangGraph MemorySaver는 자동으로 메모리를 관리합니다.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# === 개발 전용 엔드포인트 ===


@app.get("/debug/state/{session_id}")
async def debug_get_state(session_id: str):
    """디버그: 세션 상태 조회 (LangGraph 표준)"""
    try:
        agent = await get_agent()
        history = agent.get_conversation_history(session_id)

        return {
            "session_id": session_id,
            "history": history,
            "debug": True,
            "note": "LangGraph MemorySaver에서 messages 채널을 통해 대화 히스토리를 관리합니다.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    # 개발 서버 실행
    uvicorn.run(
        "src.agent.integrated_agent.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
