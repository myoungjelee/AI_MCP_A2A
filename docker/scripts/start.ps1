# AI MCP A2A Docker 서비스 시작 PowerShell 스크립트

Write-Host "🚀 AI MCP A2A Docker 서비스 시작..." -ForegroundColor Green

# Docker 폴더로 이동 (docker-compose.yml 위치)
Set-Location ".."

# 환경 변수 파일 확인
if (-not (Test-Path "../.env")) {
    Write-Host "[WARNING] .env 파일이 없습니다. 기본 환경 변수를 사용합니다." -ForegroundColor Yellow
    Write-Host "[INFO] 필요한 API 키들을 .env 파일에 설정하세요." -ForegroundColor Blue
}

# 기존 컨테이너 정리
Write-Host "[INFO] 기존 컨테이너 정리 중..." -ForegroundColor Blue
docker-compose down

# 서비스 시작
Write-Host "[INFO] 모든 서비스 시작 중..." -ForegroundColor Blue
docker-compose up -d

# 서비스 상태 확인
Write-Host "[INFO] 서비스 상태 확인 중..." -ForegroundColor Blue
Start-Sleep -Seconds 10

# 각 서비스 상태 확인
$services = @(
    "redis",
    "postgres",
    "macroeconomic_mcp",
    "financial_analysis_mcp",
    "stock_analysis_mcp",
    "naver_news_mcp",
    "tavily_search_mcp",
    "kiwoom_mcp",
    "integrated_agent",
    "prometheus",
    "grafana"
)

foreach ($service in $services) {
    $status = docker-compose ps -q $service
    if ($status) {
        $container_status = docker inspect --format='{{.State.Status}}' $status
        if ($container_status -eq "running") {
            Write-Host "[SUCCESS] $service`: 실행 중" -ForegroundColor Green
        }
        else {
            Write-Host "[ERROR] $service`: $container_status" -ForegroundColor Red
        }
    }
    else {
        Write-Host "[ERROR] $service`: 컨테이너를 찾을 수 없음" -ForegroundColor Red
    }
}

Write-Host "[SUCCESS] 모든 서비스 시작 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] 서비스 접속 정보:" -ForegroundColor Blue
Write-Host "  - 통합 에이전트 API: http://localhost:8000" -ForegroundColor White
Write-Host "  - 에이전트 API 문서: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Grafana 대시보드: http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  - Redis: localhost:6379" -ForegroundColor White
Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] 로그 확인: docker-compose logs -f [서비스명]" -ForegroundColor Blue
Write-Host "[INFO] 서비스 중지: docker-compose down" -ForegroundColor Blue
