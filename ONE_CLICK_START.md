# ⚡ QUICK START - One Click!

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🎯 START EVERYTHING WITH ONE CLICK!                       │
│                                                             │
│     Double-click: START_ALL.bat                            │
│                                                             │
│  ✅ Backend starts automatically                           │
│  ✅ Frontend starts automatically                          │
│  ✅ Browser opens automatically                            │
│  ✅ Ready to use in 15 seconds!                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 Available Start Files

### ⚡ ONE-CLICK START (NEW!)

#### `START_ALL.bat` ⭐ RECOMMENDED
```
📁 Location: Root folder
🎯 Purpose: Start EVERYTHING at once
✨ Features:
   - Opens 2 terminal windows
   - Starts backend automatically
   - Starts frontend automatically
   - Opens browser at http://localhost:3000
   - Shows status in both windows
```

**How to use:**
1. Double-click `START_ALL.bat`
2. Wait 15 seconds
3. Browser opens automatically
4. Start detecting defects!

---

#### `START_ALL.ps1` (PowerShell Alternative)
```
📁 Location: Root folder
🎯 Purpose: Same as .bat but with colors!
✨ Features:
   - Colored output (easier to read)
   - Same functionality as .bat
   - Better error handling
```

**How to use:**
1. Right-click `START_ALL.ps1`
2. Select "Run with PowerShell"
3. Wait 15 seconds
4. Browser opens automatically

---

### 📋 STEP-BY-STEP START (Manual Control)

#### `1_START_BACKEND.bat`
```
🎯 Start backend only
📡 Port: 8000
🤖 Model: YOLOv8s (99.88% mAP)
```

#### `2_START_FRONTEND.bat`
```
🎯 Start frontend only
📡 Port: 3000
🖥️ Framework: Next.js
```

#### `3_TEST_CONNECTION.bat`
```
🎯 Test if backend is ready
✅ Verifies API connection
📊 Shows server status
```

---

## 🎯 What Happens When You Start

### Phase 1: Backend Startup (Window 1)
```
========================================
   RadiKal Backend Server
========================================

Starting FastAPI with YOLOv8 model...
✅ Loaded YOLOv8 model from best.pt
✅ Performance: mAP@0.5 = 0.9988
✅ Uvicorn running on http://0.0.0.0:8000

Server ready! ✨
```

### Phase 2: Frontend Startup (Window 2)
```
========================================
   RadiKal Frontend
========================================

Installing dependencies...
✅ Dependencies installed

Starting Next.js development server...
✅ Ready in 2.3s
✅ Local: http://localhost:3000

Opening browser... 🌐
```

### Phase 3: Browser Opens
```
🌐 http://localhost:3000

Your RadiKal dashboard loads!
Ready to upload images and detect defects! 🎉
```

---

## 🎬 Complete Startup Flow

```
Double-click START_ALL.bat
         ↓
┌────────────────────┐
│ Main Window Opens  │
│ "Starting system…" │
└─────────┬──────────┘
          │
          ├─→ Opens Backend Window
          │   └─→ Starts FastAPI
          │       └─→ Loads YOLOv8 model
          │           └─→ ✅ Ready on :8000
          │
          ├─→ Waits 10 seconds
          │
          ├─→ Opens Frontend Window  
          │   └─→ Installs dependencies
          │       └─→ Starts Next.js
          │           └─→ ✅ Ready on :3000
          │
          └─→ Opens Browser
              └─→ http://localhost:3000
                  └─→ 🎉 Ready to use!
```

---

## ⏱️ Startup Times

| Component | Time | Status |
|-----------|------|--------|
| Backend startup | ~8 sec | Model loading |
| Frontend startup | ~5 sec | Build + serve |
| Browser open | ~2 sec | Auto-launch |
| **Total** | **~15 sec** | **Ready!** |

---

## 🎨 What You'll See

### Main Control Window:
```
========================================
   RadiKal - Full System Startup
========================================

[1/2] Starting Backend Server...
✅ Backend window opened!

Waiting 10 seconds for backend to initialize...

[2/2] Starting Frontend...
✅ Frontend window opened!

========================================
   System Startup Complete!
========================================

Services:
  Backend:  http://localhost:8000
  API Docs: http://localhost:8000/api/docs
  Frontend: http://localhost:3000

Your browser will open automatically!

Press any key to exit this window...
```

