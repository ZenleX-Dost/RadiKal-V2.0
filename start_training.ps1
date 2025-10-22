# ============================================================================
# RadiKal Training Launcher (PowerShell)
# Verifies system setup then starts training automatically
# ============================================================================

param(
    [switch]$SkipConfirmation,
    [switch]$NoMLflow,
    [int]$Epochs = 50,
    [int]$BatchSize = 16
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   $Text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host $Text -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "[SUCCESS] $Text" -ForegroundColor Green
}

function Write-Info {
    param([string]$Text)
    Write-Host "[INFO] $Text" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Text)
    Write-Host "[WARNING] $Text" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

# Start
Clear-Host
Write-Header "RadiKal XAI - Automated Training Launcher"

# Check virtual environment
Write-Section "Checking Environment"

if (-not $env:VIRTUAL_ENV) {
    Write-Warning "Virtual environment not detected"
    Write-Info "Attempting to activate venv..."
    
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
        Write-Success "Virtual environment activated"
    } else {
        Write-Error-Custom "Virtual environment not found!"
        Write-Host ""
        Write-Host "Please create a virtual environment first:" -ForegroundColor Red
        Write-Host "   python -m venv venv" -ForegroundColor Yellow
        Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Success "Virtual environment is active: $env:VIRTUAL_ENV"
}

# Run preflight check
Write-Section "Step 1/3: Running Pre-Flight Verification"

Write-Info "Running preflight_check.py..."
Write-Host ""

try {
    $preflightOutput = python preflight_check.py 2>&1
    $preflightExitCode = $LASTEXITCODE
    
    # Display output
    $preflightOutput | ForEach-Object {
        if ($_ -match "✅") {
            Write-Host $_ -ForegroundColor Green
        } elseif ($_ -match "❌") {
            Write-Host $_ -ForegroundColor Red
        } elseif ($_ -match "⚠️") {
            Write-Host $_ -ForegroundColor Yellow
        } else {
            Write-Host $_
        }
    }
    
    if ($preflightExitCode -ne 0) {
        Write-Host ""
        Write-Error-Custom "Pre-flight check FAILED!"
        Write-Host "Please fix the issues above before training." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host ""
    Write-Success "All pre-flight checks passed!"
    
} catch {
    Write-Error-Custom "Failed to run preflight check: $_"
    Read-Host "Press Enter to exit"
    exit 1
}

# Configuration summary
Write-Section "Step 2/3: Training Configuration"

Write-Host "Training is ready to start with the following configuration:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dataset:           " -NoNewline; Write-Host "RIAWELC (24,407 images)" -ForegroundColor Green
Write-Host "  GPU:               " -NoNewline; Write-Host "NVIDIA RTX 4050 (6GB VRAM)" -ForegroundColor Green
Write-Host "  Batch Size:        " -NoNewline; Write-Host "$BatchSize" -ForegroundColor Green
Write-Host "  Epochs:            " -NoNewline; Write-Host "$Epochs" -ForegroundColor Green
Write-Host "  Expected Duration: " -NoNewline; Write-Host "4-6 hours" -ForegroundColor Yellow
Write-Host "  Expected mAP:      " -NoNewline; Write-Host "0.75-0.90" -ForegroundColor Green
Write-Host ""

# Confirmation
if (-not $SkipConfirmation) {
    $confirmation = Read-Host "Do you want to start training now? (Y/N)"
    if ($confirmation -ne "Y" -and $confirmation -ne "y") {
        Write-Host ""
        Write-Warning "Training cancelled by user"
        Write-Host ""
        exit 0
    }
}

# Start training
Write-Section "Step 3/3: Starting Training"

Write-Info "Training will start in 5 seconds..."
Write-Info "Press Ctrl+C to cancel now"
Write-Host ""

Start-Sleep -Seconds 5

$startTime = Get-Date
Write-Header "Training Started: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"

Write-Host ""
Write-Host "💡 TIPS:" -ForegroundColor Cyan
Write-Host "   Open additional terminals for monitoring:" -ForegroundColor Gray
Write-Host "   Terminal 2: " -NoNewline -ForegroundColor Gray
Write-Host "cd backend; mlflow ui" -ForegroundColor Yellow
Write-Host "   Terminal 3: " -NoNewline -ForegroundColor Gray
Write-Host "nvidia-smi -l 1" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Then open your browser:" -ForegroundColor Gray
Write-Host "   MLflow UI: " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:5000" -ForegroundColor Yellow
Write-Host ""

Write-Section "Training Output"

# Change to backend directory and start training
Push-Location backend

try {
    Write-Info "Executing: python scripts\train.py --config configs\train_config.json --gpu 0"
    Write-Host ""
    
    # Start training with real-time output
    python scripts\train.py --config configs\train_config.json --gpu 0
    
    if ($LASTEXITCODE -eq 0) {
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-Host ""
        Write-Header "Training Completed Successfully!"
        
        Write-Success "Training finished at: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))"
        Write-Success "Total duration: $($duration.ToString('hh\:mm\:ss'))"
        
        Write-Host ""
        Write-Host "📊 Next Steps:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Evaluate the model:" -ForegroundColor Yellow
        Write-Host "   cd backend" -ForegroundColor Gray
        Write-Host "   python scripts\evaluate.py --model models\checkpoints\best_model.pth" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Generate XAI explanations:" -ForegroundColor Yellow
        Write-Host "   python scripts\generate_explanations.py --checkpoint models\checkpoints\best_model.pth" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. View results in MLflow:" -ForegroundColor Yellow
        Write-Host "   mlflow ui" -ForegroundColor Gray
        Write-Host "   Open: " -NoNewline -ForegroundColor Gray
        Write-Host "http://localhost:5000" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "4. Test the API:" -ForegroundColor Yellow
        Write-Host "   uvicorn main:app --reload" -ForegroundColor Gray
        Write-Host "   Open: " -NoNewline -ForegroundColor Gray
        Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host ""
        
    } else {
        throw "Training script returned error code: $LASTEXITCODE"
    }
    
} catch {
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Error-Custom "Training failed after $($duration.ToString('hh\:mm\:ss'))"
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  - Error messages above" -ForegroundColor Gray
    Write-Host "  - GPU availability (nvidia-smi)" -ForegroundColor Gray
    Write-Host "  - Disk space" -ForegroundColor Gray
    Write-Host "  - Dataset integrity" -ForegroundColor Gray
    Write-Host ""
    
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

Pop-Location

Write-Host ""
Read-Host "Press Enter to exit"
exit 0
