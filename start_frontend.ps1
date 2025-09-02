# AI MCP A2A 프론트엔드 시작 스크립트
# 사용법: .\start_frontend.ps1

Write-Host "💻 프론트엔드 시작..." -ForegroundColor Green

# 1. 프론트엔드 디렉토리로 이동
if (-not (Test-Path "frontend")) {
    Write-Host "❌ frontend 디렉토리를 찾을 수 없습니다." -ForegroundColor Red
    exit 1
}

Set-Location frontend

# 2. 의존성 설치 확인
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 의존성 설치 중..." -ForegroundColor Yellow
    npm install
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install 실패" -ForegroundColor Red
        exit 1
    }
}

# 3. 개발 서버 시작
Write-Host "🚀 개발 서버 시작 중..." -ForegroundColor Yellow
Write-Host "📱 프론트엔드: http://localhost:3001" -ForegroundColor Cyan
Write-Host "Ctrl+C로 종료할 수 있습니다." -ForegroundColor Gray

npm run dev
