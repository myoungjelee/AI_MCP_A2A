'use client'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { CheckCircle } from 'lucide-react'

interface UsedMCPServersProps {
  usedServers: string[]
  connectedServers: string[]
  availableTools: number
  totalServers: number
  className?: string
}

export function UsedMCPServers({ 
  usedServers, 
  connectedServers,
  availableTools,
  totalServers,
  className 
}: UsedMCPServersProps) {
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

  if (!usedServers || usedServers.length === 0) return null

  return (
    <Card className={`border-l-4 border-l-green-500 bg-green-50/50 ${className}`}>
      <CardContent className="p-4 space-y-3">
        {/* 제목 */}
        <div className="flex items-center gap-2 text-sm font-medium text-green-800">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <span>분석에 사용된 MCP 서버</span>
        </div>

        {/* 사용된 서버들 */}
        <div className="flex flex-wrap gap-2">
          {usedServers.map((server) => (
            <Badge 
              key={server} 
              className="bg-green-100 text-green-800 border-green-200 hover:bg-green-200"
            >
              <CheckCircle className="w-3 h-3 mr-1" />
              {getServerDisplayName(server)}
            </Badge>
          ))}
        </div>

        {/* 요약 정보 */}
        <div className="text-xs text-green-700 flex items-center gap-4">
          <span>✓ {usedServers.length}개 서버 활용</span>
          <span>✓ {availableTools}개 도구 사용 가능</span>
          <span>✓ 실시간 데이터 기반 분석</span>
        </div>
      </CardContent>
    </Card>
  )
}
