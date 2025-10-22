# 📁 RadiKal Startup Files Reference

## Current Startup Files (After Cleanup)

### 🚀 Application Startup

| File | Purpose | Usage |
|------|---------|-------|
| **START_RADIKAL.bat** | ⭐ **Recommended** - Main launcher | Double-click to start |
| **START_SILENT.ps1** | PowerShell with loading window | `.\START_SILENT.ps1` |
| **START_SILENT.vbs** | Silent VBScript launcher | Double-click for silent start |
| **START_ALL.bat** | Development mode with terminals | For debugging |
| **STOP_ALL.ps1** | Stop all services | `.\STOP_ALL.ps1` |

### 🎓 Model Training

| File | Purpose | Usage |
|------|---------|-------|
| **backend/TRAIN.bat** | Start new training | Double-click in backend folder |
| **backend/RESUME_TRAINING.bat** | Resume training | Continue from checkpoint |
| **start_training.bat** | Root training launcher | Alternative launcher |
| **start_training.ps1** | PowerShell training script | `.\start_training.ps1` |
| **start_training_now.ps1** | Immediate training start | Quick training launch |

### ⚙️ Setup

| File | Purpose | Usage |
|------|---------|-------|
| **setup_rtx4050.ps1** | GPU environment setup | One-time setup for RTX 4050 |

## Deleted Files (No Longer Needed)

The following obsolete files have been removed:

- ❌ `1_START_BACKEND.bat` - Replaced by START_RADIKAL.bat
- ❌ `2_START_FRONTEND.bat` - Replaced by START_RADIKAL.bat
- ❌ `3_TEST_CONNECTION.bat` - No longer needed
- ❌ `START_ALL.ps1` - Duplicate of START_ALL.bat
- ❌ `backend/start_backend.bat` - Old backend launcher
- ❌ `backend/START_SERVER.bat` - Duplicate file

## Quick Start

**To start RadiKal:**
```
Double-click START_RADIKAL.bat
```

**To stop RadiKal:**
```powershell
.\STOP_ALL.ps1
```

**For development (with logs):**
```
Double-click START_ALL.bat
```

## File Organization

```
RadiKal/
├── START_RADIKAL.bat      ⭐ Use this to start
├── START_SILENT.ps1        (Called by START_RADIKAL.bat)
├── START_SILENT.vbs        (Alternative silent launcher)
├── START_ALL.bat           (Development mode)
├── STOP_ALL.ps1            (Stop services)
├── start_training.bat      (Training launcher)
├── start_training.ps1      (Training script)
├── start_training_now.ps1  (Quick training)
├── setup_rtx4050.ps1       (GPU setup)
└── backend/
    ├── TRAIN.bat           (New training)
    └── RESUME_TRAINING.bat (Resume training)
```

## Migration Guide

If you had shortcuts to old files, update them:

| Old File | New File |
|----------|----------|
| 1_START_BACKEND.bat | START_RADIKAL.bat |
| 2_START_FRONTEND.bat | START_RADIKAL.bat |
| 3_TEST_CONNECTION.bat | Open http://localhost:3000 |
| START_ALL.ps1 | START_ALL.bat |
| backend/start_backend.bat | START_RADIKAL.bat |

---

**Last Updated:** October 21, 2025  
**Cleanup Date:** October 21, 2025
