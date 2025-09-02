'use client'

import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import DOMPurify from 'dompurify'
import {
    BarChart3,
    Bot,
    Copy,
    Database,
    Lightbulb,
    RefreshCw,
    ThumbsDown,
    ThumbsUp,
    TrendingUp,
    User
} from 'lucide-react'
import { marked } from 'marked'
import { useState } from 'react'
import { AnalysisProgress } from './analysis-progress'
import { UsedMCPServers } from './used-mcp-servers'

// marked 렌더링 함수
const renderMarkdown = (content: string): string => {
  try {
    return marked.parse(content, {
      breaks: true,
      gfm: true
    }) as string
  } catch (error) {
    console.error('Markdown parsing error:', error)
    return content // 에러 시 원본 텍스트 반환
  }
}

interface MessageData {
  progress?: number
  data_sources_count?: number
  analysis_results_count?: number
  insights_count?: number
  confidence?: number
  current_step?: string
  decision_made?: boolean
  execution_status?: string
  error_count?: number
}

interface ChatMessageProps {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  status?: 'sending' | 'success' | 'error'
  data?: MessageData
  mcpStatus?: {
    connected_servers: string[]
    available_tools: number
    total_servers: number
  }
  analysisStep?: {
    step: string
    message: string
    status?: 'running' | 'completed'
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
  onCopy?: () => void
  onRegenerate?: () => void
  onFeedback?: (type: 'positive' | 'negative') => void
}

export function ChatMessage({
  id,
  type,
  content,
  timestamp,
  status = 'success',
  data,
  mcpStatus,
  analysisStep,
  toolStatuses,
  isInvestmentRelated = false,
  usedMCPServers,
  onCopy,
  onRegenerate,
  onFeedback
}: ChatMessageProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [feedbackGiven, setFeedbackGiven] = useState<'positive' | 'negative' | null>(null)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    onCopy?.()
  }

  const handleFeedback = (feedbackType: 'positive' | 'negative') => {
    setFeedbackGiven(feedbackType)
    onFeedback?.(feedbackType)
  }

  const isLoading = status === 'sending'
  const isUser = type === 'user'

