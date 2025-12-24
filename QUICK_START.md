# 🚀 RadiKal V2.0 - Quick Start Guide

**Last Updated**: December 9, 2025  
**Status**: Production Ready

---

## ✅ One-Command Startup

### For Windows:
```bash
START_RADIKAL.bat
```

This single command will:
1. Kill any existing processes on ports 3000 and 8000
2. Start the backend (FastAPI + YOLOv8) on port **8000**
3. Start the frontend (Next.js + Makerkit) on port **3000**
4. Open your browser automatically

---

## 🌐 Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application interface |
| **Backend** | http://localhost:8000 | FastAPI REST API |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |

---

## 🛑 Stopping Services

### Option 1: PowerShell Script (Recommended)
```powershell
.\STOP_ALL.ps1
```

### Option 2: Manual
Press `Ctrl+C` in the terminal window running START_RADIKAL.bat

---

## 📁 Project Structure

```
RadiKal-V2.0/
├── START_RADIKAL.bat          ⭐ Main startup file (USE THIS)
├── STOP_ALL.ps1                ⭐ Stop all services
├── backend/
│   ├── run_server.py           → Port 8000
│   ├── main.py
│   ├── api/
│   │   ├── routes.py           → /detect, /explain, /preprocess
│   │   └── review_routes.py    → /reviews/*, /reviewers
│   └── models/
│       └── yolo/
│           └── classification_defect_focused/
│               └── weights/
│                   └── best.pt  → YOLOv8s (99.8% accuracy)
└── frontend-makerkit/
    └── apps/
        └── web/                 → Port 3000
            ├── app/
            │   └── home/
            │       ├── analysis/         → Contrast adjustment
            │       └── review-queue/     → Hierarchical reviews
            └── lib/
                └── radikal/
                    └── api.ts            → API client
```

---

## 🔧 Port Configuration

### Backend (Port 8000)
**File**: `backend/run_server.py`
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,  # Backend port
    reload=False
)
```

### Frontend (Port 3000)
**File**: `frontend-makerkit/apps/web/.env.development`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Package.json**: `pnpm dev` runs on port 3000 by default

---

## 🎯 Key Features Available

### 1. Analysis Page (`/home/analysis`)
- ✅ Upload radiographic images
- ✅ **Contrast Adjustment** (NEW)
  - Slider: 0.5x - 3.0x
  - Methods: Linear, Histogram, CLAHE, Gamma
  - Real-time preview (side-by-side)
- ✅ YOLOv8s classification
- ✅ Grad-CAM XAI heatmaps
- ✅ Defect detection results

### 2. Review Queue (`/home/review-queue`)
- ✅ View pending analyses
- ✅ **Hierarchical Reviews** (NEW)
  - Three options: Approve, Reject, Request Second Opinion
  - Select peer technician or project chief
  - Role badges (Manager/Project Chief/Technician)
- ✅ Add comments and annotations
- ✅ Full image display (no truncation)

### 3. Role Management
- ✅ Manager → Project Chief → Technician hierarchy
- ✅ Database columns: `role`, `project_chief_id`, `manager_id`
- ✅ Reviewer selection based on organizational structure

### 4. Image Storage
- ✅ Full resolution images stored in database
- ✅ Preview + original images (no 1000-char truncation)
- ✅ Base64 encoding in PostgreSQL

---

## 🗄️ Database Configuration

**Supabase Cloud**:
- Project: `cvkgrefwbaaordtlqaev`
- Region: EU North 1
- URL: https://cvkgrefwbaaordtlqaev.supabase.co

**Tables**:
- `analyses` - Image analyses with full storage
- `accounts` - Users with role hierarchy
- `detections` - YOLO detections
- `explanations` - XAI explanations

**New Columns Added**:
```sql
-- Image storage
ALTER TABLE analyses ADD COLUMN image_base64 TEXT;
ALTER TABLE analyses ADD COLUMN original_image_base64 TEXT;

