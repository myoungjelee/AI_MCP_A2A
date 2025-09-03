'use client'

import { MCPStatus } from '@/components/chat/mcp-status'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function Home() {
  const [customQuestion, setCustomQuestion] = useState('')
  const router = useRouter()

  // 미리 정의된 질문들
  const predefinedQuestions = [
    {
      category: "주식 분석",
      questions: [
        "삼성전자 주가 전망은 어때?",
        "테슬라 투자해도 될까?",
        "네이버 장기 투자 괜찮을까?",
        "애플 실적 분석해줘"
      ]
    },
    {
      category: "시장 동향",
      questions: [
        "비트코인 시장 상황은?",
        "미국 금리 인상 영향은?",
        "최근 주식 시장 전망은?",
        "코스피 상승 요인 분석해줘"
      ]
    },
    {
      category: "투자 전략",
      questions: [
        "ETF 분산투자 조합 추천",
        "배당주 투자 전략은?",
        "성장주 vs 가치주 어떻게 고를까?",
        "지금 투자하기 좋은 섹터는?"
      ]
    },
    {
      category: "기초 지식",
      questions: [
        "PER, PBR 쉽게 설명해줘",
        "ROE가 높으면 좋은 주식일까?",
        "주식 차트 보는 방법 알려줘",
        "재무제표 어떻게 분석해?"
      ]
    }
  ]

  // 질문 클릭 처리
  const handleQuestionClick = (question: string) => {
    const encodedQuestion = encodeURIComponent(question)
    router.push(`/chat?q=${encodedQuestion}`)
  }

  // 사용자 정의 질문 처리
  const handleCustomQuestionSubmit = () => {
    if (customQuestion.trim()) {
      const encodedQuestion = encodeURIComponent(customQuestion.trim())
      router.push(`/chat?q=${encodedQuestion}`)
    }
  }

  // Enter 키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCustomQuestionSubmit()
    }
  }

  // 바로 채팅 시작
  const handleStartChat = () => {
    router.push('/chat')
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-6xl py-8 px-4">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">AI 투자 분석가</h1>
          <p className="text-muted-foreground text-lg">
            실시간 데이터를 활용한 종합 투자 분석 서비스
          </p>
        </div>

        {/* MCP 서버 상태 */}
        <div className="flex justify-center mb-8">
          <MCPStatus className="w-full max-w-md" />
        </div>

        {/* 메인 컨텐츠 */}
        <div className="max-w-4xl mx-auto space-y-8">
          {/* 사용자 정의 질문 입력 */}
          <Card>
            <CardHeader>
              <CardTitle>무엇을 도와드릴까요?</CardTitle>
              <CardDescription>
                궁금한 종목이나 투자 관련 질문을 자유롭게 입력해주세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="예: 애플 주식 분석해줘, 비트코인 전망은 어때?"
                  value={customQuestion}
                  onChange={(e) => setCustomQuestion(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="flex-1"
                />
                <Button 
                  onClick={handleCustomQuestionSubmit}
                  disabled={!customQuestion.trim()}
                >
                  분석 시작
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 미리 정의된 질문들 */}
          <div className="grid gap-6">
            {predefinedQuestions.map((category, categoryIndex) => (
              <Card key={categoryIndex}>
                <CardHeader>
                  <CardTitle className="text-lg">{category.category}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {category.questions.map((question, questionIndex) => (
                      <Button
                        key={questionIndex}
                        variant="outline"
                        onClick={() => handleQuestionClick(question)}
                        className="h-auto text-left p-3 justify-start"
                      >
                        {question}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}