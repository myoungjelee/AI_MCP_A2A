#!/bin/bash

# AI MCP A2A 통합 에이전트 Docker 빌드 스크립트

set -e

echo "🐳 AI MCP A2A 통합 에이전트 Docker 빌드 시작..."

# 프로젝트 루트로 이동
cd "$(dirname "$0")/../.."

echo "📁 현재 작업 디렉토리: $(pwd)"

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
docker-compose -f docker/agents/docker-compose.yml down --remove-orphans || true

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose -f docker/agents/docker-compose.yml build --no-cache

echo "✅ Docker 이미지 빌드 완료!"

# 컨테이너 시작
echo "🚀 컨테이너 시작 중..."
docker-compose -f docker/agents/docker-compose.yml up -d

echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 헬스 체크
echo "🏥 헬스 체크 중..."
echo "- 통합 에이전트: http://localhost:8000/health"
curl -f http://localhost:8000/health || echo "❌ 통합 에이전트 헬스 체크 실패"

echo ""
echo "📊 실행 중인 컨테이너:"
docker-compose -f docker/agents/docker-compose.yml ps

echo ""
echo "🎉 AI MCP A2A 통합 에이전트 Docker 빌드 및 실행 완료!"
echo ""
echo "📍 접속 정보:"
echo "- 통합 에이전트 API: http://localhost:8000"
echo "- API 문서: http://localhost:8000/docs"
echo "- 헬스 체크: http://localhost:8000/health"
echo ""
echo "🔍 로그 확인: docker-compose -f docker/agents/docker-compose.yml logs -f integrated_agent"
echo "🛑 중지: docker-compose -f docker/agents/docker-compose.yml down"