  return (
    <div 
      className={cn(
        "group w-full py-6 transition-colors hover:bg-gray-50/50",
        isUser ? "bg-gray-50" : "bg-white"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex gap-4 px-6 max-w-5xl mx-auto">
        {/* 아바타 */}
        <div className="flex-shrink-0">
          {isUser ? (
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
          ) : (
            <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
          )}
        </div>

        {/* 메시지 컨텐츠 */}
        <div className="flex-1 space-y-3">
          {/* 분석 진행 상황 표시 (투자 관련 질문이고 상태가 sending일 때만) */}
                              {type === 'assistant' && 
                               status === 'sending' && 
                               isInvestmentRelated && 
                               (mcpStatus || analysisStep || toolStatuses) && (
                      <div className="mb-4">
                        <AnalysisProgress
                          currentStep={analysisStep?.step}
                          currentMessage={analysisStep?.message}
                          stepStatus={analysisStep?.status}
                          mcpStatus={mcpStatus}
                          toolStatuses={toolStatuses}
                        />
                      </div>
                    )}

          {/* 메시지 내용 */}
          <div className="prose prose-sm max-w-none">
            {isLoading ? (
              <div className="flex items-center gap-3 text-gray-600">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div 
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
                    style={{animationDelay: '0.1s'}}
                  ></div>
                  <div 
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" 
                    style={{animationDelay: '0.2s'}}
                  ></div>
                </div>
                <span className="text-sm">{analysisStep?.message || '분석하고 있어요...'}</span>
              </div>
            ) : (
              <div 
                className="prose prose-sm max-w-none leading-relaxed text-gray-800 markdown-content"
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(renderMarkdown(content))
                }}
              />
            )}
          </div>

          {/* 사용된 MCP 서버 (분석 완료 후) */}
          {usedMCPServers && !isLoading && (
            <UsedMCPServers
              usedServers={usedMCPServers.used_servers}
              connectedServers={usedMCPServers.connected_servers}
              availableTools={usedMCPServers.available_tools}
              totalServers={usedMCPServers.total_servers}
              className="mt-3"
            />
          )}

          {/* 분석 결과 데이터 */}
          {data && !isLoading && (
            <div className="bg-gray-50 rounded-xl p-4 space-y-4">
              {/* 메트릭스 그리드 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {data.progress !== undefined && (
                  <div className="bg-white rounded-lg p-3 text-center">
                    <BarChart3 className="w-5 h-5 text-blue-600 mx-auto mb-2" />
                    <div className="text-lg font-semibold text-gray-900">
                      {Math.round(data.progress * 100)}%
                    </div>
                    <div className="text-xs text-gray-600">진행률</div>
                  </div>
                )}
                
                {data.data_sources_count !== undefined && (
                  <div className="bg-white rounded-lg p-3 text-center">
                    <Database className="w-5 h-5 text-green-600 mx-auto mb-2" />
                    <div className="text-lg font-semibold text-gray-900">
                      {data.data_sources_count}
                    </div>
                    <div className="text-xs text-gray-600">데이터 소스</div>
                  </div>
                )}
                
                {data.analysis_results_count !== undefined && (
                  <div className="bg-white rounded-lg p-3 text-center">
                    <TrendingUp className="w-5 h-5 text-purple-600 mx-auto mb-2" />
                    <div className="text-lg font-semibold text-gray-900">
                      {data.analysis_results_count}
                    </div>
                    <div className="text-xs text-gray-600">분석 결과</div>
                  </div>
                )}
                
                {data.insights_count !== undefined && (
                  <div className="bg-white rounded-lg p-3 text-center">
                    <Lightbulb className="w-5 h-5 text-orange-600 mx-auto mb-2" />
                    <div className="text-lg font-semibold text-gray-900">
                      {data.insights_count}
                    </div>
                    <div className="text-xs text-gray-600">인사이트</div>
                  </div>
                )}
              </div>

              {/* 신뢰도 바 */}
              {data.confidence !== undefined && (
                <div className="bg-white rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">분석 신뢰도</span>
                    <span className="text-sm font-mono text-gray-600">
                      {Math.round(data.confidence)}%
                    </span>
                  </div>
                  <Progress value={data.confidence} className="h-2" />
                </div>
              )}

              {/* 현재 단계 */}
              {data.current_step && (
                <div className="bg-white rounded-lg p-3">
                  <div className="text-sm font-medium text-gray-700 mb-1">현재 단계</div>
                  <div className="text-sm text-gray-600">{data.current_step}</div>
                </div>
              )}
            </div>
          )}

          {/* 액션 버튼들 */}
          {!isUser && !isLoading && (isHovered || feedbackGiven) && (
            <div className="flex items-center gap-2 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-8 px-2 text-gray-500 hover:text-gray-700"
              >
                <Copy className="w-4 h-4" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={onRegenerate}
                className="h-8 px-2 text-gray-500 hover:text-gray-700"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>

              <div className="flex gap-1 ml-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFeedback('positive')}
                  className={cn(
                    "h-8 px-2",
                    feedbackGiven === 'positive' 
                      ? "text-green-600 bg-green-50" 
                      : "text-gray-500 hover:text-green-600"
                  )}
                >
                  <ThumbsUp className="w-4 h-4" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleFeedback('negative')}
                  className={cn(
                    "h-8 px-2",
                    feedbackGiven === 'negative' 
                      ? "text-red-600 bg-red-50" 
                      : "text-gray-500 hover:text-red-600"
                  )}
                >
                  <ThumbsDown className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {/* 타임스탬프 */}
          <div className="text-xs text-gray-400">
            {timestamp.toLocaleTimeString('ko-KR', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
