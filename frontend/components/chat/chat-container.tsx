'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ArrowLeft } from 'lucide-react'
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
  isValidating?: boolean
  onInputChange: (value: string) => void
  onSend: () => void
  onMessageCopy?: () => void
  onMessageRegenerate?: (messageId: string) => void
  onMessageFeedback?: (messageId: string, type: 'positive' | 'negative') => void
  onNewChat?: () => void
  onClear?: () => void
  onExport?: () => void
  onSettings?: () => void
  onBackToHome?: () => void
}

export function ChatContainer({
  messages,
  input,
  isLoading,
  isValidating = false,
  onInputChange,
  onSend,
  onMessageCopy,
  onMessageRegenerate,
  onMessageFeedback,
  onNewChat,
  onClear,
  onExport,
  onSettings,
  onBackToHome
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
            <div className="flex items-center gap-3">
              {onBackToHome && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onBackToHome}
                  className="p-1 h-8 w-8"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <div className="flex-1">
                <CardTitle className="text-lg">AI 투자 분석가</CardTitle>
                <CardDescription>실시간 종목 분석 서비스</CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-0 flex-1">
            <div className="flex h-full flex-col">
              {/* 메시지 영역 */}
              <ScrollArea className="flex-1">
                <div className="px-4">
                  {isEmpty ? (
                    <div className="flex flex-col items-center justify-center h-96 text-center space-y-4">
                      <div className="space-y-2">
                        <h2 className="text-xl font-semibold">무엇을 도와드릴까요?</h2>
                        <p className="text-muted-foreground text-sm">
                          궁금한 종목이나 투자 관련 질문을 자유롭게 물어보세요.
                        </p>
                      </div>
                      {/* MCP 상태 */}
                      <div className="mt-6">
                        <MCPStatus className="w-full max-w-md" />
                      </div>
                    </div>
                  ) : (
                    <>
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
                    </>
                  )}
                </div>
              </ScrollArea>

              {/* 입력창 - 콘텐츠 영역 하단에 고정 */}
              <div className="border-t">
                <ChatInput
                  value={input}
                  onChange={onInputChange}
                  onSend={onSend}
                  disabled={isLoading}
                  isLoading={isLoading}
                  isValidating={isValidating}
                  placeholder="메시지를 입력하세요..."
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
