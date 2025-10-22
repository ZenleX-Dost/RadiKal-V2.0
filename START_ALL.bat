@echo off
echo ========================================
echo   RadiKal - Full System Startup
echo ========================================
echo.
echo Starting both Backend and Frontend...
echo.

REM Get the directory where this batch file is located
set "ROOT_DIR=%~dp0"

echo [1/2] Starting Backend Server...
echo Opening new window for backend...
start "RadiKal Backend" cmd /k "cd /d "%ROOT_DIR%backend" && echo ======================================== && echo    RadiKal Backend Server && echo ======================================== && echo. && echo Starting FastAPI with YOLOv8 model... && echo Server will be available at: http://localhost:8000 && echo API Docs: http://localhost:8000/api/docs && echo. && echo Press Ctrl+C to stop the backend && echo ======================================== && echo. && python main.py"

echo.
echo Waiting 10 seconds for backend to initialize...
timeout /t 10 /nobreak > nul

echo.
echo [2/2] Starting Frontend...
echo Opening new window for frontend...
start "RadiKal Frontend" cmd /k "cd /d "%ROOT_DIR%frontend" && echo ======================================== && echo    RadiKal Frontend && echo ======================================== && echo. && echo Installing dependencies (if needed)... && call npm install > nul 2>&1 && echo. && echo Starting Next.js development server... && echo Frontend will be available at: http://localhost:3000 && echo. && echo Your browser will open automatically in 5 seconds... && echo Press Ctrl+C to stop the frontend && echo ======================================== && echo. && timeout /t 5 /nobreak > nul && start http://localhost:3000 && npm run dev"

echo.
echo ========================================
echo   System Startup Complete!
echo ========================================
echo.
echo Two windows have been opened:
echo   1. Backend Server (FastAPI + YOLOv8)
echo   2. Frontend (Next.js)
echo.
echo Services:
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/api/docs
echo   Frontend: http://localhost:3000
echo.
echo Your browser should open automatically.
echo If not, open: http://localhost:3000
echo.
echo To stop the services:
echo   - Press Ctrl+C in each window
echo   - Or close the terminal windows
echo.
echo ========================================
echo.

pause
