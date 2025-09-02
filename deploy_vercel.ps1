# 🚀 Vercel 배포 스크립트 (고정 URL)

Write-Host "🌐 Vercel 배포 시작" -ForegroundColor Green

$ProjectPath = "D:\Python\AI_MCP_A2A"
cd "$ProjectPath\frontend"

Write-Host "`n📦 1. 프론트엔드 설정 수정..." -ForegroundColor Yellow

# Next.js 설정 파일 생성 (정적 사이트용)
$NextConfigContent = @"
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000'
  },
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  }
}

module.exports = nextConfig
"@

$NextConfigContent | Out-File -FilePath "next.config.js" -Encoding UTF8
Write-Host "✅ next.config.js 생성 완료"

Write-Host "`n🔧 2. 빌드 테스트..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 빌드 성공" -ForegroundColor Green
}
else {
    Write-Host "❌ 빌드 실패" -ForegroundColor Red
    exit 1
}

Write-Host "`n🚀 3. Vercel 배포..." -ForegroundColor Yellow
Write-Host "다음 명령어를 실행하세요:" -ForegroundColor Cyan
Write-Host ""
Write-Host "npx vercel --prod" -ForegroundColor White
Write-Host ""
Write-Host "배포 후 받게 될 URL 예시:" -ForegroundColor Yellow
Write-Host "https://ai-mcp-a2a-username.vercel.app" -ForegroundColor Cyan

Write-Host "`n📋 면접 사용법:" -ForegroundColor Green
Write-Host "1. 위 명령어로 배포 → 고정 URL 획득" -ForegroundColor White
Write-Host "2. 면접 시 백엔드만 ngrok으로 터널링" -ForegroundColor White
Write-Host "3. 환경변수로 백엔드 URL 연결" -ForegroundColor White

pause
