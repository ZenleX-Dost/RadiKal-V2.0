# RadiKal Stop All Services
# Stops backend and frontend processes

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Stopping RadiKal Services..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop Python processes (Backend)
Write-Host "Stopping Backend (Python)..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "  Backend stopped ✓" -ForegroundColor Green
} else {
    Write-Host "  No backend processes found" -ForegroundColor Gray
}

# Stop Node processes (Frontend)
Write-Host "Stopping Frontend (Node.js)..." -ForegroundColor Yellow
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force
    Write-Host "  Frontend stopped ✓" -ForegroundColor Green
} else {
    Write-Host "  No frontend processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services stopped!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pause
