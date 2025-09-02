/**
 * 투자 질문 검증 API 라우트
 */
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { question } = body;

    if (!question || typeof question !== "string") {
      return NextResponse.json(
        {
          success: false,
          error: "질문을 입력해주세요",
          message: "유효한 질문이 필요합니다",
        },
        { status: 400 }
      );
    }

    // 백엔드 에이전트 서버로 요청 전달
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/validate/investment/json`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error("Backend validation error:", errorData);

      return NextResponse.json(
        {
          success: false,
          error: "백엔드 서버 오류",
          message: "질문 검증 중 오류가 발생했습니다",
        },
        { status: response.status }
      );
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Validation API error:", error);

    return NextResponse.json(
      {
        success: false,
        error: "서버 오류",
        message: "질문 검증 중 내부 오류가 발생했습니다",
      },
      { status: 500 }
    );
  }
}
