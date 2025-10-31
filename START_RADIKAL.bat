@echo off
title RadiKal Startup
color 0B
cls

echo.
echo ========================================
echo.
echo           R A D I K A L
echo.
echo    AI-Powered Weld Defect Detection
echo.
echo ========================================
echo.
echo  Starting services...
echo.

REM Get the directory where this batch file is located
set "ROOT_DIR=%~dp0"

echo  [1/3] Starting Backend Server...
echo         Please wait...
start /B "" cmd /c "cd /d "%ROOT_DIR%backend" && python main.py > nul 2>&1"

echo.
echo  [2/3] Waiting for backend to initialize...
timeout /t 8 /nobreak > nul
echo         Backend ready!

echo.
echo  [3/3] Starting Frontend Server...
echo         Please wait...
start /B "" cmd /c "cd /d "%ROOT_DIR%frontend-makerkit\apps\web" && pnpm dev > nul 2>&1"

echo.
echo  Waiting for frontend to initialize...
timeout /t 8 /nobreak > nul
echo         Frontend ready!

echo.
echo ========================================
echo.
echo      RadiKal is now running!
echo.
echo ========================================
echo.
echo  Services:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/api/docs
echo.
echo  Opening browser in 3 seconds...
timeout /t 3 /nobreak > nul

start http://localhost:3000

echo.
echo ========================================
echo.
echo  To stop RadiKal:
echo    - Run STOP_ALL.ps1
echo    - Or close this window and kill processes
echo.
echo  Press any key to keep this window open
echo  (Services will continue running)
echo.
pause > nul

cls
echo.
echo ========================================
echo    RadiKal is running in background
echo ========================================
echo.
echo  Services are active at:
echo    http://localhost:3000
echo    http://localhost:8000
echo.
echo  To stop: Run STOP_ALL.ps1
echo.
echo  You can now close this window safely.
echo  Services will continue running.
echo.
pause
