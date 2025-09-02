'use client'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
    Activity,
    Brain,
    Download,
    MoreVertical,
    Settings,
    Trash2
} from 'lucide-react'
import { useState } from 'react'

interface ChatHeaderProps {
  title?: string
  subtitle?: string
  isOnline?: boolean
  messageCount?: number
  onSettings?: () => void
  onExport?: () => void
  onClear?: () => void
  onNewChat?: () => void
}

export function ChatHeader({
  title = "AI 투자 분석가",
  subtitle = "실시간 종목 분석 서비스",
  isOnline = true,
  messageCount = 0,
  onSettings,
  onExport,
  onClear,
  onNewChat
}: ChatHeaderProps) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* 왼쪽: AI 정보 */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <Avatar className="border-2 border-white shadow-sm">
                <AvatarFallback className="bg-gradient-to-br from-orange-400 to-red-500 text-white">
                  <Brain className="w-6 h-6" />
                </AvatarFallback>
              </Avatar>
              
              {/* 온라인 상태 표시 */}
              <div className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${
                isOnline ? 'bg-green-500' : 'bg-gray-400'
              }`} />
            </div>
            
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
              <div className="flex items-center gap-2">
                <p className="text-sm text-gray-600">{subtitle}</p>
                {messageCount > 0 && (
                  <span className="text-xs text-gray-400">
                    • {messageCount}개 메시지
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 오른쪽: 상태 및 액션 */}
          <div className="flex items-center gap-3">
            {/* 온라인 상태 배지 */}
            <Badge 
              variant={isOnline ? "default" : "secondary"}
              className={`gap-1 ${
                isOnline 
                  ? "bg-green-100 text-green-800 border-green-200" 
                  : "bg-gray-100 text-gray-600 border-gray-200"
              }`}
            >
              <Activity className="w-3 h-3" />
              {isOnline ? "온라인" : "오프라인"}
            </Badge>

            {/* 새 채팅 버튼 */}
            <Button
              variant="outline"
              size="sm"
              onClick={onNewChat}
              className="gap-2 text-sm"
            >
              새 채팅
            </Button>

            {/* 메뉴 버튼 */}
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowMenu(!showMenu)}
                className="h-8 w-8 p-0"
              >
                <MoreVertical className="w-4 h-4" />
              </Button>

              {/* 드롭다운 메뉴 */}
              {showMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-20">
                  <button
                    onClick={() => {
                      onSettings?.()
                      setShowMenu(false)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Settings className="w-4 h-4" />
                    설정
                  </button>
                  
                  <button
                    onClick={() => {
                      onExport?.()
                      setShowMenu(false)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    대화 내보내기
                  </button>
                  
                  <div className="border-t border-gray-100 my-1" />
                  
                  <button
                    onClick={() => {
                      onClear?.()
                      setShowMenu(false)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    대화 지우기
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 메뉴 클릭 시 배경 클릭하면 닫기 */}
      {showMenu && (
        <div 
          className="fixed inset-0 z-10"
          onClick={() => setShowMenu(false)}
        />
      )}
    </div>
  )
}
