@echo off
echo ======================================================================
echo      Resume YOLOv8 Training - RadiKal Weld Detection
echo ======================================================================
echo.
echo This will resume training from your last checkpoint (Epoch 36)
echo.
echo Starting in 3 seconds...
echo Press Ctrl+C now if you want to cancel
timeout /t 3
echo.
cd /d "C:\Users\Amine EL-Hend\Documents\GitHub\RadiKal\backend"
python scripts/resume_training.py
echo.
echo ======================================================================
echo Training session finished! Press any key to close...
pause
