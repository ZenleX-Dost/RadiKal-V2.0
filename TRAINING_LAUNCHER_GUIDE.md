# 🚀 Training Launcher Scripts - Quick Guide

## Overview

Two automated training launcher scripts have been created to simplify the training process:

1. **`start_training.bat`** - Windows Batch file (simple, compatible)
2. **`start_training.ps1`** - PowerShell script (advanced, colorful)

Both scripts automatically:
- ✅ Verify virtual environment
- ✅ Run pre-flight checks (`preflight_check.py`)
- ✅ Display training configuration
- ✅ Ask for confirmation
- ✅ Start training if everything passes
- ✅ Show next steps after completion

---

## 🎯 Usage

### Option 1: Windows Batch File (Recommended for Beginners)

**Simple Run:**
```cmd
start_training.bat
```

**Features:**
- Simple, straightforward execution
- Works in Command Prompt
- Auto-activates virtual environment
- Color-coded output
- Error handling with pause

---

### Option 2: PowerShell Script (Recommended for Power Users)

**Basic Run:**
```powershell
.\start_training.ps1
```

**Advanced Options:**
```powershell
# Skip confirmation prompt (auto-start)
.\start_training.ps1 -SkipConfirmation

# Custom epochs and batch size
.\start_training.ps1 -Epochs 100 -BatchSize 8

# Combine options
.\start_training.ps1 -SkipConfirmation -Epochs 75 -BatchSize 12
```

**Features:**
- Colorful, modern output (Green ✅, Red ❌, Yellow ⚠️)
- Real-time progress display
- Training duration tracking
- Advanced error handling
- Parameter support
- Professional formatting

---

## 📋 What Happens Step-by-Step

### Step 1: Environment Check (Automatic)
```
✅ Checking if virtual environment is activated
✅ Auto-activates venv if needed
❌ Exits with error if venv not found
```

### Step 2: Pre-Flight Verification (Automatic)
```
Runs: python preflight_check.py

Checks:
✅ GPU Detection (CUDA availability)
✅ Dataset Presence (24,407 images)
✅ Configuration Correctness (4 classes, 224×224)
✅ Training Script Availability
```

### Step 3: Configuration Display
```
Shows:
- Dataset: RIAWELC (24,407 images)
- GPU: NVIDIA RTX 4050 (6GB VRAM)
- Batch Size: 16
- Epochs: 50
- Expected Duration: 4-6 hours
- Expected mAP: 0.75-0.90
```

### Step 4: User Confirmation
```
Prompt: "Do you want to start training now? (Y/N)"
- Press Y to continue
- Press N to cancel
- (Skip with -SkipConfirmation in PowerShell)
```

### Step 5: Training Execution
```
Executes:
cd backend
python scripts\train.py --config configs\train_config.json --gpu 0

Displays:
- Real-time training output
- Epoch progress
- Loss values
- Validation metrics
```

### Step 6: Completion Summary
```
On Success:
✅ Training duration
✅ Next steps guide
✅ Evaluation commands
✅ MLflow UI link

On Failure:
❌ Error details
❌ Troubleshooting tips
❌ Duration before failure
```

---

## 🎨 Output Examples

### Batch File (.bat)
```
============================================================
   RadiKal XAI - Automated Training Launcher
============================================================

[OK] Virtual environment is active

------------------------------------------------------------
Step 1/3: Running Pre-Flight Verification
------------------------------------------------------------

✅ CUDA Available: True
✅ GPU Device: NVIDIA GeForce RTX 4050 Laptop GPU
✅ TRAIN: 15,863 images
✅ All checks passed!

[SUCCESS] All pre-flight checks passed!

------------------------------------------------------------
Step 2/3: Confirmation
------------------------------------------------------------

Do you want to start training now? (Y/N): Y

------------------------------------------------------------
Step 3/3: Starting Training
------------------------------------------------------------

Training Started: 10/14/2025 14:30:00
...
```

### PowerShell (.ps1)
```
============================================================
   RadiKal XAI - Automated Training Launcher
============================================================

✅ [SUCCESS] Virtual environment is active

------------------------------------------------------------
Step 1/3: Running Pre-Flight Verification
------------------------------------------------------------

✅ CUDA Available: True
✅ GPU Device: NVIDIA GeForce RTX 4050 Laptop GPU
✅ Configuration correct

[SUCCESS] All pre-flight checks passed!

------------------------------------------------------------
Training Started: 2025-10-14 14:30:00
============================================================

💡 TIPS:
   Terminal 2: cd backend; mlflow ui
   Terminal 3: nvidia-smi -l 1
   MLflow UI: http://localhost:5000
...
```

