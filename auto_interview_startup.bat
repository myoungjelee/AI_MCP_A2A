@echo off
title AI MCP A2A 자동 면접 시스템

echo 🚀 AI MCP A2A 자동 면접 시스템 시작
echo.

:: 프로젝트 경로로 이동
cd /d "D:\Python\AI_MCP_A2A"

:: 로그 파일 초기화
echo %date% %time% - 자동 시작 시작 > auto_startup.log

:: 1. Docker Desktop 실행 대기
echo ⏳ Docker Desktop 준비 대기 중...
:wait_docker
timeout /t 10 /nobreak >nul
docker version >nul 2>&1
if errorlevel 1 (
    echo Docker 대기 중...
    goto wait_docker
)
echo ✅ Docker Desktop 준비 완료
echo %date% %time% - Docker 준비 완료 >> auto_startup.log

:: 2. Ollama 백그라운드 실행
echo 🧠 Ollama 서버 시작...
start /min ollama serve
timeout /t 15 /nobreak >nul
echo %date% %time% - Ollama 시작 >> auto_startup.log

:: 3. 백엔드 서비스 실행
echo ⚙️ 백엔드 서비스 시작...
docker-compose up -d
timeout /t 30 /nobreak >nul
echo %date% %time% - 백엔드 서비스 시작 >> auto_startup.log

:: 4. 백엔드 헬스체크
echo 🔍 백엔드 상태 확인...
curl -s http://localhost:8000/health >nul
if errorlevel 1 (
    echo ❌ 백엔드 오류
    pause
    exit /b 1
)
echo ✅ 백엔드 정상 작동
echo %date% %time% - 백엔드 헬스체크 성공 >> auto_startup.log

:: 5. ngrok 터널링 (새 창에서)
echo 🌐 백엔드 터널링 시작...
start "ngrok-backend" ngrok http 8000
timeout /t 10 /nobreak >nul

:: 6. ngrok URL 추출 및 저장
echo 📋 외부 접속 URL 추출 중...
powershell -Command "try { $api = Invoke-RestMethod 'http://localhost:4040/api/tunnels'; $url = $api.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -ExpandProperty public_url; if($url) { $url | Out-File 'backend_url.txt' -Encoding UTF8; Write-Host \"✅ 백엔드 URL: $url\"; $url | Set-Clipboard; Write-Host \"📋 URL이 클립보드에 복사됨\" } } catch { Write-Host \"⚠️ URL 추출 실패\" }"

:: 7. 완료 메시지
echo.
echo 🎉 자동 시작 완료!
echo.
echo 📱 면접 준비 완료:
echo ✅ 프론트엔드: https://ai-mcp-a2a.vercel.app (고정 URL)
echo ✅ 백엔드: backend_url.txt 파일 확인
echo ✅ 시스템: 완전 가동 중
echo.
echo 📋 면접 진행:
echo 1. 면접관에게 Vercel URL 전달
echo 2. Vercel 환경변수에 backend_url.txt 내용 설정
echo 3. 외부에서 접속 테스트
echo.

:: 로그 저장
echo %date% %time% - 자동 시작 완료 >> auto_startup.log

:: 상태 모니터링 창 열기
start "상태 모니터링" cmd /k "echo 📊 시스템 상태 모니터링 && echo. && docker ps && echo. && echo 백엔드 URL: && type backend_url.txt 2>nul || echo URL 파일 없음"

pause
