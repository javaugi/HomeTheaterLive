# Find and kill process on port 8000, 8001
#netstat -ano | findstr :8000
#taskkill /F /PID <PID>

# Or one-liner:
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a

# For port 8001:
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %a