Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting HomeTheaterLive Servers" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nStarting Backend server on port 8000..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 3

Write-Host "`nStarting Mobile server on port 8001..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn mobile.app.main:app --host 0.0.0.0 --port 8001 --reload"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Servers Started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Mobile:  http://localhost:8001" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop servers" -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*"
    } | Stop-Process -Force
    Write-Host "Servers stopped." -ForegroundColor Green
}