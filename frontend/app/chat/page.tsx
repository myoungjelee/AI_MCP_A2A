'use client'

import { ChatContainer } from '@/components/chat/chat-container'
import { useInvestmentValidation } from '@/hooks/useInvestmentValidation'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useRef, useState } from 'react'

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
  isInvestmentRelated?: boolean
  usedMCPServers?: {
    used_servers: string[]
    connected_servers: string[]
    available_tools: number
    total_servers: number
  }
}

export default function ChatPage() {
  return (
    <Suspense fallback={null}>
      <ChatPageContent />
    </Suspense>
  )
}

function ChatPageContent() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(() => {
    // 새로고침 시에도 세션 ID 유지
    if (typeof window !== 'undefined') {
      return localStorage.getItem('chat_session_id') || null
    }
    return null
  })
  const isSendingRef = useRef(false)
  const { validateQuestion, isValidating } = useInvestmentValidation()
  const router = useRouter()
  const searchParams = useSearchParams()

  // URL 파라미터에서 초기 질문 가져오기 및 자동 실행
  useEffect(() => {
    const initialQuestion = searchParams.get('q')
    if (initialQuestion && !isLoading && messages.length === 0) {
      const question = decodeURIComponent(initialQuestion)
      setInput(question)
      
      // 자동으로 질문 실행
      setTimeout(() => {
        handleAutoSend(question)
      }, 100)
    }
  }, [searchParams, isLoading, messages.length])

  // 자동 질문 실행 함수
  const handleAutoSend = async (question: string) => {
    if (!question.trim() || isLoading || isSendingRef.current) return

    isSendingRef.current = true
    const inputText = question.trim()
    
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
      isInvestmentRelated
    }

    setMessages([userMessage, loadingMessage])
    setInput('')
    setIsLoading(true)

    // 실제 분석 로직은 기존 handleSend와 동일
    try {
      await executeAnalysis(inputText, isInvestmentRelated, loadingMessage)
    } finally {
      isSendingRef.current = false
    }
  }

  // 분석 실행 로직을 분리
  const executeAnalysis = async (inputText: string, isInvestmentRelated: boolean, loadingMessage: Message) => {
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
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiBaseUrl}/analyze/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputText,
          ...(sessionId && { session_id: sessionId })  // sessionId가 있을 때만 포함 
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
      let buffer = '' // chunk 사이에 걸친 데이터 누적용

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          // 1) 새 chunk 를 버퍼에 이어붙이기
          buffer += decoder.decode(value, { stream: true })

          // 2) SSE 이벤트는 보통 \n\n 로 한 덩어리가 끝남
          const events = buffer.split('\n\n')
          buffer = events.pop() ?? '' // 마지막 조각은 아직 미완성일 수 있으니 버퍼에 남김

          // 3) 완성된 이벤트들만 처리
          for (const event of events) {
            // 여러 줄 중 data: 로 시작하는 줄만 찾기
            const dataLine = event
              .split('\n')
              .find(line => line.startsWith('data: '))

            if (!dataLine) continue

            const jsonStr = dataLine.slice(6).trim()
            if (!jsonStr) continue

            let data: any
            try {
              data = JSON.parse(jsonStr)
            } catch (e) {
              console.warn('JSON 파싱 실패:', e, '\nraw:', jsonStr)
              continue // 이 이벤트만 건너뛰고 나머지 계속
            }

            switch (data.type) {
              case 'start':
                if (!sessionId && data.session_id) {
                  setSessionId(data.session_id)
                  localStorage.setItem('chat_session_id', data.session_id)
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
                            message: `${data.step} 단계 진행 중...`,
                            status: data.status || 'running',
                          },
                        }
                      : msg,
                  ),
                )
                break

              case 'step_completed':
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === loadingMessage.id
                      ? {
                          ...msg,
                          analysisStep: {
                            step: data.step,
                            message: `${data.step} 단계 완료`,
                            status: 'completed',
                          },
                        }
                      : msg,
                  ),
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
                          usedMCPServers: data.used_servers
                            ? {
                                used_servers: data.used_servers,
                                connected_servers: data.used_servers,
                                available_tools: data.used_servers.length,
                                total_servers: 6,
                              }
                            : undefined,
                        }
                      : msg,
                  ),
                )
                break

              case 'complete':
                setIsLoading(false)
                break

              case 'error':
                throw new Error(
                  data.error || '알 수 없는 오류가 발생했습니다.',
                )
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

  const handleSend = async () => {
    if (!input.trim() || isLoading || isSendingRef.current) return

    isSendingRef.current = true
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
      isInvestmentRelated
    }

    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInput('')
    setIsLoading(true)

    // 분석 실행
    try {
      await executeAnalysis(inputText, isInvestmentRelated, loadingMessage)
    } finally {
      isSendingRef.current = false
    }
  }



  // 새 대화 시작
  const handleNewChat = () => {
    setMessages([])
    setInput('')
    setSessionId(null)
    localStorage.removeItem('chat_session_id')
    // URL에서 쿼리 파라미터 제거
    router.replace('/chat')
  }

  // 채팅 기록 지우기
  const handleClear = () => {
    if (window.confirm('대화 기록을 모두 지우시겠습니까?')) {
      setMessages([])
      setSessionId(null)
      localStorage.removeItem('chat_session_id')
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
    console.log('메시지가 복사되었습니다.')
  }

  // 메시지 재생성
  const handleMessageRegenerate = (messageId: string) => {
    const lastUserMessage = messages
      .slice()
      .reverse()
      .find(msg => msg.type === 'user')
    
    if (lastUserMessage) {
      setInput(lastUserMessage.content)
      const messageIndex = messages.findIndex(msg => msg.id === messageId)
      if (messageIndex > 0) {
        setMessages(prev => prev.slice(0, messageIndex))
      }
    }
  }

  // 메시지 피드백
  const handleMessageFeedback = (messageId: string, type: 'positive' | 'negative') => {
    console.log(`메시지 ${messageId}에 ${type} 피드백`)
  }




  // 메인 페이지로 돌아가기
  const handleBackToHome = () => {
    router.push('/')
  }

  return (
    <ChatContainer
      messages={messages}
      input={input}
      isLoading={isLoading}
      isValidating={isValidating}
      onInputChange={setInput}
      onSend={handleSend}
      onMessageCopy={handleMessageCopy}
      onMessageRegenerate={handleMessageRegenerate}
      onMessageFeedback={handleMessageFeedback}
      onNewChat={handleNewChat}
      onClear={handleClear}
      onExport={handleExport}
      onBackToHome={handleBackToHome}
    />
  )
}
