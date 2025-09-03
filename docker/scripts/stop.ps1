# AI MCP A2A Docker 서비스 중지 PowerShell 스크립트

Write-Host "🛑 AI MCP A2A Docker 서비스 중지..." -ForegroundColor Yellow

# Docker 폴더로 이동 (docker-compose.yml 위치)
Set-Location ".."

# 서비스 중지
Write-Host "[INFO] 모든 서비스 중지 중..." -ForegroundColor Blue
docker-compose down

Write-Host "[SUCCESS] 모든 서비스 중지 완료!" -ForegroundColor Green

# 선택적: 볼륨도 함께 삭제
$removeVolumes = Read-Host "볼륨도 함께 삭제하시겠습니까? (y/N)"
if ($removeVolumes -eq "y" -or $removeVolumes -eq "Y") {
    Write-Host "[INFO] 볼륨 삭제 중..." -ForegroundColor Blue
    docker-compose down -v
    Write-Host "[SUCCESS] 볼륨 삭제 완료!" -ForegroundColor Green
}

# 선택적: 이미지도 함께 삭제
$removeImages = Read-Host "Docker 이미지도 함께 삭제하시겠습니까? (y/N)"
if ($removeImages -eq "y" -or $removeImages -eq "Y") {
    Write-Host "[INFO] Docker 이미지 삭제 중..." -ForegroundColor Blue
    docker-compose down --rmi all
    Write-Host "[SUCCESS] Docker 이미지 삭제 완료!" -ForegroundColor Green
}

Write-Host "[INFO] 시스템 정리 완료!" -ForegroundColor Blue
