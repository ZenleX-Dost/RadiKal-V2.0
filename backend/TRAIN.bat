@echo off
echo ======================================================================
echo      YOLOv8 Training - RadiKal Weld Defect Detection
echo ======================================================================
echo.
echo Starting training in 5 seconds...
echo Press Ctrl+C now if you want to cancel
timeout /t 5
echo.
cd /d "C:\Users\Amine EL-Hend\Documents\GitHub\RadiKal\backend"
python scripts/start_training.py
echo.
echo ======================================================================
echo Training finished! Press any key to close...
pause
