# Kill process on port 8000, 8001
#Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force

# Or using netstat:
netstat -ano | Select-String :8000 | ForEach-Object { taskkill /F /PID $_.ToString().Split()[-1] }

# For port 8001:
netstat -ano | Select-String :8001 | ForEach-Object { taskkill /F /PID $_.ToString().Split()[-1] }