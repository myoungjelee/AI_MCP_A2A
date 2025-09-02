# AI MCP A2A 통합 에이전트 Docker 빌드 스크립트 (PowerShell)

Write-Host "🐳 AI MCP A2A 통합 에이전트 Docker 빌드 시작..." -ForegroundColor Green

# 프로젝트 루트로 이동
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptPath "../.."
Set-Location $projectRoot

Write-Host "📁 현재 작업 디렉토리: $(Get-Location)" -ForegroundColor Blue

# 기존 컨테이너 정리
Write-Host "🧹 기존 컨테이너 정리..." -ForegroundColor Yellow
try {
    docker-compose -f docker/agents/docker-compose.yml down --remove-orphans
}
catch {
    Write-Host "기존 컨테이너가 없거나 정리 중 오류 발생 (정상)" -ForegroundColor Gray
}

# Docker 이미지 빌드
Write-Host "🔨 Docker 이미지 빌드 중..." -ForegroundColor Blue
docker-compose -f docker/agents/docker-compose.yml build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker 이미지 빌드 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker 이미지 빌드 완료!" -ForegroundColor Green

# 컨테이너 시작
Write-Host "🚀 컨테이너 시작 중..." -ForegroundColor Blue
docker-compose -f docker/agents/docker-compose.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 컨테이너 시작 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "⏳ 서비스 시작 대기 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 헬스 체크
Write-Host "🏥 헬스 체크 중..." -ForegroundColor Blue
Write-Host "- 통합 에이전트: http://localhost:8000/health"

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 통합 에이전트 헬스 체크 성공" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ 통합 에이전트 응답 코드: $($response.StatusCode)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ 통합 에이전트 헬스 체크 실패: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 실행 중인 컨테이너:" -ForegroundColor Blue
docker-compose -f docker/agents/docker-compose.yml ps

Write-Host ""
Write-Host "🎉 AI MCP A2A 통합 에이전트 Docker 빌드 및 실행 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 접속 정보:" -ForegroundColor Cyan
Write-Host "- 통합 에이전트 API: http://localhost:8000" -ForegroundColor White
Write-Host "- API 문서: http://localhost:8000/docs" -ForegroundColor White
Write-Host "- 헬스 체크: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "🔍 로그 확인: docker-compose -f docker/agents/docker-compose.yml logs -f integrated_agent" -ForegroundColor Yellow
Write-Host "🛑 중지: docker-compose -f docker/agents/docker-compose.yml down" -ForegroundColor Yellow
