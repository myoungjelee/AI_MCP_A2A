'use client'

import { ChatContainer } from '@/components/chat/chat-container'
import { useInvestmentValidation } from '@/hooks/useInvestmentValidation'
import { useState } from 'react'

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

interface AnalysisResult {
  success: boolean
  summary?: {
    current_step: string
    progress: number
    data_sources_count: number
    analysis_results_count: number
    insights_count: number
    decision_made: boolean
    confidence: number
    execution_status: string
    error_count: number
  }
  result?: any
  error?: string
}

export default function Home() {
  // 초기 메시지 없이 시작 (ChatContainer에서 처리)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const { validateQuestion } = useInvestmentValidation()

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const inputText = input.trim()
    
    // 먼저 투자 관련 질문인지 검증
    const validationResult = await validateQuestion(inputText)
    const isInvestmentRelated = validationResult.is_investment_related

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText,
      timestamp: new Date(),
      status: 'success'
    }

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: isInvestmentRelated ? '분석을 시작하고 있어요...' : '답변을 준비하고 있어요...',
      timestamp: new Date(),
      status: 'sending',
      isInvestmentRelated  // 투자 관련 여부 설정
    }

    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInput('')
    setIsLoading(true)

    try {
      // 비투자 질문이면 백엔드 요청 없이 바로 거부 메시지 표시
      if (!isInvestmentRelated) {
        setMessages(prev => 
          prev.map(msg => 
            msg.id === loadingMessage.id 
              ? { 
                  ...msg, 
                  content: "죄송합니다. 저는 투자 분석 전문 AI입니다. 주식, 경제, 투자 관련 질문만 답변드릴 수 있어요. 관련 분야로 다시 질문해 주세요.",
                  status: 'success' as const
                }
              : msg
          )
        )
        setIsLoading(false)
        return
      }

      // 투자 관련 질문만 백엔드로 분석 요청
      const response = await fetch('http://localhost:8000/analyze/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputText,
          session_id: sessionId || undefined
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('스트림을 읽을 수 없습니다')
      }

      const decoder = new TextDecoder()
      let accumulatedContent = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6).trim()
                if (!jsonStr) continue
                
                const data = JSON.parse(jsonStr)

                switch (data.type) {
                  case 'start':
                    if (!sessionId && data.session_id) {
                      setSessionId(data.session_id)
                    }
                    break

                  case 'step_update':
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === loadingMessage.id 
                          ? { 
                              ...msg, 
                              content: `${data.step} 단계 진행 중...`,
                              analysisStep: {
                                step: data.step,
                                message: `${data.step} 단계 진행 중...`
                              }
                            }
                          : msg
                      )
                    )
                    break

                  case 'final_response':
                    setMessages(prev => 
                      prev.map(msg => 
                        msg.id === loadingMessage.id 
                          ? { 
                              ...msg, 
                              content: data.response,
                              status: 'success',
                              usedMCPServers: data.used_servers ? {
                                used_servers: data.used_servers,
                                connected_servers: data.used_servers,
                                available_tools: data.used_servers.length,
                                total_servers: 6
                              } : undefined
                            }
                          : msg
                      )
                    )
                    break

                  case 'complete':
                    setIsLoading(false)
                    break

                  case 'error':
                    throw new Error(data.error || "알 수 없는 오류가 발생했습니다.")
                }
              } catch (parseError) {
                console.warn('JSON 파싱 실패:', parseError, 'Line:', line)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    } catch (error) {
      console.error('스트리밍 실패:', error)
      setMessages(prev => 
        prev.map(msg => 
          msg.id === loadingMessage.id 
            ? { 
                ...msg, 
                content: `죄송합니다. 서버와의 연결에 문제가 발생했습니다.\n\n${error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'}\n\n잠시 후 다시 시도해주세요.`,
                status: 'error' as const 
              }
            : msg
        )
      )
      setIsLoading(false)
    }
  }

  // 빠른 제안 질문들
  const quickQuestions = [
    '삼성전자 주가 전망은 어때?',
    '테슬라 투자해도 될까?',
    '비트코인 시장 상황은?',
    '네이버 실적 분석해줘',
    '애플 주식 어떻게 생각해?'
  ]

  // 새 채팅 시작
  const handleNewChat = () => {
    setMessages([])
    setInput('')
    setSessionId(null) // 세션 ID 초기화
  }

  // 채팅 기록 지우기
  const handleClear = () => {
    if (window.confirm('대화 기록을 모두 지우시겠습니까?')) {
      setMessages([])
      setSessionId(null)
    }
  }

  // 채팅 내보내기
  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      messages: messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp.toISOString()
      }))
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // 메시지 복사 완료 알림
  const handleMessageCopy = () => {
    // 토스트 알림 추가할 수 있음
    console.log('메시지가 복사되었습니다.')
  }

  // 메시지 재생성
  const handleMessageRegenerate = (messageId: string) => {
    // 마지막 사용자 메시지를 찾아서 다시 전송
    const lastUserMessage = messages
      .slice()
      .reverse()
      .find(msg => msg.type === 'user')
    
    if (lastUserMessage) {
      setInput(lastUserMessage.content)
      // 해당 메시지 이후의 메시지들 제거
      const messageIndex = messages.findIndex(msg => msg.id === messageId)
      if (messageIndex > 0) {
        setMessages(prev => prev.slice(0, messageIndex))
      }
    }
  }

  // 메시지 피드백
  const handleMessageFeedback = (messageId: string, type: 'positive' | 'negative') => {
    console.log(`메시지 ${messageId}에 ${type} 피드백`)
    // 실제로는 서버에 피드백 전송
  }

  // 제안 클릭 처리
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  return (
    <ChatContainer
      messages={messages}
      input={input}
      isLoading={isLoading}
      onInputChange={setInput}
      onSend={handleSend}
      onMessageCopy={handleMessageCopy}
      onMessageRegenerate={handleMessageRegenerate}
      onMessageFeedback={handleMessageFeedback}
      onNewChat={handleNewChat}
      onClear={handleClear}
      onExport={handleExport}
      quickSuggestions={quickQuestions}
      onSuggestionClick={handleSuggestionClick}
      showSuggestions={messages.length === 0}
    />
  )
}