---

## 🔧 Customization

### Modify Training Parameters

**In Batch File** (edit `start_training.bat`):
```batch
REM Line ~100: Change the training command
python scripts\train.py --config configs\train_config.json --gpu 0 --epochs 100
```

**In PowerShell** (use parameters):
```powershell
.\start_training.ps1 -Epochs 100 -BatchSize 8
```

### Skip Confirmation

**PowerShell Only:**
```powershell
.\start_training.ps1 -SkipConfirmation
```

**Batch File** (edit and remove confirmation section):
```batch
REM Comment out or remove these lines:
REM set /p CONFIRM="Do you want to start training now? (Y/N): "
REM if /i not "%CONFIRM%"=="Y" (
REM    ...
REM )
```

---

## 📊 Monitoring During Training

While training runs, open additional terminals:

### Terminal 2: MLflow UI
```powershell
cd backend
mlflow ui
```
Then open: http://localhost:5000

### Terminal 3: GPU Monitor
```powershell
nvidia-smi -l 1
```
Updates every 1 second

---

## 🛠️ Troubleshooting

### Issue: "Virtual environment not found"
**Solution:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### Issue: "Pre-flight check failed"
**Solution:**
```powershell
# Run check manually to see details
python preflight_check.py

# Common fixes:
# - GPU not detected: Check CUDA installation
# - Dataset missing: Verify backend/data/ folder
# - Config wrong: Check backend/configs/train_config.json
```

### Issue: "PowerShell execution policy"
**Solution:**
```powershell
# Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run the script
.\start_training.ps1
```

### Issue: Training crashes with OOM (Out of Memory)
**Solution:**
```powershell
# Run with smaller batch size
.\start_training.ps1 -BatchSize 8

# Or edit config file:
# backend/configs/train_config.json
# Change "batch_size": 16 to "batch_size": 8
```

---

## 🎯 Quick Command Reference

### Start Training (Simple)
```cmd
start_training.bat
```

### Start Training (Advanced)
```powershell
.\start_training.ps1
```

### Start Training (Auto-confirm)
```powershell
.\start_training.ps1 -SkipConfirmation
```

### Start Training (Custom Config)
```powershell
.\start_training.ps1 -Epochs 100 -BatchSize 8 -SkipConfirmation
```

### Manual Pre-Flight Check Only
```powershell
python preflight_check.py
```

### Manual Training (No Automation)
```powershell
cd backend
python scripts\train.py --config configs\train_config.json --gpu 0
```

---

## 📁 Related Files

| File | Purpose |
|------|---------|
| `start_training.bat` | Windows Batch launcher |
| `start_training.ps1` | PowerShell launcher (advanced) |
| `preflight_check.py` | System verification script |
| `backend/scripts/train.py` | Actual training script |
| `backend/configs/train_config.json` | Training configuration |

---

## ✅ Recommended Workflow

1. **First Time:**
   ```powershell
   # Verify everything manually
   python preflight_check.py
   
   # Review output, ensure all checks pass
   ```

2. **Start Training:**
   ```powershell
   # Use launcher script
   .\start_training.ps1
   
   # Or batch file
   start_training.bat
   ```

3. **Open Monitoring (While Training):**
   ```powershell
   # Terminal 2
   cd backend
   mlflow ui
   
   # Terminal 3
   nvidia-smi -l 1
   ```

4. **After Training:**
   ```powershell
   cd backend
   
   # Evaluate
   python scripts\evaluate.py --model models\checkpoints\best_model.pth
   
   # Generate explanations
   python scripts\generate_explanations.py --checkpoint models\checkpoints\best_model.pth
   ```

---

## 🎉 Benefits of Using These Scripts

✅ **Automated Verification** - No need to remember all checks  
✅ **Error Prevention** - Catches issues before training starts  
✅ **Time Saving** - One command instead of multiple steps  
✅ **User Friendly** - Clear prompts and colorful output  
✅ **Professional** - Logs timestamps and durations  
✅ **Foolproof** - Confirms before starting long training  
✅ **Helpful** - Shows next steps after completion  

---

**Created**: October 14, 2025  
**Status**: Ready to use  
**Tested**: Windows 10/11 with PowerShell 5.1+
