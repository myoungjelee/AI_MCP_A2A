# AI MCP A2A 통합 에이전트만 재빌드 스크립트
# 사용법: .\rebuild_agent.ps1

Write-Host "🤖 통합 에이전트 재빌드 시작..." -ForegroundColor Green

# 1. 에이전트 컨테이너 중지 및 제거
Write-Host "⏹️ 기존 에이전트 컨테이너 중지 및 제거..." -ForegroundColor Yellow
docker compose stop integrated_agent
docker compose rm -f integrated_agent

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ 컨테이너 중지/제거 중 오류 (계속 진행)" -ForegroundColor Yellow
}

# 2. 에이전트 이미지만 재빌드 (캐시 없이)
Write-Host "🔨 에이전트 이미지 재빌드 중 (캐시 없이)..." -ForegroundColor Yellow
docker compose build --no-cache integrated_agent

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 에이전트 빌드 실패" -ForegroundColor Red
    exit 1
}

# 3. 에이전트 서비스 시작
Write-Host "🚀 에이전트 서비스 시작..." -ForegroundColor Yellow
docker compose up -d integrated_agent

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 에이전트 시작 실패" -ForegroundColor Red
    exit 1
}

# 4. 잠시 대기 후 상태 확인
Write-Host "⏳ 에이전트 초기화 대기 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# 5. 컨테이너 상태 확인
Write-Host "📊 전체 컨테이너 상태..." -ForegroundColor Yellow
docker compose ps

# 6. 에이전트 로그 확인
Write-Host "📝 에이전트 최근 로그..." -ForegroundColor Yellow
docker compose logs --tail=30 integrated_agent

# 7. 헬스체크 확인
Write-Host "🏥 에이전트 헬스체크..." -ForegroundColor Yellow
try {
    $health = curl.exe -s http://localhost:8000/health
    Write-Host "헬스체크 응답: $health" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ 헬스체크 실패" -ForegroundColor Red
}

# 8. MCP 상태 확인
Write-Host "🔗 MCP 서버 연결 상태 확인..." -ForegroundColor Yellow
try {
    $mcpStatus = curl.exe -s http://localhost:8000/mcp/status | ConvertFrom-Json
    Write-Host "연결된 MCP 서버: $($mcpStatus.connected_count)/$($mcpStatus.total_count)" -ForegroundColor Cyan
    
    if ($mcpStatus.connected_count -gt 0) {
        Write-Host "✅ 연결된 서버: $($mcpStatus.connected_servers -join ', ')" -ForegroundColor Green
    }
    
    if ($mcpStatus.disconnected_servers.Count -gt 0) {
        Write-Host "❌ 연결 끊어진 서버: $($mcpStatus.disconnected_servers -join ', ')" -ForegroundColor Red
    }
    
    Write-Host "🛠️ 사용 가능한 도구: $($mcpStatus.available_tools)개" -ForegroundColor Cyan
}
catch {
    Write-Host "⚠️ MCP 상태 확인 실패 (서비스 시작 중일 수 있음)" -ForegroundColor Yellow
}

Write-Host "✅ 에이전트 재빌드 완료!" -ForegroundColor Green
Write-Host "🤖 에이전트 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📊 MCP 상태: http://localhost:8000/mcp/status" -ForegroundColor Cyan
