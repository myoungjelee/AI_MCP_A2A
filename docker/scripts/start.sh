#!/bin/bash

# AI MCP A2A Docker 서비스 시작 스크립트

set -e

echo "🚀 AI MCP A2A Docker 서비스 시작..."

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

# 환경 변수 파일 확인
if [ ! -f "../.env" ]; then
    log_warning ".env 파일이 없습니다. 기본 환경 변수를 사용합니다."
    log_info "필요한 API 키들을 .env 파일에 설정하세요."
fi

# 기존 컨테이너 정리
log_info "기존 컨테이너 정리 중..."
docker-compose down

# 서비스 시작
log_info "모든 서비스 시작 중..."
docker-compose up -d

# 서비스 상태 확인
log_info "서비스 상태 확인 중..."
sleep 10

# 각 서비스 상태 확인
services=(
    "redis"
    "postgres"
    "macroeconomic_mcp"
    "financial_analysis_mcp"
    "stock_analysis_mcp"
    "naver_news_mcp"
    "tavily_search_mcp"
    "kiwoom_mcp"
    "integrated_agent"
    "prometheus"
    "grafana"
)

for service in "${services[@]}"; do
    status=$(docker-compose ps -q $service)
    if [ -n "$status" ]; then
        container_status=$(docker inspect --format='{{.State.Status}}' $status)
        if [ "$container_status" = "running" ]; then
            log_success "$service: 실행 중"
        else
            log_error "$service: $container_status"
        fi
    else
        log_error "$service: 컨테이너를 찾을 수 없음"
    fi
done

log_success "모든 서비스 시작 완료!"
echo ""
log_info "서비스 접속 정보:"
echo "  - 통합 에이전트 API: http://localhost:8000"
echo "  - 에이전트 API 문서: http://localhost:8000/docs"
echo "  - Grafana 대시보드: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Redis: localhost:6379"
echo "  - PostgreSQL: localhost:5432"
echo ""
log_info "로그 확인: docker-compose logs -f [서비스명]"
log_info "서비스 중지: docker-compose down"
