#!/bin/bash

# AI MCP A2A Docker 서비스 중지 스크립트

set -e

echo "🛑 AI MCP A2A Docker 서비스 중지..."

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

# Docker 폴더로 이동 (docker-compose.yml 위치)
cd ..

# 서비스 중지
log_info "모든 서비스 중지 중..."
docker-compose down

log_success "모든 서비스 중지 완료!"

# 선택적: 볼륨도 함께 삭제
read -p "볼륨도 함께 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "볼륨 삭제 중..."
    docker-compose down -v
    log_success "볼륨 삭제 완료!"
fi

# 선택적: 이미지도 함께 삭제
read -p "Docker 이미지도 함께 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Docker 이미지 삭제 중..."
    docker-compose down --rmi all
    log_success "Docker 이미지 삭제 완료!"
fi

log_info "시스템 정리 완료!"
