# 📚 RadiKal XAI Quality Control - Complete Documentation

**Version**: 2.0  
**Last Updated**: January 1, 2025  
**Status**: ✅ Production Ready with Cloud Supabase Integration

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start Guide](#quick-start-guide)
3. [System Architecture](#system-architecture)
4. [Database Configuration](#database-configuration)
5. [Backend Setup](#backend-setup)
6. [Frontend Setup](#frontend-setup)
7. [Features & Capabilities](#features--capabilities)
8. [Custom Defects System](#custom-defects-system)
9. [Training & Model Management](#training--model-management)
10. [API Documentation](#api-documentation)
11. [Troubleshooting](#troubleshooting)
12. [Development Workflow](#development-workflow)

---

## 🎯 Project Overview

**RadiKal XAI Quality Control** is an AI-powered radiographic weld defect detection system with explainable AI (XAI) capabilities, built for B2B SaaS deployment.

### Core Technology Stack

- **Frontend**: Next.js 15 + Makerkit SaaS Kit + TypeScript + TailwindCSS
- **Backend**: FastAPI + Python 3.10 + YOLOv8/v11
- **Database**: Supabase PostgreSQL (Cloud) with Row Level Security
- **ML/AI**: YOLOv8s-cls, GradCAM, LIME, SHAP, Integrated Gradients
- **Authentication**: Supabase Auth (Multi-tenant)
- **Infrastructure**: Docker, MLflow, DVC

### Key Features

✅ **AI-Powered Defect Detection** - YOLOv8/v11 for weld defect classification  
✅ **Explainable AI (XAI)** - GradCAM heatmaps showing decision-making  
✅ **Custom Defect Types** - User-defined defect categories with training  
✅ **Human-in-the-Loop Learning** - Active learning with review queue  
✅ **Multi-Tenant SaaS** - Account-based isolation with RLS  
✅ **Real-time Analysis** - Upload images, get instant results  
✅ **Training Pipeline** - Automated retraining with transfer learning  
✅ **Compliance Ready** - Certificate generation, audit trails  

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** and **pnpm** installed
- **Git** installed
- **Windows** OS (PowerShell)

### 1. Clone Repository

```powershell
cd "C:\Users\Amine EL-Hend\Documents\GitHub"
git clone https://github.com/ZenleX-Dost/RadiKal-V2.0.git
cd RadiKal-V2.0
```

### 2. Backend Setup (5 minutes)

```powershell
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Configuration is already in .env
# Backend connects to Cloud Supabase automatically

# Test connection
python -c "from db.database import init_db; init_db(); print('Database ready!')"
```

### 3. Frontend Setup (5 minutes)

```powershell
# Navigate to frontend
cd ..\frontend-makerkit\apps\web

# Install dependencies
pnpm install

# Configuration already in .env.local
# Frontend connects to Cloud Supabase automatically
```

### 4. Start Everything

**Option A: Using Batch Scripts**
```powershell
# From project root
.\START_RADIKAL.bat
```

**Option B: Manual Start**
```powershell
# Terminal 1: Start Backend
cd backend
python main.py

# Terminal 2: Start Frontend
cd frontend-makerkit\apps\web
pnpm dev
```

### 5. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Supabase Dashboard**: https://supabase.com/dashboard/project/cvkgrefwbaaordtlqaev

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                       │
│          Next.js 15 Frontend @ :3000                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ • Image Upload Dashboard                         │   │
│  │ • Real-time Analysis Results                     │   │
│  │ • XAI Heatmap Visualization                      │   │
│  │ • Custom Defects Management                      │   │
│  │ • Training Monitor & History                     │   │
│  │ • Review Queue with Active Learning              │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND SERVICES                       │
│           FastAPI Server @ :8000                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │ API Routes:                                      │   │
│  │ • /api/xai-qc/explain - Upload & Analyze        │   │
│  │ • /api/xai-qc/history - Analysis History        │   │
│  │ • /api/xai-qc/metrics - System Metrics          │   │
│  │ • /api/xai-qc/reviews/* - Review Queue (10)     │   │
│  │ • /api/xai-qc/custom-defects/* - Custom (23)    │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ML/XAI Engine:                                   │   │
│  │ • YOLOv8s-cls - Defect Classification           │   │
│  │ • GradCAM - Visual Explanations                 │   │
│  │ • LIME/SHAP - Feature Importance                │   │
│  │ • Transfer Learning - Fine-tuning               │   │
│  │ • Active Learning - Intelligent Sampling        │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ PostgreSQL Protocol
                     ▼
┌─────────────────────────────────────────────────────────┐
│              CLOUD SUPABASE DATABASE                    │
│   PostgreSQL @ aws-1-eu-north-1.pooler.supabase.com    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 15 RadiKal Tables:                               │   │
│  │ Core: analyses, detections, explanations         │   │
│  │ Review: reviews, review_annotations              │   │
│  │ Training: custom_defect_types, training_samples  │   │
│  │ ML: model_versions, training_jobs                │   │
│  │ Active Learning: active_learning_queue           │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Security:                                        │   │
│  │ • Row Level Security (RLS) enabled              │   │
│  │ • Multi-tenant isolation by account_id          │   │
│  │ • Service role for backend access               │   │
│  │ • User authentication via Supabase Auth         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User uploads image** → Frontend sends to `/api/xai-qc/explain`
2. **Backend processes** → YOLOv8 inference + GradCAM heatmap
3. **Results stored** → PostgreSQL (analyses, detections, explanations)
4. **Frontend displays** → Classification + confidence + heatmap
5. **Review optional** → Inspector can correct → Adds to training queue
6. **Active learning** → System suggests uncertain samples for labeling
7. **Retraining** → When enough samples → Transfer learning → New model

---

## 💾 Database Configuration

### Cloud Supabase Setup (CURRENT)

**Connection Details**:
- **Project**: cvkgrefwbaaordtlqaev
- **Region**: EU North 1 (Stockholm)
- **Pooler**: aws-1-eu-north-1.pooler.supabase.com:6543
- **Database**: postgres

**Environment Variables** (`backend/.env`):
```bash
DATABASE_TYPE=supabase
SUPABASE_URL=https://cvkgrefwbaaordtlqaev.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (service_role key)
SUPABASE_DB_URL=postgresql://postgres.cvkgrefwbaaordtlqaev:[PASSWORD]@aws-1-eu-north-1.pooler.supabase.com:6543/postgres
```

### Database Schema (15 Tables)

#### Core Analysis Tables
1. **analyses** - Main analysis records
   - id, image_name, image_path, predicted_class, confidence
   - user_id, account_id, status, created_at

2. **detections** - Individual defect detections
   - analysis_id, defect_type, confidence, bbox coordinates
   - severity, created_at

3. **explanations** - XAI heatmaps
   - analysis_id, method, heatmap_path
   - feature_importance, confidence_breakdown

4. **system_metrics** - Performance tracking
   - timestamp, metric_type, value, metadata

#### Review & QA Tables
5. **reviews** - Human review queue
   - analysis_id, reviewer_id, status, priority
   - corrected_class, corrected_confidence

6. **review_annotations** - Review annotations
   - review_id, annotation_type, coordinates, notes

7. **compliance_certificates** - Compliance docs
   - analysis_id, certificate_number, standard, pdf_path

8. **operator_performance** - Operator tracking
   - operator_id, period metrics, accuracy stats

#### Custom Defects & Training Tables
9. **custom_defect_types** - User-defined defects
   - name, description, color, is_active
   - target_sample_count, current_sample_count
   - requires_retraining, account_id

10. **training_samples** - Labeled training data
    - defect_type_id, image_path, bbox coordinates
    - is_augmented, source, created_by

11. **model_versions** - Trained models
    - version, defect_type_id, model_path
    - accuracy, precision, recall, f1_score
    - is_active, created_at

12. **training_datasets** - Dataset splits
    - name, defect_type_id, split_ratio
    - train_count, val_count, test_count

13. **training_jobs** - Training tracking
    - defect_type_id, dataset_id, status, progress
    - current_epoch, current_loss, best_accuracy

14. **active_learning_queue** - AI suggestions
    - defect_type_id, image_path, prediction
    - uncertainty_score, diversity_score, priority_score

### Row Level Security (RLS)

All tables have RLS policies:
- **Users** see only their own data or team data
- **Account-based isolation** via account_id
- **Service role** (backend) has full access
- **Automatic enforcement** at database level

---

## 🔧 Backend Setup

### Directory Structure

```
backend/
├── api/                      # FastAPI routes
│   ├── routes.py             # Main analysis routes
│   ├── custom_defects_routes.py  # Custom defects (23 endpoints)
│   └── review_routes.py      # Review queue (11 endpoints)
├── core/                     # Core ML/XAI logic
│   ├── models/               # YOLOv8 detector
│   ├── xai/                  # GradCAM, LIME, SHAP, IG
│   ├── learning/             # Active learner
│   └── training/             # Transfer learner, retraining
├── db/                       # Database models
│   ├── database.py           # SQLAlchemy setup
│   └── models.py             # 15 table definitions
├── configs/                  # Configuration files
├── data/                     # Training data
├── models/                   # Trained models
├── exports/                  # Generated reports
├── main.py                   # FastAPI app entry
├── requirements.txt          # Python dependencies
└── .env                      # Environment config
```

### Environment Configuration

**File**: `backend/.env`

```bash
# Database
DATABASE_TYPE=supabase
SUPABASE_URL=https://cvkgrefwbaaordtlqaev.supabase.co
SUPABASE_KEY=<service_role_key>
SUPABASE_DB_URL=postgresql://postgres.cvkgrefwbaaordtlqaev:<password>@aws-1-eu-north-1.pooler.supabase.com:6543/postgres

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true

# Model
MODEL_PATH=models/checkpoints/best_model.pth
DEVICE=cuda  # or cpu
NUM_CLASSES=2
IMAGE_SIZE=512

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=xai-quality-control

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CORS_ALLOW_CREDENTIALS=true

# Training
BATCH_SIZE=8
NUM_EPOCHS=50
LEARNING_RATE=0.0001

# Inference
CONFIDENCE_THRESHOLD=0.5
```

### Key API Endpoints

#### Analysis Endpoints
- `POST /api/xai-qc/explain` - Upload image & get analysis
- `GET /api/xai-qc/history` - Get analysis history
- `GET /api/xai-qc/metrics` - Get system metrics

#### Custom Defects Endpoints (23 total)
- `GET /api/xai-qc/custom-defects` - List all custom defect types
- `POST /api/xai-qc/custom-defects` - Create new defect type
- `GET /api/xai-qc/custom-defects/{id}` - Get specific defect
- `PUT /api/xai-qc/custom-defects/{id}` - Update defect type
- `DELETE /api/xai-qc/custom-defects/{id}` - Delete defect type
- `POST /api/xai-qc/custom-defects/{id}/samples` - Add training sample
- `GET /api/xai-qc/custom-defects/{id}/samples` - List samples
- `POST /api/xai-qc/custom-defects/{id}/train` - Start training
- `GET /api/xai-qc/custom-defects/training/status/{job_id}` - Training status
- `GET /api/xai-qc/custom-defects/active-learning/suggestions` - Get suggestions
- ... and 13 more

#### Review Queue Endpoints (11 total)
- `GET /api/xai-qc/reviews/queue` - Get review queue
- `POST /api/xai-qc/reviews/submit` - Submit review
- `GET /api/xai-qc/reviews/history` - Review history
- `POST /api/xai-qc/reviews/add-to-training` - Add correction to training
- ... and 7 more

---

## 🎨 Frontend Setup

### Directory Structure

```
frontend-makerkit/apps/web/
├── app/                      # Next.js App Router
│   ├── home/                 # Main application pages
│   │   ├── analysis/         # Analysis dashboard
│   │   ├── history/          # Analysis history
│   │   ├── metrics/          # System metrics
│   │   ├── custom-defects/   # Custom defects management
│   │   ├── labeling/         # Dataset labeling tool
│   │   └── review-queue/     # Review queue
│   ├── auth/                 # Authentication pages
│   └── api/                  # API routes (if any)
├── components/               # Reusable components
│   └── radikal/              # RadiKal-specific components
├── lib/                      # Utilities
│   └── radikal/              # RadiKal API client
├── types/                    # TypeScript types
├── public/                   # Static assets
├── .env.local                # Environment variables
├── next.config.js            # Next.js config
└── package.json              # Dependencies
```

### Environment Configuration

**File**: `frontend-makerkit/apps/web/.env.local`

```bash
# Site
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_PRODUCT_NAME=RadiKal
NEXT_PUBLIC_SITE_TITLE=RadiKal XAI Visual Quality Control

# Supabase (Cloud)
NEXT_PUBLIC_SUPABASE_URL=https://cvkgrefwbaaordtlqaev.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key>
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/api/xai-qc

# Auth
NEXT_PUBLIC_AUTH_PASSWORD=true
NEXT_PUBLIC_AUTH_MAGIC_LINK=false

# Feature Flags
NEXT_PUBLIC_ENABLE_THEME_TOGGLE=true
NEXT_PUBLIC_ENABLE_PERSONAL_ACCOUNT_DELETION=true
```

### Key Frontend Pages

1. **Analysis Dashboard** (`/home/analysis`)
   - Image upload interface
   - Real-time analysis results
   - XAI heatmap visualization
   - Defect details with confidence scores

2. **Analysis History** (`/home/history`)
   - Table of past analyses
   - Filtering and sorting
   - Export capabilities

3. **Custom Defects** (`/home/custom-defects`)
   - Create/edit/delete custom defect types
   - View training progress
   - Monitor sample counts
   - Start/stop training jobs

4. **Dataset Labeling** (`/home/labeling`)
   - Interactive canvas for bounding boxes
   - Image upload and annotation
   - Active learning suggestions
   - Batch operations

5. **Review Queue** (`/home/review-queue`)
   - Pending analyses for review
   - Approve/reject/correct predictions
   - Add corrections to training
   - Priority management

6. **System Metrics** (`/home/metrics`)
   - Accuracy trends
   - Performance statistics
   - Model comparisons

---

## ✨ Features & Capabilities

### 1. AI-Powered Defect Detection

**Technology**: YOLOv8s-cls (Classification model)

**Process**:
1. User uploads radiographic weld image
2. Image preprocessed (resize, normalize)
3. YOLOv8 inference (~50-200ms)
4. Classification result with confidence score
5. GradCAM heatmap generated showing decision regions

**Supported Defect Classes**:
- Crack
- Porosity
- Lack of Fusion
- Slag Inclusion
- Undercut
- Normal (No defect)
- ... (extensible via Custom Defects)

### 2. Explainable AI (XAI)

**Methods Implemented**:

#### GradCAM (Default, Fastest)
- Gradient-weighted Class Activation Mapping
- Shows which regions influenced the prediction
- Overlay heatmap on original image
- Real-time generation (~100ms)

#### LIME (On-demand)
- Local Interpretable Model-agnostic Explanations
- Highlights influential superpixels
- More detailed than GradCAM
- Slower (~2-5 seconds)

#### SHAP (Advanced)
- SHapley Additive exPlanations
- Unified approach to explaining predictions
- Feature importance values
- Computation-intensive (~5-10 seconds)

#### Integrated Gradients (Research)
- Gradient-based attribution method
- Path-integral approach
- High-quality explanations
- Very slow (~10-20 seconds)

**Usage**:
```python
# Backend generates automatically
result = await detector.predict(image)
heatmap = await explainer.explain(image, result)

# Frontend displays
<XAIHeatmapViewer 
  image={originalImage}
  heatmap={heatmapBase64}
  prediction={result.class}
/>
```

### 3. Custom Defects System

**Capability**: Define unlimited custom defect categories

**Workflow**:
1. **Create Custom Defect Type**
   - Name, description, color
   - Target sample count (e.g., 100)
   
2. **Label Training Data**
   - Upload images
   - Draw bounding boxes (if detection)
   - Assign to custom defect
   
3. **Automatic Training**
   - Transfer learning from YOLOv8 base
   - Fine-tuning on custom data
   - Progress monitoring in real-time
   
4. **Model Deployment**
   - Automatic activation when trained
   - Version management
   - Rollback capability

**Features**:
- ✅ Human-in-the-loop learning
- ✅ Active learning suggestions
- ✅ Transfer learning (3-stage)
- ✅ Data augmentation
- ✅ Model versioning
- ✅ Performance tracking

### 4. Active Learning

**Purpose**: Intelligently select which samples to label next

**Strategies**:

1. **Uncertainty Sampling**
   - Entropy-based
   - Margin-based
   - Least confident
   
2. **Diversity Sampling**
   - Feature-based clustering
   - Cosine similarity
   - Representative selection

3. **Ensemble Disagreement**
   - Multiple model predictions
   - High disagreement = informative

**Priority Score**:
```python
priority = (
    0.4 * uncertainty_score +
    0.3 * diversity_score +
    0.3 * ensemble_disagreement
)
```

**Usage**:
- System automatically suggests which images to label
- Inspector labels high-priority samples
- Model improves faster with less data

### 5. Review Queue System

**Purpose**: Human verification and correction

**Workflow**:
1. **Analysis Flagged** - Uncertain predictions → Review queue
2. **Inspector Reviews** - Views image + AI prediction + heatmap
3. **Actions**:
   - Approve: Confirms AI prediction is correct
   - Reject: Marks prediction as wrong
   - Correct: Provides correct classification
   - Escalate: Flags for senior review
4. **Add to Training** - Approved/corrected → Training dataset
5. **Model Improvement** - Retraining includes corrections

**Integration with Active Learning**:
- Low confidence corrections (< 0.7) → Active learning queue
- High priority score (0.9) for review corrections
- Automatic retraining trigger when threshold reached

---

## 🎓 Training & Model Management

### Training Pipeline

#### 1. Data Preparation
```python
# Training samples collected from:
samples = [
    manual_labels,        # Hand-labeled by inspectors
    review_corrections,   # Corrections from review queue
    active_learning       # Strategically selected samples
]

# Automatic train/val/test split (80/10/10)
dataset = create_dataset(samples, split_ratio=0.8)
```

#### 2. Transfer Learning (3 Stages)

**Stage 1: Feature Extraction** (5 epochs)
- Freeze all layers except classifier
- Quick adaptation to new data
- Fast convergence

**Stage 2: Fine-tuning Top Layers** (10 epochs)
- Unfreeze last 2-3 layers
- Learn domain-specific features
- Moderate learning rate

**Stage 3: Full Fine-tuning** (35 epochs)
- Unfreeze all layers
- Comprehensive adaptation
- Low learning rate

```python
# Automatic progression
trainer = TransferLearner(base_model="yolov8s-cls")
for stage in [1, 2, 3]:
    trainer.train_stage(stage, dataset)
    metrics = trainer.evaluate(val_dataset)
    if metrics.accuracy < threshold:
        early_stop()
```

#### 3. Training Monitoring

**Real-time Updates**:
- Current epoch / total epochs
- Current loss
- Best accuracy achieved
- Training samples count
- Validation samples count
- Progress percentage

**Frontend Display**:
```typescript
<TrainingMonitor 
  status="training"
  progress={65}
  currentEpoch={32}
  currentLoss={0.23}
  bestAccuracy={0.94}
/>
```

#### 4. Model Deployment

**Automatic Activation**:
- Training completes successfully
- Metrics exceed threshold
- Model exported (PyTorch + ONNX)
- Set as active version
- Previous version archived

**Version Management**:
```sql
-- model_versions table
SELECT version, accuracy, is_active, created_at
FROM model_versions
WHERE defect_type_id = ?
ORDER BY created_at DESC;
```

**Rollback**:
```python
# If new model underperforms
rollback_to_version(previous_version_id)
```

### Retraining Triggers

**Automatic Retraining When**:
1. Sample count reaches target (e.g., 100)
2. `requires_retraining` flag set to TRUE
3. Manual trigger by admin

**Threshold Configuration**:
```python
# custom_defect_types table
{
    "target_sample_count": 100,
    "current_sample_count": 87,  # Auto-train at 100
    "requires_retraining": False
}
```

---

## 📡 API Documentation

### Complete API Reference

#### Analysis Endpoints

**POST /api/xai-qc/explain**
```bash
# Upload image and get analysis
curl -X POST http://localhost:8000/api/xai-qc/explain \
  -F "file=@weld_image.jpg"

# Response
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "predicted_class": "Crack",
  "confidence": 0.94,
  "heatmap_base64": "data:image/png;base64,iVBORw0KGgoAAAA...",
  "detections": [
    {
      "defect_type": "Crack",
      "confidence": 0.94,
      "bbox": [120, 45, 280, 190],
      "severity": "high"
    }
  ]
}
```

**GET /api/xai-qc/history**
```bash
# Get analysis history
curl http://localhost:8000/api/xai-qc/history?limit=10&offset=0

# Response
{
  "total": 247,
  "analyses": [
    {
      "id": "...",
      "image_name": "weld_001.jpg",
      "predicted_class": "Porosity",
      "confidence": 0.87,
      "created_at": "2025-01-01T10:30:00Z"
    }
  ]
}
```

**GET /api/xai-qc/metrics**
```bash
# Get system metrics
curl http://localhost:8000/api/xai-qc/metrics

# Response
{
  "total_analyses": 1247,
  "avg_confidence": 0.89,
  "accuracy": 0.93,
  "defect_distribution": {
    "Crack": 234,
    "Porosity": 189,
    "Normal": 824
  }
}
```

#### Custom Defects Endpoints

**GET /api/xai-qc/custom-defects**
```bash
curl http://localhost:8000/api/xai-qc/custom-defects

# Response
[
  {
    "id": 1,
    "name": "Tungsten Inclusion",
    "description": "Metallic tungsten particles",
    "color": "#FF6B6B",
    "is_active": true,
    "target_sample_count": 100,
    "current_sample_count": 87,
    "requires_retraining": false
  }
]
```

**POST /api/xai-qc/custom-defects**
```bash
curl -X POST http://localhost:8000/api/xai-qc/custom-defects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tungsten Inclusion",
    "description": "Metallic tungsten particles",
    "color": "#FF6B6B",
    "target_sample_count": 100
  }'
```

**POST /api/xai-qc/custom-defects/{id}/train**
```bash
# Start training for a custom defect
curl -X POST http://localhost:8000/api/xai-qc/custom-defects/1/train \
  -H "Content-Type: application/json" \
  -d '{
    "epochs": 50,
    "batch_size": 8,
    "learning_rate": 0.0001
  }'

# Response
{
  "job_id": 42,
  "status": "started",
  "defect_type_id": 1,
  "training_samples": 87,
  "validation_samples": 9
}
```

**GET /api/xai-qc/custom-defects/training/status/{job_id}**
```bash
# Monitor training progress
curl http://localhost:8000/api/xai-qc/custom-defects/training/status/42

# Response
{
  "job_id": 42,
  "status": "training",
  "progress": 65.0,
  "current_epoch": 32,
  "total_epochs": 50,
  "current_loss": 0.234,
  "best_accuracy": 0.941,
  "started_at": "2025-01-01T12:00:00Z"
}
```

#### Review Queue Endpoints

**GET /api/xai-qc/reviews/queue**
```bash
curl http://localhost:8000/api/xai-qc/reviews/queue?status=pending

# Response
{
  "total": 15,
  "reviews": [
    {
      "id": 1,
      "analysis_id": "...",
      "status": "pending",
      "priority": "high",
      "image_name": "weld_042.jpg",
      "ai_prediction": "Crack",
      "ai_confidence": 0.62,
      "assigned_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

**POST /api/xai-qc/reviews/add-to-training**
```bash
# Add review correction to training
curl -X POST http://localhost:8000/api/xai-qc/reviews/add-to-training \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "...",
    "corrected_defect_type_id": 1,
    "confidence": 1.0
  }'

# Response
{
  "success": true,
  "sample_id": 123,
  "defect_type": "Tungsten Inclusion",
  "current_sample_count": 88,
  "target_sample_count": 100,
  "training_ready": false,
  "added_to_active_learning": true
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'torch'`

**Solution**:
```powershell
cd backend
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

**Error**: `Could not connect to database`

**Solution**:
- Check `.env` file has correct `SUPABASE_DB_URL`
- Verify Supabase project is active
- Test connection:
  ```powershell
  python -c "from db.database import init_db; init_db()"
  ```

#### 2. Frontend Won't Start

**Error**: `Module not found: Can't resolve 'lib/radikal'`

**Solution**:
```powershell
cd frontend-makerkit\apps\web
pnpm install
```

**Error**: `Invalid Supabase URL`

**Solution**:
- Check `.env.local` has correct `NEXT_PUBLIC_SUPABASE_URL`
- Verify anon key is valid

#### 3. Database Connection Issues

**Error**: `Tenant or user not found`

**Solution**:
- Get correct connection string from Supabase Dashboard
- Go to: Settings → Database → Connection string → URI
- Copy entire string to `SUPABASE_DB_URL` in `backend/.env`

**Error**: `Could not translate host name`

**Solution**:
- Use pooler URL, not direct connection
- Format: `postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres`

#### 4. Training Issues

**Error**: `Not enough training samples`

**Solution**:
- Need minimum 50 samples per custom defect
- Add more labels via Dataset Labeling tool
- Check `current_sample_count` in Custom Defects page

**Error**: `CUDA out of memory`

**Solution**:
- Reduce batch size in training config
- Switch to CPU: Set `DEVICE=cpu` in `.env`
- Close other GPU applications

#### 5. XAI Heatmap Not Showing

**Error**: Heatmap is blank or not displaying

**Solution**:
- Check GradCAM model layer exists
- Verify image preprocessing
- Test with sample image:
  ```python
  from core.xai.gradcam_explainer import GradCAMExplainer
  explainer = GradCAMExplainer()
  heatmap = explainer.explain(image, prediction)
  ```

### Debug Mode

**Enable verbose logging**:

Backend (`backend/.env`):
```bash
LOG_LEVEL=DEBUG
```

Frontend (browser console):
```javascript
localStorage.setItem('debug', 'radikal:*')
```

### Health Checks

**Backend**:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Database**:
```bash
python -c "from db.database import engine; print(engine.url)"
# Expected: Shows Supabase connection string
```

**Frontend**:
```bash
curl http://localhost:3000
# Expected: HTML response (200 OK)
```

---

## 🔄 Development Workflow

### Adding a New Feature

1. **Backend Changes**:
   ```bash
   # Add route
   backend/api/routes.py or new file
   
   # Add database model (if needed)
   backend/db/models.py
   
   # Test locally
   python -m pytest tests/
   ```

2. **Frontend Changes**:
   ```bash
   # Add page/component
   frontend-makerkit/apps/web/app/home/new-feature/
   
   # Add API client method
   frontend-makerkit/apps/web/lib/radikal/api-client.ts
   
   # Test locally
   pnpm dev
   ```

3. **Database Migration** (if schema changed):
   ```bash
   cd frontend-makerkit/apps/web
   
   # Create migration
   pnpm supabase migration new feature_name
   
   # Edit migration file
   # supabase/migrations/TIMESTAMP_feature_name.sql
   
   # Apply migration
   pnpm supabase db push
   ```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... code ...

# Commit
git add .
git commit -m "feat: add new feature"

# Push
git push origin feature/new-feature

# Create Pull Request on GitHub
```

### Testing

**Backend Tests**:
```bash
cd backend
python -m pytest tests/ -v
python -m pytest tests/test_api.py::test_explain_endpoint
```

**Frontend Tests**:
```bash
cd frontend-makerkit/apps/web
pnpm test
pnpm test:e2e
```

### Deployment

**Backend** (Example: Railway/Render):
1. Push to GitHub
2. Connect repository to hosting service
3. Set environment variables
4. Deploy

**Frontend** (Example: Vercel):
1. Push to GitHub
2. Import repository in Vercel
3. Set environment variables
4. Deploy

**Database** (Already on Supabase Cloud):
- Already deployed and configured
- Apply migrations: `pnpm supabase db push`

---

## 📞 Support & Resources

### Documentation
- **Supabase Docs**: https://supabase.com/docs
- **Next.js Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **YOLOv8 Docs**: https://docs.ultralytics.com

### Quick Links
- **Supabase Dashboard**: https://supabase.com/dashboard/project/cvkgrefwbaaordtlqaev
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **GitHub Repo**: https://github.com/ZenleX-Dost/RadiKal-V2.0

### Project Status
- ✅ Backend: Complete with 34 API endpoints
- ✅ Frontend: Complete with 6 main pages
- ✅ Database: Cloud Supabase with 15 tables
- ✅ Custom Defects: Full CRUD + Training
- ✅ Active Learning: Implemented
- ✅ Review Queue: Integrated
- ✅ XAI: GradCAM, LIME, SHAP, IG
- ✅ Multi-tenant: RLS enabled

---

## 🎉 Summary

**RadiKal XAI Quality Control** is a production-ready B2B SaaS platform for AI-powered weld defect detection with explainable AI. The system features:

- **Real-time analysis** with YOLOv8 (~100ms inference)
- **Explainable AI** with visual heatmaps (GradCAM)
- **Custom defect types** with transfer learning
- **Human-in-the-loop** active learning
- **Multi-tenant SaaS** architecture
- **Cloud Supabase** for scalable database
- **Complete API** (34 endpoints)
- **Professional UI** with Next.js 15

**Everything is configured and ready to use!** Just start the backend and frontend, and you're good to go.

---

**Last Updated**: October 30, 2025  
**Version**: 2.0  
**Status**: ✅ Production Ready