### Backend Window (Green):
```
========================================
   RadiKal Backend Server
========================================

INFO:     Started server process
INFO:api.routes:Initializing models on device: cuda
INFO:core.models.yolo_detector:Loading YOLOv8 model...
INFO:core.models.yolo_detector:Model loaded successfully
INFO:api.routes:✅ Loaded YOLOv8 model
INFO:api.routes:   Performance: mAP@0.5 = 0.9988
INFO:     Uvicorn running on http://0.0.0.0:8000

Press Ctrl+C to stop
```

### Frontend Window (Blue):
```
========================================
   RadiKal Frontend
========================================

Installing dependencies...
✅ Dependencies up to date

Starting Next.js development server...
- ready started server on 0.0.0.0:3000
✓ Ready in 2.3s
○ Local:   http://localhost:3000

Opening browser in 5 seconds...
Press Ctrl+C to stop
```

---

## 🛑 How to Stop

### Stop Everything:
1. **Close all terminal windows**, or
2. **Press Ctrl+C** in each window

### Stop One Service:
- Backend only: Close backend window
- Frontend only: Close frontend window

---

## 🔄 Restart After Changes

### Code Changes:
- **Frontend**: Auto-reloads (hot reload enabled)
- **Backend**: Restart backend window only

### Full Restart:
1. Close all windows
2. Double-click `START_ALL.bat` again

---

## ✅ Verification Checklist

After starting, verify:

- [ ] Backend window shows "Uvicorn running"
- [ ] Backend shows "mAP@0.5 = 0.9988"
- [ ] Frontend window shows "Ready in X.Xs"
- [ ] Browser opens to http://localhost:3000
- [ ] Upload button is visible
- [ ] No error messages in windows

---

## 🐛 Troubleshooting

### "Port already in use"
**Problem:** Previous instance still running

**Solution:**
```bash
# Kill processes on ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Backend window closes immediately
**Problem:** Python error or missing dependencies

**Solution:**
```bash
cd backend
pip install -r requirements.txt
python start_server.py
```

### Frontend won't start
**Problem:** Node modules not installed

**Solution:**
```bash
cd frontend
npm install
npm run dev
```

### Browser doesn't open
**Not a problem!** Just manually open:
```
http://localhost:3000
```

---

## 🎯 After Startup

### 1. Upload an Image
- Click "Upload Image" button
- Select a weld X-ray image
- Wait for processing (~2 seconds)

### 2. View Results
- See bounding boxes on defects
- Check defect types (Difetto1, Difetto2, Difetto4, NoDifetto)
- View confidence scores
- Check severity levels

### 3. API Documentation
Visit: http://localhost:8000/api/docs
- Interactive API testing
- Try endpoints directly
- See request/response schemas

---

## 📊 System Resources

While running:
- **RAM**: ~2-3 GB (both services)
- **GPU**: Used by YOLOv8 inference
- **CPU**: Low (mostly idle)
- **Network**: Localhost only (no internet needed)

---

## 🎓 Pro Tips

### Tip 1: Keep windows visible
Position backend and frontend windows side-by-side to monitor both

### Tip 2: Check backend logs
Backend window shows all API requests and responses

### Tip 3: Use API docs
Test endpoints at http://localhost:8000/api/docs before coding

### Tip 4: Hot reload
Frontend auto-reloads on code changes (save = instant update!)

### Tip 5: Monitor performance
Backend shows inference time for each detection

---

## 🎉 Success Indicators

You'll know it's working when you see:

✅ **Backend:** "Uvicorn running on http://0.0.0.0:8000"
✅ **Frontend:** "Ready in X.Xs" and "○ Local: http://localhost:3000"  
✅ **Browser:** RadiKal dashboard loads
✅ **Upload:** Can select and upload images
✅ **Detection:** Results appear with bounding boxes

---

## 🚀 Ready to Go!

```
╔═══════════════════════════════════════╗
║                                       ║
║  🎉 EVERYTHING IS READY!             ║
║                                       ║
║  Just double-click: START_ALL.bat    ║
║                                       ║
║  And start detecting defects! 🔍     ║
║                                       ║
╚═══════════════════════════════════════╝
```

---

**Quick Start Summary:**
1. Double-click `START_ALL.bat`
2. Wait 15 seconds
3. Upload weld images
4. See defects detected with 99.88% accuracy! 🎯

**That's it!** 🎊

---

*Last Updated: January 20, 2025*  
*One-Click Startup: ✅ AVAILABLE*
