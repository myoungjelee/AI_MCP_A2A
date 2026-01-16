'use client'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Server, Wifi, WifiOff, Wrench } from 'lucide-react'
import { useEffect, useState } from 'react'

interface MCPServer {
  name: string
  status: 'connected' | 'disconnected'
}

interface MCPStatusData {
  mcp_servers: Record<string, string>
  connected_count: number
  total_count: number
  connected_servers: string[]
  disconnected_servers: string[]
  available_tools: number
}

interface MCPStatusProps {
  className?: string
}

export function MCPStatus({ className }: MCPStatusProps) {
  const [mcpStatus, setMcpStatus] = useState<MCPStatusData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const endpoint = process.env.NEXT_PUBLIC_MCP_STATUS_ENDPOINT || '/mcp/status'

  // 서버명을 한글로 변환
  const getServerDisplayName = (serverName: string) => {
    const names = {
      'financedatareader': '금융데이터리더',
      'macroeconomic': '거시경제',
      'financial_analysis': '재무분석',
      'stock_analysis': '주식분석',
      'naver_news': '네이버뉴스',
      'tavily_search': '웹검색',
      'kiwoom': '키움증권'
    }
    return names[serverName as keyof typeof names] || serverName
  }

  const fetchMCPStatus = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(endpoint, { cache: 'no-store' })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      setMcpStatus(data)
      setError(null)
    } catch (err) {
      console.error('MCP 상태 조회 실패:', err)
      setError(err instanceof Error ? err.message : '알 수 없는 오류')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchMCPStatus()
    
    // 30초마다 상태 갱신
    const interval = setInterval(fetchMCPStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Server className="w-4 h-4" />
            MCP 서버 상태
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-gray-500">상태 확인 중...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Server className="w-4 h-4" />
            MCP 서버 상태
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-red-500">연결 오류: {error}</div>
        </CardContent>
      </Card>
    )
  }

  if (!mcpStatus) return null

  const connectionRate = mcpStatus.total_count > 0 
    ? Math.round((mcpStatus.connected_count / mcpStatus.total_count) * 100)
    : 0

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Server className="w-4 h-4" />
          MCP 서버 상태
        </CardTitle>
        <CardDescription className="text-xs">
          {mcpStatus.connected_count}/{mcpStatus.total_count} 서버 연결됨 ({connectionRate}%)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 연결 상태 요약 */}
        <div className="flex items-center gap-2 text-xs">
          {mcpStatus.connected_count > 0 ? (
            <Wifi className="w-3 h-3 text-green-500" />
          ) : (
            <WifiOff className="w-3 h-3 text-red-500" />
          )}
          <span className="text-gray-600">
            {mcpStatus.connected_count > 0 
              ? `${mcpStatus.connected_count}개 서버 활성` 
              : '연결된 서버 없음'
            }
          </span>
        </div>

        {/* 사용 가능한 도구 */}
        <div className="flex items-center gap-2 text-xs">
          <Wrench className="w-3 h-3 text-blue-500" />
          <span className="text-gray-600">
            {mcpStatus.available_tools}개 도구 사용 가능
          </span>
        </div>

        {/* 연결된 서버들 */}
        {mcpStatus.connected_servers.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-gray-700">활성 서버:</div>
            <div className="flex flex-wrap gap-1">
              {mcpStatus.connected_servers.map((server) => (
                <Badge key={server} variant="secondary" className="text-xs">
                  {getServerDisplayName(server)}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* 연결 안된 서버들 */}
        {mcpStatus.disconnected_servers.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-gray-500">비활성 서버:</div>
            <div className="flex flex-wrap gap-1">
              {mcpStatus.disconnected_servers.map((server) => (
                <Badge key={server} variant="outline" className="text-xs text-gray-400">
                  {getServerDisplayName(server)}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