-- Role management
ALTER TABLE accounts ADD COLUMN role VARCHAR(50);
ALTER TABLE accounts ADD COLUMN project_chief_id UUID;
ALTER TABLE accounts ADD COLUMN manager_id UUID;
```

---

## 🧪 Testing Checklist

### Quick Test (2 minutes)
1. Run `START_RADIKAL.bat`
2. Wait for browser to open
3. Navigate to `/home/analysis`
4. Upload a test image
5. Verify results display

### Full Feature Test (10 minutes)
1. **Contrast Adjustment**:
   - Upload image → Click "Adjust Contrast"
   - Move slider to 1.5x, select CLAHE
   - Click "Preview Adjustment"
   - Verify side-by-side comparison
   - Analyze with adjusted settings

2. **Review Queue**:
   - Navigate to `/home/review-queue`
   - Select an analysis
   - Click "Second Opinion"
   - Verify reviewer dropdown shows users with role badges
   - Submit review with assignment

3. **API Endpoints**:
   - Visit http://localhost:8000/docs
   - Test `/api/xai-qc/preprocess`
   - Test `/api/xai-qc/reviews/reviewers`

---

## ⚠️ Troubleshooting

### Issue: Port already in use
**Solution**: Run `STOP_ALL.ps1` first, then `START_RADIKAL.bat`

### Issue: Frontend shows connection error
**Solution**: 
1. Check backend is running: http://localhost:8000/docs
2. Verify `.env.development` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Issue: Images not displaying in Review Queue
**Solution**: Upload new images after the image storage update. Old analyses may not have stored images.

### Issue: Reviewer list is empty
**Solution**: 
```sql
-- Assign roles to users in Supabase
UPDATE accounts SET role = 'technician' WHERE email = 'user@example.com';
UPDATE accounts SET role = 'project_chief' WHERE email = 'chief@example.com';
```

### Issue: Python/Node processes won't stop
**Solution**:
```powershell
# Manual cleanup
Get-Process python,node | Where-Object {$_.Path -notmatch "Adobe"} | Stop-Process -Force
```

---

## 📚 API Endpoints Summary

### Detection & Analysis
- `POST /api/xai-qc/detect` - Detect defects
- `POST /api/xai-qc/explain` - Get XAI explanations (with contrast params)
- `POST /api/xai-qc/preprocess` - Preview contrast adjustment ⭐ NEW

### Review System
- `GET /api/xai-qc/reviews/queue` - Get pending reviews
- `GET /api/xai-qc/reviews/reviewers` - Get available reviewers ⭐ NEW
- `POST /api/xai-qc/reviews/submit` - Submit review (with assignment) ⭐ UPDATED

### History & Metrics
- `GET /api/xai-qc/history` - Analysis history
- `GET /api/xai-qc/metrics` - Performance metrics
- `POST /api/xai-qc/export` - Export reports

---

## 🔐 Authentication

**Supabase Auth** is enabled:
- Sign up: http://localhost:3000/auth/sign-up
- Sign in: http://localhost:3000/auth/sign-in

**Default for testing**: Auth is optional (can use system user)

---

## 📊 System Requirements

- **OS**: Windows 10/11
- **Python**: 3.10+
- **Node.js**: 18+ (with pnpm)
- **GPU**: NVIDIA RTX 4050 or better (for CUDA)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for models and data

---

## 🎉 What's New in V2.0

1. ✅ **Contrast Adjustment** - Preprocess images with 4 methods
2. ✅ **Hierarchical Reviews** - Manager/Chief/Technician workflow
3. ✅ **Reviewer Assignment** - Select specific reviewers
4. ✅ **Full Image Storage** - No truncation, full resolution
5. ✅ **Role Management** - Organizational hierarchy support
6. ✅ **Improved XAI** - Better heatmaps and explanations

---

## 📝 Next Steps

After starting the application:

1. **First Time Setup**:
   - Create account at `/auth/sign-up`
   - Assign roles in Supabase database
   - Configure organizational hierarchy

2. **Upload Test Images**:
   - Navigate to `/home/analysis`
   - Try different contrast settings
   - Review XAI explanations

3. **Test Review Workflow**:
   - Submit analysis for review
   - Assign to different reviewers
   - Track review history

---

## 🆘 Support

**Issues**: Open issue on GitHub  
**Docs**: See `HIERARCHICAL_FEATURES_COMPLETE.md` for detailed feature documentation  
**API**: Visit http://localhost:8000/docs for interactive API documentation

---

**Ready to start? Run `START_RADIKAL.bat` now!** 🚀
