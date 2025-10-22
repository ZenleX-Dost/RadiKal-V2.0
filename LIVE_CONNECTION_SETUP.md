# 🚀 RadiKal - Live Backend Connection Setup

## ✅ What Changed

### 1. **Removed ALL Mock Data**
- Frontend now ONLY connects to real backend
- No fallback data - if backend is down, you'll see an error
- All metrics, mAP values, and analysis data come from live backend

### 2. **Fixed Backend Startup**
- Modified `main.py` to disable reload mode (Windows compatibility)
- Added signal handling to prevent premature shutdown
- Created reliable startup scripts

### 3. **Dark Mode Only**
- Removed theme toggle button
- Application always runs in dark mode
- Cleaner, more professional UI

## 🎯 How to Start Everything

### **Option 1: One-Click Startup (EASIEST)**
1. Double-click `START_ALL.bat` in the root folder
2. Two windows will open (Backend + Frontend)
3. Wait ~15 seconds for everything to initialize
4. Browser opens automatically to http://localhost:3000

### **Option 2: Manual Startup**

#### Terminal 1 - Backend:
```powershell
cd backend
python main.py
```
**Keep this window open!** Backend runs on port 8000.

#### Terminal 2 - Frontend:
```powershell
cd frontend
npm run dev
```
**Keep this window open!** Frontend runs on port 3000.

## 📊 Verifying Backend Connection

### 1. Check Backend Health
Open in browser: http://localhost:8000/api/xai-qc/health

Should see:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T...",
  "model_loaded": true,
  "database_connected": true
}
```

### 2. Check API Documentation
Open: http://localhost:8000/api/docs

You'll see interactive API documentation with all endpoints.

### 3. Check Metrics Page
1. Go to http://localhost:3000/metrics
2. Should see REAL mAP values from backend:
   - mAP@0.5: 99.88%
   - mAP@0.75: 98.56%
   - mAP Average: 99.74%

If you see an error instead, the backend isn't running!

## 🔧 Troubleshooting

### "Backend connection failed" Error
**Cause**: Backend server is not running

**Solution**:
1. Open a new terminal
2. Run: `cd backend && python main.py`
3. Wait for "Uvicorn running on http://0.0.0.0:8000"
4. Refresh frontend page

### Port Already in Use
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual number)
taskkill /PID <PID> /F

# Try starting again
cd backend
python main.py
```

### Server Starts Then Immediately Stops
**Solution**: Run in a dedicated terminal window, not in background mode.

Use the `START_ALL.bat` script or open a NEW PowerShell window.

## 📁 Important Files

- `START_ALL.bat` - One-click startup for everything
- `backend/start_backend.bat` - Backend only
- `backend/main.py` - Backend entry point (modified for Windows)
- `STARTUP_GUIDE.md` - Detailed startup instructions

## 🎉 What You Get

### Real-Time Data Flow:
```
Frontend (Port 3000)
    ↓ HTTP Requests
Backend (Port 8000)
    ↓ Loads Model
YOLOv8s (99.88% mAP)
    ↓ Inference
Results → Frontend
```

### No Mock Data:
- ❌ No fallback values
- ❌ No cached metrics  
- ✅ Only real backend responses
- ✅ Live model predictions
- ✅ Real database queries

## 🔥 Quick Test Workflow

1. **Start servers**: Run `START_ALL.bat`
2. **Wait**: ~15 seconds for initialization
3. **Check backend**: http://localhost:8000/api/xai-qc/health
4. **Check frontend**: http://localhost:3000
5. **Upload image**: Go to Dashboard, upload a weld image
6. **See live results**: Real YOLOv8 detection with 99.88% accuracy!

## 💡 Pro Tips

1. **Always start backend FIRST**, then frontend
2. **Keep both terminal windows open** while using the app
3. **Check backend logs** if you see connection errors
4. **Use API docs** (http://localhost:8000/api/docs) to test endpoints
5. **Frontend will show clear errors** if backend is down (no silent failures!)

---

**Everything is now configured for REAL, LIVE backend connection!** 🚀
