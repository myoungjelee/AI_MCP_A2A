'use client'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { QuestionValidator } from './question-validator'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  placeholder?: string
  disabled?: boolean
  isLoading?: boolean
  isValidating?: boolean
  maxLength?: number
  quickSuggestions?: string[]
  onSuggestionClick?: (suggestion: string) => void
  showSuggestions?: boolean
  showValidation?: boolean
  onValidationResult?: (isInvestmentRelated: boolean) => void
}

export function ChatInput({
  value,
  onChange,
  onSend,
  placeholder = "메시지를 입력하세요...",
  disabled = false,
  isLoading = false,
  isValidating = false,
  maxLength = 2000,
  quickSuggestions = [],
  onSuggestionClick,
  showSuggestions = false,
  showValidation = true,
  onValidationResult
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [isFocused, setIsFocused] = useState(false)

  // 자동 높이 조절
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() && !disabled && !isValidating) {
        onSend()
      }
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion)
    onSuggestionClick?.(suggestion)
  }

  const canSend = value.trim().length > 0 && !disabled && !isValidating

  return (
    <div className="border-t bg-white">
      <div className="max-w-5xl mx-auto w-full">
        {/* 빠른 제안 (빈 화면에서 공간 채우기) */}
        {showSuggestions && quickSuggestions.length > 0 && (
          <div className="px-4 pt-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {quickSuggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="justify-start h-10 text-sm bg-white hover:bg-gray-50 border-gray-200"
                  disabled={disabled || isValidating}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* 입력 영역 */}
        <div className="px-3 py-2">
          <div className={cn(
            "relative flex items-end gap-2.5 p-3 border rounded-xl transition-all",
            isLoading
              ? "border-blue-400 bg-blue-50"
              : (isFocused 
                  ? "border-gray-300 shadow-sm bg-white" 
                  : "border-gray-200 bg-white")
          )}>
            {/* 텍스트 입력 */}
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder={placeholder}
                className={cn(
                  "min-h-[44px] max-h-[240px] resize-none border-0 bg-transparent p-0 text-[15px]",
                  "focus:ring-0 focus:outline-none placeholder:text-gray-400",
                  "scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
                )}
                disabled={disabled || isValidating}
                maxLength={maxLength}
                rows={1}
              />
            </div>

            {/* 전송 버튼 */}
            <Button
              onClick={onSend}
              disabled={!canSend}
              className={cn(
                "h-9 w-9 p-0 shrink-0 transition-all",
                canSend
                  ? "bg-black hover:bg-gray-800 text-white"
                  : "bg-gray-200 text-gray-400 cursor-not-allowed"
              )}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>

          {/* 질문 검증 결과 */}
          {showValidation && value.trim().length > 3 && (
            <div className="mt-2 px-1">
              <QuestionValidator 
                question={value}
                onValidationResult={onValidationResult}
                showValidation={showValidation}
              />
            </div>
          )}

          {/* 도움말 텍스트 */}
          <div className="text-center mt-1">
            {isLoading ? (
              <div className="text-[10px] text-blue-600">분석 중...</div>
            ) : isValidating ? (
              <div className="text-[10px] text-orange-600">질문 검증 중...</div>
            ) : (
              <div className="text-[10px] text-gray-500">Enter로 전송, Shift+Enter로 줄바꿈</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
