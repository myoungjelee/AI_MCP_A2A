@echo off
chcp 65001 >nul 2>&1
cls
echo ======================================
echo AI MCP A2A System Auto Startup
echo ======================================

REM 0. Change working directory
cd /d "D:\Python\AI_MCP_A2A"

REM 1. Start Ollama server (background)
echo [1/3] Starting Ollama Server...
start "" /min cmd /c "ollama serve >nul 2>&1"
timeout /t 5 >nul

REM 2. Wait for Backend API (max 30s)
echo [2/3] Waiting for Backend API (http://localhost:8000)...
set /a counter=0

:wait_backend
curl -s http://localhost:8000 >nul 2>&1
if %errorlevel% equ 0 goto backend_ready

set /a counter+=1
if %counter% geq 30 (
    echo [WARNING] Backend API not responding after 30 seconds.
    echo Proceeding to start Cloudflare Tunnel anyway...
    goto start_tunnel
)

timeout /t 1 >nul
goto wait_backend

:backend_ready
echo [OK] Backend API is responding!

:start_tunnel
echo.
echo [3/3] Starting Cloudflare Tunnel...
echo (Tunnel logs will be shown in this window)
echo --------------------------------------
cloudflared tunnel run ai-mcp-a2a-backend
echo --------------------------------------
echo [Tunnel process exited]

echo.
echo ======================================
echo Frontend : https://ai-mcp-a2a.vercel.app
echo Backend  : http://localhost:8000
echo Public   : https://ai-mcp-a2a-backend.xyz
echo ======================================
pause
