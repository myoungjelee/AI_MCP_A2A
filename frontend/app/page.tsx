"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BarChart3, Bot, DollarSign, Loader2, Send, TrendingUp, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ApiResponse {
  success: boolean;
  session_id: string;
  message: string;
  summary?: string;
}

export default function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 추천 질문들
  const suggestedQuestions = [
    "삼성전자 주식 분석해줘",
    "네이버 최신 뉴스 보여줘", 
    "카카오 투자 전망은?",
    "SK하이닉스 재무 상태는?",
    "현재 시장 상황 분석"
  ];

  // 스크롤을 맨 아래로
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 메시지 전송
  const sendMessage = async (messageText?: string) => {
    const text = messageText || inputMessage.trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          task_type: "comprehensive_analysis",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      
      if (data.success) {
        setSessionId(data.session_id);
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.message,
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error("API returned error");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant", 
        content: "죄송합니다. 현재 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  // Enter 키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* 헤더 */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">AI 투자 분석 어시스턴트</h1>
              <p className="text-sm text-slate-500">실시간 주식 분석 및 투자 상담</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-green-600 border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              연결됨
            </Badge>
          </div>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full px-6">
          <div className="max-w-4xl mx-auto py-6">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-slate-800 mb-2">
                  무엇을 도와드릴까요?
                </h2>
                <p className="text-slate-500 mb-8">
                  주식 분석, 시장 동향, 투자 조언 등 무엇이든 물어보세요
                </p>
                
                {/* 추천 질문들 */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-w-3xl mx-auto">
                  {suggestedQuestions.map((question, index) => (
                    <Card 
                      key={index}
                      className="p-4 cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-105 bg-white/60 hover:bg-white/80"
                      onClick={() => sendMessage(question)}
                    >
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-lg flex items-center justify-center">
                          {index === 0 && <DollarSign className="w-4 h-4 text-white" />}
                          {index === 1 && <BarChart3 className="w-4 h-4 text-white" />}
                          {index === 2 && <TrendingUp className="w-4 h-4 text-white" />}
                          {index === 3 && <DollarSign className="w-4 h-4 text-white" />}
                          {index === 4 && <BarChart3 className="w-4 h-4 text-white" />}
                        </div>
                        <span className="text-sm font-medium text-slate-700">{question}</span>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* 메시지 목록 */}
            <div className="space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`flex max-w-3xl ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                    {/* 아바타 */}
                    <div className={`flex-shrink-0 ${message.role === "user" ? "ml-3" : "mr-3"}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        message.role === "user" 
                          ? "bg-gradient-to-r from-blue-500 to-blue-600" 
                          : "bg-gradient-to-r from-purple-500 to-purple-600"
                      }`}>
                        {message.role === "user" ? (
                          <User className="w-4 h-4 text-white" />
                        ) : (
                          <Bot className="w-4 h-4 text-white" />
                        )}
                      </div>
                    </div>

                    {/* 메시지 내용 */}
                    <div className={`${message.role === "user" ? "bg-blue-500 text-white" : "bg-white text-slate-800"} rounded-2xl px-4 py-3 shadow-sm border`}>
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {message.content}
                      </div>
                      <div className={`text-xs mt-2 ${message.role === "user" ? "text-blue-100" : "text-slate-400"}`}>
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* 로딩 인디케이터 */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex">
                    <div className="flex-shrink-0 mr-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-purple-600 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                    </div>
                    <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="w-4 h-4 animate-spin text-purple-500" />
                        <span className="text-sm text-slate-500">분석 중...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* 입력 영역 */}
      <div className="bg-white/80 backdrop-blur-sm border-t border-slate-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex space-x-4">
            <div className="flex-1 relative">
              <Input
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="메시지를 입력하세요... (예: 삼성전자 분석해줘)"
                className="pr-12 py-3 text-sm border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                disabled={isLoading}
              />
              <Button
                onClick={() => sendMessage()}
                disabled={!inputMessage.trim() || isLoading}
                size="sm"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <div className="text-xs text-slate-400 mt-2 text-center">
            AI 분석 결과는 투자 참고용이며, 실제 투자 결정은 신중하게 하시기 바랍니다.
          </div>
        </div>
      </div>
    </div>
  );
}