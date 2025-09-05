@echo off
chcp 65001 >nul 2>&1
cls
echo ======================================
echo AI MCP A2A System Auto Startup
echo ======================================

cd /d "D:\Python\AI_MCP_A2A"

echo [1/2] Starting Ollama Server...
start /min cmd /c "ollama serve"
timeout /t 10

:start_tunnels
echo [2/2] Starting Pinggy Tunnel...
REM TODO: eu.org 도메인 나오면 Cloudflare Tunnel로 전환

echo Pinggy Public URL: https://uexkl-175-113-49-154.a.free.pinggy.link
echo Access Token: z0Mt4RGjye (starting in background...)

REM Create temporary VBScript for silent execution
echo Set WshShell = CreateObject("WScript.Shell") > %temp%\pinggy_silent.vbs
echo WshShell.Run "cmd /c echo z0Mt4RGjye | ssh -p 443 -R0:127.0.0.1:8000 -L4300:127.0.0.1:4300 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 z0Mt4RGjye@free.pinggy.io", 0, False >> %temp%\pinggy_silent.vbs

REM Execute silently
cscript //nologo %temp%\pinggy_silent.vbs

REM Clean up
del %temp%\pinggy_silent.vbs

timeout /t 10

echo ======================================
echo [SUCCESS] System Startup Complete!
echo ======================================
echo Frontend: https://ai-mcp-a2a.vercel.app
echo Backend API: https://uexkl-175-113-49-154.a.free.pinggy.link
echo Local Backend: http://localhost:8000
echo ======================================
echo NOTE: Pinggy tunnel running silently in background!
echo ======================================
echo Ready URLs:
echo - Frontend: https://ai-mcp-a2a.vercel.app
echo - API: https://uexkl-175-113-49-154.a.free.pinggy.link
echo ======================================
pause
