# 🎯 고정 URL 면접 시연 스크립트

param(
    [string]$BackendNgrokUrl = ""  # ngrok에서 받은 백엔드 URL
)

Write-Host "🎯 고정 URL 면접 시연 시작" -ForegroundColor Green

$ProjectPath = "D:\Python\AI_MCP_A2A"
$FrontendUrl = "https://ai-mcp-a2a.vercel.app"  # 배포 후 실제 URL로 변경

Write-Host "`n📱 접속 정보:" -ForegroundColor Yellow
Write-Host "프론트엔드 (고정): $FrontendUrl" -ForegroundColor Cyan
Write-Host "백엔드 (동적): $BackendNgrokUrl" -ForegroundColor Cyan

# 1. 백엔드 실행
Write-Host "`n⚙️ 1. 백엔드 서비스 실행..." -ForegroundColor Yellow
cd $ProjectPath
docker-compose up -d
Start-Sleep -Seconds 30

# 2. Ollama 실행
Write-Host "`n🧠 2. Ollama 실행..." -ForegroundColor Yellow
Start-Process -WindowStyle Hidden -FilePath "ollama" -ArgumentList "serve"
Start-Sleep -Seconds 15

# 3. 백엔드 상태 확인
Write-Host "`n🔍 3. 백엔드 상태 확인..." -ForegroundColor Yellow
try {
    $Health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "✅ 백엔드 정상 동작" -ForegroundColor Green
}
catch {
    Write-Host "❌ 백엔드 오류" -ForegroundColor Red
    exit 1
}

# 4. ngrok 터널링 (백엔드만)
Write-Host "`n🌐 4. 백엔드 터널링 시작..." -ForegroundColor Yellow
Write-Host "새 터미널에서 실행하세요:" -ForegroundColor Cyan
Write-Host "ngrok http 8000" -ForegroundColor White

Write-Host "`n⏳ ngrok URL을 받으면 다음 명령어로 재실행:" -ForegroundColor Yellow
Write-Host ".\interview_with_fixed_url.ps1 -BackendNgrokUrl 'https://xxx.ngrok.io'" -ForegroundColor Cyan

if ($BackendNgrokUrl) {
    Write-Host "`n🎯 최종 설정:" -ForegroundColor Green
    Write-Host "프론트엔드: $FrontendUrl" -ForegroundColor Cyan
    Write-Host "백엔드: $BackendNgrokUrl" -ForegroundColor Cyan
    
    Write-Host "`n📋 면접 진행:" -ForegroundColor Yellow
    Write-Host "1. 면접관에게 프론트엔드 URL 전달: $FrontendUrl" -ForegroundColor White
    Write-Host "2. 백엔드 환경변수는 자동으로 $BackendNgrokUrl 사용" -ForegroundColor White
    Write-Host "3. 어디서든 접속 가능한 고정 URL 시연" -ForegroundColor White
    
    # URL을 클립보드에 복사
    $FrontendUrl | Set-Clipboard
    Write-Host "`n📋 프론트엔드 URL이 클립보드에 복사되었습니다" -ForegroundColor Green
}

Write-Host "`n✨ 장점:" -ForegroundColor Green
Write-Host "✅ 고정 URL - 미리 면접관에게 전달 가능" -ForegroundColor White
Write-Host "✅ 전세계 접속 - 어떤 네트워크에서든 OK" -ForegroundColor White
Write-Host "✅ HTTPS 자동 - 보안 연결" -ForegroundColor White
Write-Host "✅ 무료 호스팅 - 비용 부담 없음" -ForegroundColor White

pause

