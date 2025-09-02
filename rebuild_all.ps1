무조저# AI MCP A2A 전체 시스템 재빌드 스크립트
# 사용법: .\rebuild_all.ps1

Write-Host "🚀 AI MCP A2A 전체 시스템 재빌드 시작..." -ForegroundColor Green

# 1. 기존 컨테이너 및 이미지 정리
Write-Host "📦 기존 컨테이너 및 이미지 정리 중..." -ForegroundColor Yellow
docker compose down --rmi all --volumes --remove-orphans

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker down 실패" -ForegroundColor Red
    exit 1
}

# 2. 전체 이미지 재빌드 (캐시 없이)
Write-Host "🔨 전체 이미지 재빌드 중 (캐시 없이)..." -ForegroundColor Yellow
docker compose build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build 실패" -ForegroundColor Red
    exit 1
}

# 3. 전체 서비스 시작
Write-Host "🚀 전체 서비스 시작 중..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker up 실패" -ForegroundColor Red
    exit 1
}

# 4. 잠시 대기 후 상태 확인
Write-Host "⏳ 서비스 초기화 대기 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 5. 컨테이너 상태 확인
Write-Host "📊 컨테이너 상태 확인..." -ForegroundColor Yellow
docker compose ps

# 6. 통합 에이전트 로그 확인
Write-Host "📝 통합 에이전트 최근 로그..." -ForegroundColor Yellow
docker compose logs --tail=20 integrated_agent

# 7. MCP 상태 확인
Write-Host "🔗 MCP 서버 연결 상태 확인..." -ForegroundColor Yellow
try {
    $mcpStatus = curl.exe -s http://localhost:8000/mcp/status | ConvertFrom-Json
    Write-Host "연결된 MCP 서버: $($mcpStatus.connected_count)/$($mcpStatus.total_count)" -ForegroundColor Cyan
    
    if ($mcpStatus.connected_count -gt 0) {
        Write-Host "연결된 서버: $($mcpStatus.connected_servers -join ', ')" -ForegroundColor Green
    }
    
    if ($mcpStatus.disconnected_servers.Count -gt 0) {
        Write-Host "연결 끊어진 서버: $($mcpStatus.disconnected_servers -join ', ')" -ForegroundColor Red
    }
}
catch {
    Write-Host "⚠️ MCP 상태 확인 실패 (서비스 시작 중일 수 있음)" -ForegroundColor Yellow
}

Write-Host "✅ 전체 시스템 재빌드 완료!" -ForegroundColor Green
Write-Host "📱 프론트엔드: http://localhost:3001" -ForegroundColor Cyan
Write-Host "🤖 백엔드 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 Grafana: http://localhost:3000" -ForegroundColor Cyan
