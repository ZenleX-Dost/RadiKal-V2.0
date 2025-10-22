# RTX 4050 Setup and Training Script
# Run this script to verify GPU setup and start training

Write-Host "=== XAI Quality Control - RTX 4050 Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check NVIDIA GPU
Write-Host "Checking for NVIDIA GPU..." -ForegroundColor Yellow
try {
    nvidia-smi
    Write-Host "GPU detected successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: nvidia-smi not found. Please install NVIDIA drivers." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Verifying CUDA Installation ===" -ForegroundColor Cyan

# Check CUDA version
try {
    $cudaVersion = nvcc --version
    Write-Host "CUDA installed: $cudaVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING: nvcc not found. CUDA toolkit may not be installed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Checking Python Environment ===" -ForegroundColor Cyan

# Check Python
$pythonVersion = python --version
Write-Host "Python version: $pythonVersion" -ForegroundColor Green

# Check if in virtual environment
if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "WARNING: Not in a virtual environment. Consider creating one:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor White
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
}

Write-Host ""
Write-Host "=== Installing Dependencies ===" -ForegroundColor Cyan
Write-Host "This will install PyTorch with CUDA support and other dependencies..." -ForegroundColor White

$install = Read-Host "Install dependencies now? (y/n)"
if ($install -eq "y") {
    cd backend
    pip install -r requirements.txt
    
    Write-Host ""
    Write-Host "=== Verifying PyTorch CUDA Support ===" -ForegroundColor Cyan
    python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
} else {
    Write-Host "Skipping installation. Make sure to install dependencies before training!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Prepare your dataset in backend/data/" -ForegroundColor White
Write-Host "2. Review training config in backend/configs/train_config.json" -ForegroundColor White
Write-Host "3. Start training:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python scripts/train.py --config configs/train_config.json --gpu 0" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Monitor training with MLflow:" -ForegroundColor White
Write-Host "   mlflow ui" -ForegroundColor Gray
Write-Host "   Open http://localhost:5000" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed instructions, see: backend/RTX4050_TRAINING_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

# Offer to start training
$startTraining = Read-Host "Start training now? (y/n)"
if ($startTraining -eq "y") {
    Write-Host ""
    Write-Host "=== Starting Training ===" -ForegroundColor Cyan
    cd backend
    python scripts/train.py --config configs/train_config.json --gpu 0
}
