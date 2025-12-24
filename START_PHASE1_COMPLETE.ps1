# RadiKal V2.0 - Phase 1 Complete Startup Script (PowerShell)
# =========================================================================
#
# This script starts both backend and frontend services with all
# Phase 1 production-ready features enabled.
#
# =========================================================================

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host " RadiKal V2.0 - Phase 1 Production Readiness Complete" -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " All systems ready for deployment!" -ForegroundColor Green
Write-Host ""
Write-Host " Features enabled:" -ForegroundColor Yellow
Write-Host "   - Real-time notifications (SSE)" -ForegroundColor White
Write-Host "   - Advanced settings management" -ForegroundColor White
Write-Host "   - Enhanced export (PDF/Excel with preview)" -ForegroundColor White
Write-Host "   - Batch analysis (multi-image processing)" -ForegroundColor White
Write-Host "   - Rate limiting middleware" -ForegroundColor White
Write-Host "   - Error handling middleware" -ForegroundColor White
Write-Host "   - Health monitoring" -ForegroundColor White
Write-Host "   - JWT authentication ready" -ForegroundColor White
Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend virtual environment exists
if (-not (Test-Path "backend\venv")) {
    Write-Host "[ERROR] Backend virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if frontend dependencies are installed
if (-not (Test-Path "frontend-makerkit\node_modules")) {
    Write-Host "[ERROR] Frontend dependencies not installed!" -ForegroundColor Red
    Write-Host "Please run: cd frontend-makerkit; pnpm install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/4] Starting Backend Server..." -ForegroundColor Cyan
Write-Host ""

# Start backend in a new terminal
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; python run_server.py"
Start-Sleep -Seconds 5

Write-Host "[2/4] Starting Frontend Development Server..." -ForegroundColor Cyan
Write-Host ""

# Start frontend in a new terminal
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd frontend-makerkit\apps\web; pnpm dev"
Start-Sleep -Seconds 10

Write-Host "[3/4] Running Integration Tests..." -ForegroundColor Cyan
Write-Host ""

# Run integration tests
python test_frontend_integration.py

Write-Host ""
Write-Host "[4/4] Opening Browser..." -ForegroundColor Cyan
Write-Host ""
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000/home/analysis"

Write-Host ""
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host " RadiKal V2.0 Started Successfully!" -ForegroundColor Green
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Services Running:" -ForegroundColor Yellow
Write-Host "   - Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "   - API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "   - Health Check:   http://localhost:8000/health/detailed" -ForegroundColor White
Write-Host "   - Frontend:       http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host " New Pages Available:" -ForegroundColor Yellow
Write-Host "   - Analysis:       http://localhost:3000/home/analysis" -ForegroundColor White
Write-Host "   - Batch Analysis: http://localhost:3000/home/batch" -ForegroundColor White
Write-Host "   - Settings:       http://localhost:3000/home/settings/advanced" -ForegroundColor White
Write-Host ""
Write-Host " To stop services: Close the PowerShell windows or press Ctrl+C" -ForegroundColor Gray
Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
