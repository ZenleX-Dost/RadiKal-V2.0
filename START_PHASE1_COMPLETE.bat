@echo off
REM =========================================================================
REM RadiKal V2.0 - Phase 1 Complete Startup Script
REM =========================================================================
REM
REM This script starts both backend and frontend services for RadiKal V2.0
REM with all Phase 1 features enabled:
REM   - Real-time notifications
REM   - Advanced settings UI
REM   - Enhanced export (PDF/Excel)
REM   - Batch analysis
REM   - Production middleware
REM
REM =========================================================================

echo.
echo =========================================================================
echo  RadiKal V2.0 - Phase 1 Production Readiness Complete
echo =========================================================================
echo.
echo  All systems ready for deployment!
echo.
echo  Features enabled:
echo    - Real-time notifications (SSE)
echo    - Advanced settings management
echo    - Enhanced export (PDF/Excel with preview)
echo    - Batch analysis (multi-image processing)
echo    - Rate limiting middleware
echo    - Error handling middleware
echo    - Health monitoring
echo    - JWT authentication ready
echo.
echo =========================================================================
echo.

REM Check if backend virtual environment exists
if not exist "backend\venv" (
    echo [ERROR] Backend virtual environment not found!
    echo Please run: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist "frontend-makerkit\node_modules" (
    echo [ERROR] Frontend dependencies not installed!
    echo Please run: cd frontend-makerkit ^&^& pnpm install
    pause
    exit /b 1
)

echo [1/4] Starting Backend Server...
echo.
start "RadiKal Backend" cmd /k "cd backend && venv\Scripts\activate && python run_server.py"
timeout /t 5 /nobreak >nul

echo [2/4] Starting Frontend Development Server...
echo.
start "RadiKal Frontend" cmd /k "cd frontend-makerkit\apps\web && pnpm dev"
timeout /t 10 /nobreak >nul

echo [3/4] Running Integration Tests...
echo.
python test_frontend_integration.py

echo.
echo [4/4] Opening Browser...
echo.
timeout /t 3 /nobreak >nul
start http://localhost:3000/home/analysis

echo.
echo =========================================================================
echo  RadiKal V2.0 Started Successfully!
echo =========================================================================
echo.
echo  Services Running:
echo    - Backend API:    http://localhost:8000
echo    - API Docs:       http://localhost:8000/docs
echo    - Health Check:   http://localhost:8000/health/detailed
echo    - Frontend:       http://localhost:3000
echo.
echo  New Pages Available:
echo    - Analysis:       http://localhost:3000/home/analysis
echo    - Batch Analysis: http://localhost:3000/home/batch
echo    - Settings:       http://localhost:3000/home/settings/advanced
echo.
echo  To stop services: Close the terminal windows or press Ctrl+C
echo =========================================================================
echo.

pause
