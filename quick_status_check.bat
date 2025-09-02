@echo off
title 시스템 상태 확인

echo 📊 AI MCP A2A 시스템 상태 확인
echo.

:: 프로젝트 경로로 이동
cd /d "D:\Python\AI_MCP_A2A"

echo 📄 최근 로그:
echo ═══════════════════════════════
if exist auto_startup.log (
    powershell -Command "Get-Content auto_startup.log | Select-Object -Last 5"
) else (
    echo 로그 파일 없음
)
echo.

echo 🌐 백엔드 외부 URL:
echo ═══════════════════════════════
if exist backend_url.txt (
    type backend_url.txt
    echo.
    echo 📋 URL 클립보드 복사 중...
    powershell -Command "Get-Content backend_url.txt | Set-Clipboard"
    echo ✅ 클립보드에 복사 완료
) else (
    echo URL 파일 없음
)
echo.

echo ⚙️ Docker 컨테이너 상태:
echo ═══════════════════════════════
docker ps --format "table {{.Names}}\t{{.Status}}"
echo.

echo 🔍 서비스 상태 확인:
echo ═══════════════════════════════

:: 백엔드 확인
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ 백엔드: 오프라인
) else (
    echo ✅ 백엔드: 정상
)

:: ngrok 확인
curl -s http://localhost:4040/api/tunnels >nul 2>&1
if errorlevel 1 (
    echo ❌ ngrok: 오프라인
) else (
    echo ✅ ngrok: 정상
)

echo.
echo 📱 면접 체크리스트:
echo ✓ Vercel 프론트엔드: https://ai-mcp-a2a.vercel.app
echo ✓ 백엔드 URL: backend_url.txt 확인
echo ✓ 환경변수 설정: Vercel에서 NEXT_PUBLIC_BACKEND_URL 설정
echo.

pause
