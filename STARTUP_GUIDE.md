# 🚀 RadiKal Startup Guide

## Silent Startup (Recommended - No Terminal Windows)

### Option 1: Double-click START_RADIKAL.bat ⭐
The easiest way to start RadiKal without terminal windows:
1. Double-click `START_RADIKAL.bat` in the root folder
2. A small loading window will appear showing progress
3. Wait 15-20 seconds for services to start
4. Your browser will open automatically to http://localhost:3000

### Option 2: Use PowerShell script with GUI
```powershell
.\START_SILENT.ps1
```
Shows a nice loading window with progress bar

### Option 3: Use VBScript (completely silent)
```
Double-click START_SILENT.vbs
```
- Shows only popup messages
- No terminal windows at all
- Perfect for production use

## Traditional Startup (With Terminal Windows)

If you prefer to see the server logs in terminal windows:
```
.\START_ALL.bat
```
This will open 2 terminal windows showing:
- Backend server logs (FastAPI + YOLOv8)
- Frontend server logs (Next.js)

## Stopping Services

### Method 1: Use the stop script (Recommended)
```powershell
.\STOP_ALL.ps1
```

### Method 2: Task Manager
1. Open Task Manager (Ctrl+Shift+Esc)
2. End these processes:
   - `python.exe` (Backend)
   - `node.exe` (Frontend)

### Method 3: Kill from PowerShell
```powershell
Get-Process python,node | Stop-Process -Force
```

## Services Running

When RadiKal is running, these services are available:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main web interface |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/api/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/api/xai-qc/health | Server status |

## Troubleshooting

### PowerShell execution policy error
If you get "execution policy" error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port already in use
```powershell
# Stop all RadiKal services
.\STOP_ALL.ps1

# Or manually find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Services won't start
1. Check Python is installed: `python --version`
2. Check Node.js is installed: `node --version`
3. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

### CUDA/GPU Issues
- Server will automatically fallback to CPU if CUDA is not available
- Check GPU availability in logs: "device: cuda" or "device: cpu"

## File Overview

| File | Purpose |
|------|---------|
| `START_RADIKAL.bat` | **⭐ Recommended** - Easy double-click launcher with loading window |
| `START_SILENT.ps1` | PowerShell script with nice GUI loading window |
| `START_SILENT.vbs` | Completely silent VBScript launcher (popup messages only) |
| `START_ALL.bat` | Traditional startup with visible terminal windows |
| `STOP_ALL.ps1` | Stop all RadiKal services cleanly |

## First Time Setup

1. Install dependencies:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

2. Make sure YOLOv8 model is in place:
   - File: `backend/models/best.pt`
   - This is your trained YOLOv8s model (99.88% mAP)

3. Start the application:
   - Double-click `START_RADIKAL.bat`
   - Wait for loading window to complete
   - Browser opens automatically

## Development Mode

For development with hot-reload and visible logs:

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

This gives you:
- Live reload on code changes
- Visible error messages and logs
- Better debugging experience

## What Happens on Startup

1. ✅ Database initialized at: `backend/data/radikal.db`
2. ✅ YOLOv8 model loaded from: `models/yolo/radikal_weld_detection/weights/best.pt`
3. ✅ Model Info: YOLOv8s
4. ✅ Performance: mAP@0.5 = 0.9988 (99.88%)
5. ✅ Server running on http://0.0.0.0:8000

## Backend + Frontend Together

### Terminal 1 (Backend):
```powershell
cd backend
python main.py
```

### Terminal 2 (Frontend):
```powershell
cd frontend
npm run dev
```

Both must be running simultaneously for full functionality!
