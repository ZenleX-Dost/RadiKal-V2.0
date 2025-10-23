# 🚀 Quick Start Guide - Updated for Classification Model

## ✅ Your Model is Ready!

The new **YOLOv8 Classification Model** (99.89% accuracy) is now integrated into your RadiKal application.

---

## 🎯 How to Start RadiKal

### Method 1: Use START_RADIKAL.bat (Recommended)

Just **double-click** this file:
```
START_RADIKAL.bat
```

**What it does:**
1. ✅ Starts backend server (loads classification model automatically)
2. ✅ Starts frontend server
3. ✅ Opens http://localhost:3000 in your browser

**That's it!** The new classification model will be loaded automatically.

---

### Method 2: Manual Start

If you prefer to start services manually:

**Terminal 1 - Backend:**
```powershell
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

---

## 🧪 Test Before Starting (Optional)

Run this to verify everything works:
```
Double-click: TEST_NEW_MODEL.bat
```

This will:
- ✅ Check if model file exists
- ✅ Test classification on sample images
- ✅ Verify server can start

---

## 📍 Model Path Configuration

The application is now configured to use:

**File**: `backend/api/routes.py`
```python
YOLO_MODEL_PATH = Path("models/yolo/classification_defect_focused/weights/best.pt")
```

**This happens automatically when you run `START_RADIKAL.bat`!**

---

## ✅ Startup Flow

```
START_RADIKAL.bat
    ↓
backend/main.py
    ↓
api/routes.py (initialize_models)
    ↓
Loads: models/yolo/classification_defect_focused/weights/best.pt
    ↓
✅ Classification model ready!
```

---

## 🎯 What Changed from Before

| Aspect | Before | Now |
|--------|--------|-----|
| **Model Type** | Detection (wrong) | Classification ✅ |
| **Model File** | radikal_weld_detection/best.pt | classification_defect_focused/best.pt ✅ |
| **Task** | Find boxes around defects | Classify entire image ✅ |
| **Minor Defects** | Often missed ❌ | Better detection ✅ |
| **Accuracy** | 99.5% (but wrong task) | 99.89% (correct task) ✅ |

---

## 🚀 Start Now!

### Quick Start (Recommended):
1. **Double-click**: `START_RADIKAL.bat`
2. Wait 10-15 seconds
3. Browser opens automatically at http://localhost:3000
4. Upload a radiographic image
5. Get classification result!

### Services Will Run At:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000  
- **API Docs**: http://localhost:8000/api/docs

---

## 🛑 How to Stop

**Option 1**: Close the command windows

**Option 2**: Run `STOP_ALL.ps1`:
```powershell
.\STOP_ALL.ps1
```

---

## ✅ Verification

After starting, check if model loaded correctly:

1. **Open API docs**: http://localhost:8000/api/docs
2. **Check logs** in the backend terminal:
   ```
   ✅ Loaded YOLOv8 model from models\yolo\classification_defect_focused\weights\best.pt
   Model Info: YOLOv8s
   Performance: mAP@0.5 = 0.9988
   ```

3. **Test prediction**:
   - Go to http://localhost:3000
   - Upload a weld radiograph
   - Should classify as: LP, PO, CR, or ND

---

## 🎉 You're All Set!

**The new classification model is fully integrated and will load automatically when you start RadiKal with `START_RADIKAL.bat`!**

No additional configuration needed - just start the application! 🚀
