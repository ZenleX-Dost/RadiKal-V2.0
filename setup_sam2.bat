@echo off
setlocal enabledelayedexpansion

echo ========================================
echo RadiKal SAM2 Integration Setup
echo ========================================
echo.
echo Using global Python environment
echo.

echo Step 1: Installing SAM2 Dependencies
echo --------------------------------------

REM Install SAM2 from GitHub
echo Installing SAM2 from GitHub repository...
echo This may take a few minutes...
pip install git+https://github.com/facebookresearch/segment-anything-2.git

REM Install timm
echo Installing timm (required by SAM2)...
pip install timm

echo [OK] Dependencies installed
echo.

echo Step 2: Creating Model Directory
echo --------------------------------------

set MODEL_DIR=backend\models\sam2
if not exist "%MODEL_DIR%" (
    mkdir "%MODEL_DIR%" 2>nul
    echo [OK] Created directory: %MODEL_DIR%
) else (
    echo [OK] Directory already exists: %MODEL_DIR%
)
echo.

echo Step 3: Downloading SAM2 v1.1 Checkpoints
echo --------------------------------------
echo.
echo Select SAM2 model size for your GPU (RTX 4050 = 6GB VRAM):
echo   1) Tiny   - Fastest, good for testing     (~150MB, ~2GB VRAM)
echo   2) Small  - Balanced performance          (~185MB, ~3GB VRAM)
echo   3) Base+  - RECOMMENDED for 6GB GPU       (~310MB, ~4GB VRAM)
echo   4) Large  - Best accuracy (needs 8GB+)    (~900MB, ~8GB VRAM)
echo   5) Skip   - Download manually later
echo.

set /p CHOICE="Enter choice (1-5): "

set DOWNLOAD_URL=
set FILE_NAME=

REM SAM2 v1.1 checkpoints (092824 = September 2024 release)
if "%CHOICE%"=="1" (
    set DOWNLOAD_URL=https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt
    set FILE_NAME=sam2.1_hiera_t.pt
) else if "%CHOICE%"=="2" (
    set DOWNLOAD_URL=https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt
    set FILE_NAME=sam2.1_hiera_s.pt
) else if "%CHOICE%"=="3" (
    set DOWNLOAD_URL=https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt
    set FILE_NAME=sam2.1_hiera_base_plus.pt
) else if "%CHOICE%"=="4" (
    set DOWNLOAD_URL=https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt
    set FILE_NAME=sam2.1_hiera_l.pt
) else if "%CHOICE%"=="5" (
    echo [SKIP] Skipping checkpoint download
    echo Download manually from:
    echo   https://github.com/facebookresearch/segment-anything-2/tree/main/checkpoints
    goto :skip_download
) else (
    echo [ERROR] Invalid choice
    pause
    exit /b 1
)

set TARGET_PATH=%MODEL_DIR%\%FILE_NAME%

if exist "%TARGET_PATH%" (
    echo [OK] Checkpoint already exists: %FILE_NAME%
) else (
    echo Downloading %FILE_NAME%...
    echo This may take several minutes...
    
    REM Use curl (available in Windows 10+) or PowerShell
    where curl >nul 2>&1
    if !errorlevel! equ 0 (
        curl -L -o "%TARGET_PATH%" "%DOWNLOAD_URL%"
        if !errorlevel! equ 0 (
            echo [OK] Downloaded: %FILE_NAME%
        ) else (
            echo [ERROR] Download failed
            echo Please download manually from:
            echo   %DOWNLOAD_URL%
        )
    ) else (
        REM Fallback to PowerShell
        powershell -Command "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TARGET_PATH%'"
        if !errorlevel! equ 0 (
            echo [OK] Downloaded: %FILE_NAME%
        ) else (
            echo [ERROR] Download failed
            echo Please download manually from:
            echo   %DOWNLOAD_URL%
        )
    )
)

:skip_download
echo.
echo Step 4: Running Tests
echo --------------------------------------

echo Running SAM2 integration test suite...
cd backend
python test_sam2_integration.py
set TEST_RESULT=!errorlevel!
cd ..

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.

if !TEST_RESULT! equ 0 (
    echo [OK] All tests passed!
    echo.
    echo SAM2 integration is ready to use.
    echo.
    echo Next steps:
    echo   1. Start backend: python backend/run_server.py
    echo   2. Test API: curl -X POST http://localhost:8000/api/xai-qc/analyze-hybrid -F "file=@image.jpg"
    echo   3. Review docs: docs/SAM2_INTEGRATION.md
) else (
    echo [WARN] Some tests failed
    echo.
    echo Check the test output above for details.
    echo The system may still work with limited functionality.
    echo.
    echo For help, see: docs/SAM2_INTEGRATION.md
)

echo.
pause
