/**
 * 질문 검증 컴포넌트
 * 사용자가 질문을 입력할 때 실시간으로 투자 관련 여부를 검증
 */
'use client';

import { Badge } from '@/components/ui/badge';
import { useInvestmentValidation } from '@/hooks/useInvestmentValidation';
import { AlertCircle, CheckCircle, Loader2, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

interface QuestionValidatorProps {
  question: string;
  onValidationResult?: (isInvestmentRelated: boolean) => void;
  showValidation?: boolean;
}

export function QuestionValidator({ 
  question, 
  onValidationResult, 
  showValidation = true 
}: QuestionValidatorProps) {
  const { validateQuestion, isValidating, lastResult, error } = useInvestmentValidation();
  const [debouncedQuestion, setDebouncedQuestion] = useState(question);

  // 디바운싱: 사용자가 타이핑을 멈춘 후 500ms 뒤에 검증
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuestion(question);
    }, 500);

    return () => clearTimeout(timer);
  }, [question]);

  // 디바운싱된 질문이 변경되면 검증 실행
  useEffect(() => {
    if (debouncedQuestion.trim() && debouncedQuestion.length > 3) {
      validateQuestion(debouncedQuestion).then((result) => {
        onValidationResult?.(result.is_investment_related);
      });
    }
  }, [debouncedQuestion, validateQuestion, onValidationResult]);

  // 검증 결과가 없거나 표시하지 않는 경우
  if (!showValidation || !question.trim() || question.length <= 3) {
    return null;
  }

  // 로딩 중
  if (isValidating) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>질문 검증 중...</span>
      </div>
    );
  }

  // 에러 발생
  if (error) {
    return (
      <div className="flex items-center gap-2">
        <AlertCircle className="h-3 w-3 text-orange-500" />
        <Badge variant="outline" className="text-orange-600 border-orange-200">
          검증 오류
        </Badge>
        <span className="text-xs text-muted-foreground">{error}</span>
      </div>
    );
  }

  // 검증 결과 표시
  if (lastResult && lastResult.question === debouncedQuestion) {
    const isInvestment = lastResult.is_investment_related;
    
    return (
      <div className="flex items-center gap-2">
        {isInvestment ? (
          <>
            <CheckCircle className="h-3 w-3 text-green-500" />
            <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
              투자 관련
            </Badge>
          </>
        ) : (
          <>
            <XCircle className="h-3 w-3 text-red-500" />
            <Badge variant="outline" className="text-red-600 border-red-200">
              투자 무관
            </Badge>
          </>
        )}
        <span className="text-xs text-muted-foreground">
          {lastResult.message}
        </span>
      </div>
    );
  }

  return null;
}
