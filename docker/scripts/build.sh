#!/bin/bash

# AI MCP A2A Docker 이미지 빌드 스크립트

set -e

echo "🚀 AI MCP A2A Docker 이미지 빌드 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 변수 파일 확인
if [ ! -f "../../.env" ]; then
    log_warning ".env 파일이 없습니다. 기본 환경 변수를 사용합니다."
    log_info "필요한 API 키들을 .env 파일에 설정하세요."
fi

# Docker 폴더로 이동 (docker-compose.yml 위치)
cd ..

# Docker Compose 빌드
log_info "Docker Compose로 모든 서비스 빌드 중..."

# MCP 서버들 빌드
log_info "MCP 서버 이미지 빌드 중..."
docker-compose build macroeconomic_mcp
docker-compose build financial_analysis_mcp
docker-compose build stock_analysis_mcp
docker-compose build naver_news_mcp
docker-compose build tavily_search_mcp
docker-compose build kiwoom_mcp

# 에이전트 빌드
log_info "통합 에이전트 이미지 빌드 중..."
docker-compose build integrated_agent

log_success "모든 Docker 이미지 빌드 완료!"
log_info "다음 명령어로 서비스를 시작할 수 있습니다:"
echo "  docker-compose up -d"
