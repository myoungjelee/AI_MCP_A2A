'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useEffect, useRef } from 'react'
import { ChatInput } from './chat-input'
import { ChatMessage } from './chat-message'
import { MCPStatus } from './mcp-status'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  status?: 'sending' | 'success' | 'error'
  data?: any
  mcpStatus?: {
    connected_servers: string[]
    available_tools: number
    total_servers: number
  }
  analysisStep?: {
    step: string
    message: string
  }
  toolStatuses?: {
    tool: string
    action: string
    status: 'running' | 'completed' | 'error'
    error?: string
  }[]
  isInvestmentRelated?: boolean  // 투자 관련 질문 여부
  usedMCPServers?: {  // 분석 완료 후 실제 사용된 MCP 서버들
    used_servers: string[]
    connected_servers: string[]
    available_tools: number
    total_servers: number
  }
}

interface ChatContainerProps {
  messages: Message[]
  input: string
  isLoading: boolean
  onInputChange: (value: string) => void
  onSend: () => void
  onMessageCopy?: () => void
  onMessageRegenerate?: (messageId: string) => void
  onMessageFeedback?: (messageId: string, type: 'positive' | 'negative') => void
  onNewChat?: () => void
  onClear?: () => void
  onExport?: () => void
  onSettings?: () => void
  quickSuggestions?: string[]
  onSuggestionClick?: (suggestion: string) => void
  showSuggestions?: boolean
}

export function ChatContainer({
  messages,
  input,
  isLoading,
  onInputChange,
  onSend,
  onMessageCopy,
  onMessageRegenerate,
  onMessageFeedback,
  onNewChat,
  onClear,
  onExport,
  onSettings,
  quickSuggestions = [],
  onSuggestionClick,
  showSuggestions = false
}: ChatContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 메시지가 추가될 때마다 스크롤을 맨 아래로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isEmpty = messages.length === 0

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-6xl py-6 px-4">
        <Card className="flex flex-col">
          <CardHeader className="border-b">
            <CardTitle className="text-lg">AI 투자 분석가</CardTitle>
            <CardDescription>실시간 종목 분석 서비스</CardDescription>
          </CardHeader>

          <CardContent className="p-0 flex-1">
            <div className="flex h-full flex-col">
              {/* 빈 상태: 안내 + 추천 + MCP 상태 */}
              {isEmpty ? (
                <div className="px-6 py-4">
                  <div className="max-w-4xl mx-auto space-y-6">
                    {/* 메인 인사 섹션 */}
                    <div className="text-center space-y-4">
                      <div className="space-y-1">
                        <h2 className="text-xl font-semibold">무엇을 도와드릴까요?</h2>
                        <p className="text-muted-foreground text-sm">궁금한 종목이나 투자 관련 질문을 자유롭게 물어보세요.</p>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-2xl mx-auto">
                        {[
                          "삼성전자 주가 전망은 어때?",
                          "테슬라 투자해도 될까?",
                          "비트코인 시장 상황은?",
                          "애플 실적 분석해줘",
                          "네이버 장기 투자 괜찮을까?",
                          "ETF 분산투자 조합 추천",
                          "미국 금리 인상 영향은?",
                          "PER, PBR 쉽게 설명해줘"
                        ].map((example, index) => (
                          <button
                            key={index}
                            onClick={() => onSuggestionClick?.(example)}
                            className="text-left p-3 bg-muted hover:bg-accent rounded-md transition-colors text-foreground/80 hover:text-foreground text-sm"
                          >
                            {example}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* MCP 상태 섹션 */}
                    <div className="flex justify-center">
                      <MCPStatus className="w-full max-w-md" />
                    </div>
                  </div>
                </div>
              ) : (
                <ScrollArea className="flex-1">
                  <div className="px-4">
                    {messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        {...message}
                        onCopy={onMessageCopy}
                        onRegenerate={() => onMessageRegenerate?.(message.id)}
                        onFeedback={(type) => onMessageFeedback?.(message.id, type)}
                      />
                    ))}
                    <div ref={messagesEndRef} className="h-4" />
                  </div>
                </ScrollArea>
              )}

              {/* 입력창 - 콘텐츠 영역 하단에 고정 */}
              <div className="border-t">
                <ChatInput
                  value={input}
                  onChange={onInputChange}
                  onSend={onSend}
                  disabled={isLoading}
                  placeholder="메시지를 입력하세요..."
                  quickSuggestions={quickSuggestions}
                  onSuggestionClick={onSuggestionClick}
                  showSuggestions={false}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
