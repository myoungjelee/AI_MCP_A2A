# 🎯 무료 최선 배포 스크립트

Write-Host "🚀 무료 최선 방법: Vercel + ngrok" -ForegroundColor Green

$ProjectPath = "D:\Python\AI_MCP_A2A"

Write-Host "`n1️⃣ 프론트엔드 코드 수정..." -ForegroundColor Yellow
cd "$ProjectPath\frontend"

# 환경변수 사용하도록 코드 수정
Write-Host "📝 app/page.tsx에서 백엔드 URL을 환경변수로 변경하세요:" -ForegroundColor Cyan
Write-Host "const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'" -ForegroundColor White

Write-Host "`n2️⃣ Vercel 배포..." -ForegroundColor Yellow
Write-Host "다음 명령어 실행:" -ForegroundColor Cyan
Write-Host "npx vercel --prod" -ForegroundColor White

Write-Host "`n3️⃣ 면접 당일 사용법:" -ForegroundColor Yellow
Write-Host "1. 백엔드 실행: docker-compose up -d && ollama serve" -ForegroundColor White
Write-Host "2. 백엔드 터널링: ngrok http 8000" -ForegroundColor White  
Write-Host "3. Vercel에서 환경변수 설정: NEXT_PUBLIC_BACKEND_URL" -ForegroundColor White

Write-Host "`n🎯 결과:" -ForegroundColor Green
Write-Host "✅ 고정 프론트엔드 URL (미리 면접관에게 전달 가능)" -ForegroundColor White
Write-Host "✅ 완전 무료" -ForegroundColor White
Write-Host "✅ 전세계 접속" -ForegroundColor White
Write-Host "✅ HTTPS 자동" -ForegroundColor White

pause
