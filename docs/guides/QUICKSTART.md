# Quick Start Guide - XAI Visual Quality Control

This guide will help you get started quickly with the XAI Visual Quality Control system, specifically optimized for training on your **NVIDIA RTX 4050** GPU.

## 🚀 Quick Setup (5 minutes)

### 1. Clone and Navigate

```powershell
cd "c:\Users\Amine EL-Hend\Documents\GitHub\RadiKal"
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Run Automated Setup

```powershell
.\setup_rtx4050.ps1
```

This script will:
- ✅ Verify your RTX 4050 GPU is detected
- ✅ Check CUDA installation
- ✅ Install all dependencies with CUDA support
- ✅ Verify PyTorch can use your GPU
- ✅ Offer to start training immediately

## 📊 Training on RTX 4050

### Optimized Configuration

The system is pre-configured for your RTX 4050 (6GB VRAM):

- **Batch Size**: 8 (optimal for 512x512 images)
- **Mixed Precision**: Enabled (saves ~30% VRAM)
- **Gradient Clipping**: Enabled for stability
- **Auto Memory Management**: Cache cleared every batch

### Start Training

```powershell
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

### Monitor with MLflow

In a separate terminal:

```powershell
cd backend
mlflow ui
```

Then open: http://localhost:5000

## 📁 Project Structure

```
RadiKal/
├── backend/                      # Python backend
│   ├── api/                      # FastAPI routes & schemas
│   ├── core/                     # Core ML modules
│   │   ├── models/              # Detection models
│   │   ├── xai/                 # XAI methods (GradCAM, SHAP, LIME, IG)
│   │   ├── uncertainty/         # MC-Dropout, calibration
│   │   ├── preprocessing/       # Image processing
│   │   └── metrics/             # Business & technical metrics
│   ├── scripts/                 # Training & evaluation scripts
│   ├── configs/                 # Configuration files
│   ├── data/                    # Dataset storage
│   ├── models/                  # Saved models
│   └── tests/                   # Unit tests
├── frontend/                    # Makerkit/Next.js UI (placeholder)
└── notebooks/                   # Jupyter notebooks
```

## 🔧 Configuration Files

### Training Config (`backend/configs/train_config.json`)

Key settings for RTX 4050:

```json
{
  "batch_size": 8,              // Optimized for 6GB VRAM
  "num_epochs": 50,
  "learning_rate": 0.0001,
  "image_size": [512, 512],
  "num_workers": 4,
  "gpu_optimization": {
    "enabled": true,
    "device": "cuda:0",
    "mixed_precision": true
  }
}
```

### Module Config (`backend/module.yaml`)

System metadata including hardware requirements.

## 📚 Key Features Implemented

### ✅ Core ML Pipeline
- [x] Faster R-CNN defect detector
- [x] Image preprocessing & validation
- [x] Comprehensive unit tests

### ✅ XAI Methods
- [x] **Grad-CAM**: Class activation mapping
- [x] **SHAP**: Shapley value explanations
- [x] **LIME**: Local interpretable explanations
- [x] **Integrated Gradients**: Attribution-based explanations
- [x] **Aggregator**: Combines all methods with consensus scoring

### ✅ Uncertainty Quantification
- [x] **MC-Dropout**: Predictive uncertainty estimation
- [x] **Calibration**: ECE, temperature scaling, reliability diagrams

### ✅ Metrics
- [x] **Business**: FN, FP, TP, TN, Precision, Recall, F1
- [x] **Detection**: mAP@0.5, mAP@0.75, AUROC
- [x] **Segmentation**: IoU, Dice Score, Pixel Accuracy

### ✅ MLOps
- [x] **MLflow**: Experiment tracking
- [x] **DVC**: Data & model versioning
- [x] Model cards & dataset cards

### ✅ API (Schemas & Middleware)
- [x] FastAPI schemas for all endpoints
- [x] Makerkit JWT authentication
- [x] Role-based access control

## 🎯 Next Steps

### 1. Prepare Your Data

Create dataset structure:

```
backend/data/
├── train/
│   ├── images/
│   └── annotations.json
├── val/
│   ├── images/
│   └── annotations.json
└── test/
    ├── images/
    └── annotations.json
```

Annotation format (COCO-style):

```json
[
  {
    "image_file": "image1.jpg",
    "boxes": [[x1, y1, x2, y2], ...],
    "labels": [1, ...]
  }
]
```

### 2. Train the Model

```powershell
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

Expected training time: **3-5 hours** (50 epochs, depends on dataset size)

### 3. Evaluate Performance

```powershell
python scripts/evaluate.py --model models/checkpoints/best_model.pth
```

### 4. Test XAI Explanations

Create a test script or use the API to generate explanations:

```python
from core.xai.gradcam import GradCAM
from core.models.detector import DefectDetector

model = DefectDetector(num_classes=2)
gradcam = GradCAM(model)
heatmap = gradcam.generate_heatmap(image_tensor)
```

### 5. Run Tests

```powershell
cd backend
pytest tests/ -v --cov=core --cov=api
```

Expected coverage: **>90%**

## 📖 Documentation

- **Training Guide**: `backend/RTX4050_TRAINING_GUIDE.md` - Detailed GPU training instructions
- **Backend README**: `backend/README.md` - Full API documentation
- **Frontend README**: `frontend/README.md` - Makerkit integration guide

## ⚡ Performance Expectations

On your RTX 4050:

- **Training**: ~2-3 seconds/batch (batch_size=8, 512x512)
- **Inference**: <200ms per image
- **VRAM Usage**: ~5.5GB (during training)
- **Total Time**: ~3-5 hours for 50 epochs

## 🐛 Troubleshooting

### CUDA Out of Memory

Reduce batch size in `configs/train_config.json`:

```json
{
  "batch_size": 4
}
```

### PyTorch Can't Find CUDA

Reinstall PyTorch with CUDA:

```powershell
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Slow Training

- Close GPU-intensive applications (browsers, games)
- Ensure data is on SSD (not HDD)
- Check `nvidia-smi` for other processes using GPU

## 📞 Support

Check these files for detailed information:

1. `backend/RTX4050_TRAINING_GUIDE.md` - GPU-specific guide
2. `backend/README.md` - API and backend documentation
3. `backend/CHANGELOG.md` - Recent changes
4. `backend/tests/` - Example usage in tests

## 🎓 Learning Resources

- **XAI Methods**: See `backend/core/xai/` implementations
- **MLflow**: http://localhost:5000 (after starting mlflow ui)
- **DVC**: Run `dvc repro` to see full pipeline

---

**Ready to train?** Run `.\setup_rtx4050.ps1` to get started! 🚀
