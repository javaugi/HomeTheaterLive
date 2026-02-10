@echo off
echo ========================================
echo Starting HomeTheaterLive Servers
echo ========================================

echo Starting Backend server on port 8000...
start "Backend Server" cmd /k "cd /d %~dp0 && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo Starting Mobile server on port 8001...
start "Mobile Server" cmd /k "cd /d %~dp0 && python -m uvicorn mobile.app.main:app --host 0.0.0.0 --port 8001 --reload"

echo.
echo ========================================
echo Servers Started!
echo Backend: http://localhost:8000
echo Mobile:  http://localhost:8001
echo ========================================
echo.
echo Press any key to close this window...
pause >nul