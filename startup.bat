@echo off
echo ======================================
echo AI MCP A2A 시스템 자동 시작
echo ======================================

cd /d "D:\Python\AI_MCP_A2A"

echo [1/4] Ollama 서버 시작 중...
start /min cmd /c "ollama serve"
timeout /t 10

echo [2/4] Docker Desktop 시작 중...
echo Docker Desktop을 시작합니다...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
timeout /t 30

echo Docker Desktop 준비 대기 중...
:docker_wait_loop
docker info > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker Desktop 준비 완료!
    goto start_compose
)
echo ⏳ Docker Desktop 대기 중... (10초 후 재시도)
timeout /t 10
goto docker_wait_loop

:start_compose
echo [3/4] Docker 서비스들 시작 중...
start /min cmd /c "cd /d "D:\Python\AI_MCP_A2A\docker" && docker-compose up --build"
timeout /t 60

echo [4/4] 서비스 상태 확인 중...
:wait_loop
curl -s http://localhost:8000/health > nul
if %errorlevel% equ 0 (
    echo ✅ 백엔드 서비스 준비 완료!
    goto start_tunnel
)
echo ⏳ 백엔드 서비스 대기 중... (10초 후 재시도)
timeout /t 10
goto wait_loop

:start_tunnel
echo [5/5] Cloudflare 터널 시작 중...
echo 백엔드 터널 URL: https://ai-mcp-a2a-backend.duckdns.org
start /min cmd /c ""C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel run ai-mcp-a2a-backend"
timeout /t 10

echo ======================================
echo 🎉 시스템 시작 완료!
echo 프론트엔드: https://your-vercel-app.vercel.app
echo 백엔드: https://ai-mcp-a2a-backend.duckdns.org
echo 로컬 백엔드: http://localhost:8000
echo ======================================
pause
