# AI MCP A2A Docker 이미지 빌드 PowerShell 스크립트

Write-Host "🚀 AI MCP A2A Docker 이미지 빌드 시작..." -ForegroundColor Green

# 환경 변수 파일 확인
if (-not (Test-Path "../../.env")) {
    Write-Host "[WARNING] .env 파일이 없습니다. 기본 환경 변수를 사용합니다." -ForegroundColor Yellow
    Write-Host "[INFO] 필요한 API 키들을 .env 파일에 설정하세요." -ForegroundColor Blue
}

# 프로젝트 루트로 이동
Set-Location "../.."

# Docker Compose 빌드
Write-Host "[INFO] Docker Compose로 모든 서비스 빌드 중..." -ForegroundColor Blue

# MCP 서버들 빌드
Write-Host "[INFO] MCP 서버 이미지 빌드 중..." -ForegroundColor Blue
docker-compose build macroeconomic_mcp
docker-compose build financial_analysis_mcp
docker-compose build stock_analysis_mcp
docker-compose build naver_news_mcp
docker-compose build tavily_search_mcp
docker-compose build kiwoom_mcp

# 에이전트 빌드
Write-Host "[INFO] 통합 에이전트 이미지 빌드 중..." -ForegroundColor Blue
docker-compose build integrated_agent

Write-Host "[SUCCESS] 모든 Docker 이미지 빌드 완료!" -ForegroundColor Green
Write-Host "[INFO] 다음 명령어로 서비스를 시작할 수 있습니다:" -ForegroundColor Blue
Write-Host "  docker-compose up -d" -ForegroundColor White
