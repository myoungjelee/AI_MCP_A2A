@echo off
title 자동 시작 설정

echo 🔧 AI MCP A2A 자동 시작 설정
echo.

:: 현재 경로
set PROJECT_PATH=%~dp0
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

echo 📁 설정 정보:
echo 프로젝트 경로: %PROJECT_PATH%
echo 시작프로그램 폴더: %STARTUP_FOLDER%
echo.

:: 시작프로그램용 배치 파일 생성
echo @echo off > "%STARTUP_FOLDER%\AI_MCP_A2A_AutoStart.bat"
echo cd /d "%PROJECT_PATH%" >> "%STARTUP_FOLDER%\AI_MCP_A2A_AutoStart.bat"
echo start /min auto_interview_startup.bat >> "%STARTUP_FOLDER%\AI_MCP_A2A_AutoStart.bat"

echo ✅ 시작프로그램 등록 완료
echo 파일 위치: %STARTUP_FOLDER%\AI_MCP_A2A_AutoStart.bat
echo.

echo 🐳 Docker Desktop 자동 시작 설정:
echo 1. Docker Desktop 실행
echo 2. 설정(Settings) → General
echo 3. "Start Docker Desktop when you log in" 체크
echo.

echo 📋 사용법:
echo 1. 재부팅 시 자동으로 모든 시스템 실행
echo 2. backend_url.txt 파일에서 ngrok URL 확인
echo 3. Vercel 환경변수에 해당 URL 설정
echo 4. 면접 진행!
echo.

echo 🧪 지금 테스트하시겠습니까? (Y/N)
choice /c yn /n
if errorlevel 2 goto end
if errorlevel 1 call auto_interview_startup.bat

:end
pause
