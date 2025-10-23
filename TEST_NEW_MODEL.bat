@echo off
title RadiKal Classification Model Test
color 0A
cls

echo.
echo ========================================
echo.
echo    Testing New Classification Model
echo.
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/3] Checking model file exists...
if exist "models\yolo\classification_defect_focused\weights\best.pt" (
    echo       ✓ Model file found!
) else (
    echo       ✗ Model file NOT found!
    echo       Expected: models\yolo\classification_defect_focused\weights\best.pt
    pause
    exit /b 1
)

echo.
echo [2/3] Testing classifier...
python test_classifier.py
if %ERRORLEVEL% NEQ 0 (
    echo       ✗ Classifier test failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Testing server startup...
echo       Starting backend server (will stop after 5 seconds)...
start /B "" cmd /c "python main.py > server_test.log 2>&1"
timeout /t 8 /nobreak > nul

echo       Checking if server started...
curl -s http://localhost:8000/ > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo       ✓ Server is running!
    echo       ✓ API accessible at http://localhost:8000
) else (
    echo       ✗ Server not responding
    type server_test.log
    pause
    exit /b 1
)

echo.
echo ========================================
echo.
echo   ✓ All tests passed!
echo.
echo   Your RadiKal application is ready!
echo.
echo   Model: Classification (99.89% accuracy)
echo   Path: models\yolo\classification_defect_focused\weights\best.pt
echo.
echo ========================================
echo.
echo Stopping test server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *" > nul 2>&1

echo.
echo You can now run START_RADIKAL.bat safely!
echo.
pause
