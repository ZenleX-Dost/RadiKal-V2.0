@echo off
REM ============================================================================
REM RadiKal Training Launcher
REM Verifies system setup then starts training automatically
REM ============================================================================

SETLOCAL EnableDelayedExpansion

echo.
echo ============================================================
echo    RadiKal XAI - Automated Training Launcher
echo ============================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo [WARNING] Virtual environment not detected
    echo Attempting to activate venv...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
        echo [OK] Virtual environment activated
    ) else (
        echo [ERROR] Virtual environment not found at venv\Scripts\activate.bat
        echo Please create a virtual environment first:
        echo    python -m venv venv
        echo    .\venv\Scripts\Activate.ps1
        pause
        exit /b 1
    )
) else (
    echo [OK] Virtual environment is active: %VIRTUAL_ENV%
)

echo.
echo ------------------------------------------------------------
echo Step 1/3: Running Pre-Flight Verification
echo ------------------------------------------------------------
echo.

REM Run preflight check
python preflight_check.py
if errorlevel 1 (
    echo.
    echo [ERROR] Pre-flight check FAILED!
    echo Please fix the issues above before training.
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All pre-flight checks passed!
echo.

REM Ask user confirmation
echo ------------------------------------------------------------
echo Step 2/3: Confirmation
echo ------------------------------------------------------------
echo.
echo Training is ready to start with the following configuration:
echo   - Dataset: RIAWELC (24,407 images)
echo   - GPU: NVIDIA RTX 4050 (6GB VRAM)
echo   - Batch Size: 16
echo   - Epochs: 50
echo   - Expected Duration: 4-6 hours
echo   - Expected mAP: 0.75-0.90
echo.

set /p CONFIRM="Do you want to start training now? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo [CANCELLED] Training cancelled by user
    echo.
    pause
    exit /b 0
)

echo.
echo ------------------------------------------------------------
echo Step 3/3: Starting Training
echo ------------------------------------------------------------
echo.
echo [INFO] Training will start in 5 seconds...
echo [INFO] Press Ctrl+C to cancel now
timeout /t 5 /nobreak >nul

echo.
echo [START] Launching training script...
echo.
echo ============================================================
echo Training Started: %date% %time%
echo ============================================================
echo.
echo [TIP] Open another terminal and run these commands:
echo    Terminal 2: cd backend ^&^& mlflow ui
echo    Terminal 3: nvidia-smi -l 1
echo.
echo Training output below:
echo ------------------------------------------------------------
echo.

REM Change to backend directory and start training
cd backend
python scripts\train.py --config configs\train_config.json --gpu 0

REM Check training result
if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERROR] Training failed! Check the error messages above.
    echo ============================================================
    echo.
    cd ..
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================
    echo [SUCCESS] Training completed successfully!
    echo Training Finished: %date% %time%
    echo ============================================================
    echo.
    echo Next steps:
    echo   1. Evaluate the model:
    echo      cd backend
    echo      python scripts\evaluate.py --model models\checkpoints\best_model.pth
    echo.
    echo   2. Generate XAI explanations:
    echo      python scripts\generate_explanations.py --checkpoint models\checkpoints\best_model.pth
    echo.
    echo   3. View results in MLflow:
    echo      mlflow ui
    echo      Open: http://localhost:5000
    echo.
    cd ..
)

pause
exit /b 0
