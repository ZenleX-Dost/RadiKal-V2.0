@echo off
echo ========================================
echo  RadiKal XAI Quality Control - Starter
echo  Makerkit Frontend + FastAPI Backend
echo ========================================
echo.

REM Kill any existing processes on ports 3000 and 8000
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo Starting Backend (FastAPI)...
start "RadiKal Backend" cmd /k "cd /d "%~dp0backend" && python run_server.py"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Starting Frontend (Makerkit)...
start "RadiKal Frontend" cmd /k "cd /d "%~dp0frontend-makerkit\apps\web" && pnpm run dev"

echo.
echo ========================================
echo  RadiKal is starting up!
echo ========================================
echo.
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/api/docs
echo.
echo  Press any key to open browser...
pause >nul

start http://localhost:3000

echo.
echo RadiKal is now running!
echo Close this window to keep services running.
echo To stop services, close the Backend and Frontend windows.
echo.
