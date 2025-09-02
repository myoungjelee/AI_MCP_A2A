'use client'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CheckCircle, Clock, Database, Loader2, Server, Wrench, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

interface AnalysisStep {
  step: string
  message: string
  status?: 'running' | 'completed'
}

interface MCPStatusInfo {
  connected_servers: string[]
  available_tools: number
  total_servers: number
}

interface ToolStatus {
  tool: string
  action: string
  status: 'running' | 'completed' | 'error'
  error?: string
}

interface AnalysisProgressProps {
  currentStep?: string
  currentMessage?: string
  stepStatus?: 'running' | 'completed'
  mcpStatus?: MCPStatusInfo
  toolStatuses?: ToolStatus[]
  className?: string
}

const stepConfig = {
  data_collection: { 
    label: '데이터 수집', 
    icon: Database, 
    description: 'MCP 서버에서 실시간 데이터 수집 중' 
  },
  analysis: { 
    label: '데이터 분석', 
    icon: Clock, 
    description: '수집된 데이터를 분석하여 패턴 파악 중' 
  },
  decision: { 
    label: '의사결정', 
    icon: CheckCircle, 
    description: '분석 결과를 바탕으로 투자 의사결정 생성 중' 
  },
  response: { 
    label: '답변 생성', 
    icon: CheckCircle, 
    description: 'AI가 사용자 맞춤 답변을 작성 중' 
  }
}

export function AnalysisProgress({ 
  currentStep, 
  currentMessage, 
  stepStatus,
  mcpStatus, 
  toolStatuses = [],
  className 
}: AnalysisProgressProps) {
  const [progress, setProgress] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<string[]>([])

  const steps = Object.keys(stepConfig)
  const currentStepIndex = currentStep ? steps.indexOf(currentStep) : -1

  useEffect(() => {
    if (currentStep) {
      // 현재 단계가 완료된 경우에만 완료된 단계에 추가
      if (stepStatus === 'completed') {
        setCompletedSteps(prev => {
          if (!prev.includes(currentStep)) {
            const newCompleted = [...prev, currentStep]
            // 완료된 단계 수에 따라 진행률 계산
            const newProgress = (newCompleted.length / steps.length) * 100
            setProgress(newProgress)
            return newCompleted
          }
          return prev
        })
      } else if (stepStatus === 'running') {
        // 실행 중인 단계는 이전 단계까지만 완료로 표시
        const progressValue = completedSteps.length / steps.length * 100 + 
                              (1 / steps.length * 100 * 0.5) // 현재 단계는 50% 진행으로 표시
        setProgress(progressValue)
      }
    }
  }, [currentStep, stepStatus, completedSteps.length, steps.length])

  // 도구 상태별 아이콘
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="w-3 h-3 text-green-500" />
      case 'error':
        return <XCircle className="w-3 h-3 text-red-500" />
      default:
        return <Loader2 className="w-3 h-3 animate-spin text-gray-400" />
    }
  }

  // 서버명을 한글로 변환
  const getServerDisplayName = (serverName: string) => {
    const names = {
      'macroeconomic': '거시경제',
      'financial_analysis': '재무분석',
      'stock_analysis': '주식분석',
      'naver_news': '네이버뉴스',
      'tavily_search': '웹검색',
      'kiwoom': '키움증권'
    }
    return names[serverName as keyof typeof names] || serverName
  }

  if (!currentStep && !mcpStatus && toolStatuses.length === 0) return null

  return (
    <Card className={`border-l-4 border-l-blue-500 ${className}`}>
      <CardContent className="p-4 space-y-4">
        {/* MCP 서버 상태 */}
        {mcpStatus && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Server className="w-4 h-4 text-blue-500" />
              <span>연결된 MCP 서버</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {mcpStatus.connected_servers.map((server) => (
                <Badge key={server} variant="secondary" className="text-xs">
                  {server}
                </Badge>
              ))}
              {mcpStatus.connected_servers.length === 0 && (
                <Badge variant="outline" className="text-xs text-gray-500">
                  로컬 분석 모드
                </Badge>
              )}
            </div>
            <div className="text-xs text-gray-600">
              {mcpStatus.available_tools}개 도구 사용 가능 · {mcpStatus.connected_servers.length}/{mcpStatus.total_servers} 서버 활성
            </div>
          </div>
        )}

        {/* MCP 도구 실행 상태 */}
        {toolStatuses.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Wrench className="w-4 h-4 text-blue-500" />
              <span>MCP 도구 실행 상태</span>
            </div>
            
            <div className="space-y-1">
              {toolStatuses.map((toolStatus, index) => (
                <div 
                  key={`${toolStatus.tool}-${toolStatus.action}-${index}`}
                  className="flex items-center gap-2 text-xs bg-white rounded p-2 border"
                >
                  {getStatusIcon(toolStatus.status)}
                  <span className="font-medium text-gray-700 min-w-0 truncate">
                    {getServerDisplayName(toolStatus.tool)}
                  </span>
                  <span className="text-gray-500 min-w-0 truncate flex-1">
                    {toolStatus.action}
                  </span>
                  {toolStatus.error && (
                    <span className="text-red-500 text-xs">
                      오류
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 진행 상황 */}
        {currentStep && (
          <div className="space-y-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">분석 진행 상황</span>
                <span className="text-gray-600">{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {/* 현재 단계 표시 */}
            {currentStep && stepConfig[currentStep as keyof typeof stepConfig] && (
              <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                {(() => {
                  const StepIcon = stepConfig[currentStep as keyof typeof stepConfig].icon
                  return <StepIcon className="w-5 h-5 text-blue-600 mt-0.5 animate-pulse" />
                })()}
                <div className="flex-1 space-y-1">
                  <div className="font-medium text-blue-900">
                    {stepConfig[currentStep as keyof typeof stepConfig].label}
                  </div>
                  <div className="text-sm text-blue-700">
                    {currentMessage || stepConfig[currentStep as keyof typeof stepConfig].description}
                  </div>
                </div>
              </div>
            )}

            {/* 단계 목록 */}
            <div className="space-y-2">
              {steps.map((step, index) => {
                const config = stepConfig[step as keyof typeof stepConfig]
                const isCompleted = completedSteps.includes(step)
                const isCurrent = step === currentStep
                const isPending = index > currentStepIndex
                
                return (
                  <div 
                    key={step}
                    className={`flex items-center gap-3 p-2 rounded-md transition-colors ${
                      isCurrent ? 'bg-blue-50' : 
                      isCompleted ? 'bg-green-50' : 
                      'bg-gray-50'
                    }`}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      isCompleted ? 'bg-green-500 text-white' :
                      isCurrent ? 'bg-blue-500 text-white' :
                      'bg-gray-300 text-gray-600'
                    }`}>
                      {isCompleted ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : (
                        <span className="text-xs font-bold">{index + 1}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className={`text-sm font-medium ${
                        isCompleted ? 'text-green-700' :
                        isCurrent ? 'text-blue-700' :
                        'text-gray-600'
                      }`}>
                        {config.label}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
