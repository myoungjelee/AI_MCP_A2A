/**
 * 투자 질문 검증 훅
 */
import { useCallback, useState } from "react";

interface ValidationResult {
  success: boolean;
  question: string;
  is_investment_related: boolean;
  category: "investment" | "non_investment";
  message: string;
  timestamp: number;
  suggested_action?: "proceed_analysis" | "show_rejection_message";
  error?: string;
}

interface UseInvestmentValidationReturn {
  validateQuestion: (question: string) => Promise<ValidationResult>;
  isValidating: boolean;
  lastResult: ValidationResult | null;
  error: string | null;
}

export function useInvestmentValidation(): UseInvestmentValidationReturn {
  const [isValidating, setIsValidating] = useState(false);
  const [lastResult, setLastResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateQuestion = useCallback(
    async (question: string): Promise<ValidationResult> => {
      if (!question.trim()) {
        const emptyResult: ValidationResult = {
          success: false,
          question: "",
          is_investment_related: false,
          category: "non_investment",
          message: "질문을 입력해주세요",
          timestamp: Date.now(),
          error: "빈 질문은 검증할 수 없습니다",
        };
        setLastResult(emptyResult);
        return emptyResult;
      }

      setIsValidating(true);
      setError(null);

      try {
        const response = await fetch("/api/validate/investment/json", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: question.trim() }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result: ValidationResult = await response.json();
        setLastResult(result);

        if (!result.success && result.error) {
          setError(result.error);
        }

        return result;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다";
        setError(errorMessage);

        const errorResult: ValidationResult = {
          success: false,
          question,
          is_investment_related: false,
          category: "non_investment",
          message: "검증 중 오류가 발생했습니다",
          timestamp: Date.now(),
          error: errorMessage,
        };

        setLastResult(errorResult);
        return errorResult;
      } finally {
        setIsValidating(false);
      }
    },
    []
  );

  return {
    validateQuestion,
    isValidating,
    lastResult,
    error,
  };
}
