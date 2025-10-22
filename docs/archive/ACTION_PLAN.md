# RadiKal XAI QC - Action Plan
# Generated: October 14, 2025

## PHASE 1: Environment Setup (10-15 minutes)

### Step 1.1: Create Virtual Environment
```powershell
cd "c:\Users\Amine EL-Hend\Documents\GitHub\RadiKal"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 1.2: Install Dependencies
```powershell
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: This will install PyTorch with CUDA 11.8 support. Your CUDA 13.0 is backward compatible.

### Step 1.3: Verify PyTorch CUDA Support
```powershell
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

Expected output:
```
PyTorch version: 2.1.0+cu118
CUDA available: True
CUDA version: 11.8
GPU: NVIDIA GeForce RTX 4050 Laptop GPU
```

---

## PHASE 2: Prepare Sample Dataset (30-60 minutes)

You have two options:

### Option A: Use Your Own Dataset (Recommended if you have data)

Create this structure:
```
backend/data/
├── train/
│   ├── images/
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   └── annotations.json
├── val/
│   ├── images/
│   └── annotations.json
└── test/
    ├── images/
    └── annotations.json
```

Annotation format (COCO-style JSON):
```json
[
  {
    "image_file": "img001.jpg",
    "boxes": [[x1, y1, x2, y2], [x1, y1, x2, y2]],
    "labels": [1, 1]
  },
  {
    "image_file": "img002.jpg",
    "boxes": [[x1, y1, x2, y2]],
    "labels": [1]
  }
]
```

Where:
- `boxes`: List of bounding boxes [x1, y1, x2, y2] in pixel coordinates
- `labels`: 0 = background, 1 = defect (or your class IDs)

### Option B: Create Synthetic Test Dataset (Quick start)

I can create a script to generate synthetic defect images for testing:

```powershell
# Run this to generate test dataset
python scripts/generate_test_dataset.py --num-samples 100
```

---

## PHASE 3: Test the System (15 minutes)

### Step 3.1: Run Unit Tests
```powershell
cd backend
pytest tests/ -v --cov=core
```

### Step 3.2: Test Model Initialization
```powershell
python -c "from core.models.detector import DefectDetector; model = DefectDetector(num_classes=2, device='cuda'); print('Model loaded successfully on GPU!')"
```

### Step 3.3: Test XAI Methods
```powershell
python -c "from core.xai.gradcam import GradCAM; print('XAI modules imported successfully!')"
```

---

## PHASE 4: Start Training (3-5 hours)

### Step 4.1: Review Training Configuration
Edit `backend/configs/train_config.json` if needed:
- Adjust `num_epochs` (default: 50)
- Adjust `batch_size` (default: 8, optimal for RTX 4050)
- Set paths to your dataset

### Step 4.2: Initialize MLflow
```powershell
cd backend
mlflow ui
```
Leave this running in a separate terminal. Access at http://localhost:5000

### Step 4.3: Start Training
```powershell
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

Expected output:
```
=== XAI Quality Control - Training ===
GPU: NVIDIA GeForce RTX 4050 Laptop GPU
CUDA Version: 11.8
Available GPU Memory: 6.14 GB
RTX 4050 GPU setup complete with optimized settings

Epoch 1/50
Training: 100%|████████████| 125/125 [04:32<00:00,  2.18s/batch, loss=0.542]
Validation mAP@0.5: 0.673
Saved best model with mAP@0.5: 0.673
...
```

### Step 4.4: Monitor Training
- **MLflow UI**: http://localhost:5000
- **GPU Usage**: Run `nvidia-smi -l 1` in another terminal
- **Loss Curves**: Check MLflow for training/validation metrics

---

## PHASE 5: Evaluate & Test (30 minutes)

### Step 5.1: Evaluate Model
```powershell
cd backend
python scripts/evaluate.py --model models/checkpoints/best_model.pth
```

### Step 5.2: Test XAI Explanations
Create a test script to generate explanations:

```python
# test_xai.py
from core.models.detector import DefectDetector
from core.xai.gradcam import GradCAM
from core.xai.aggregator import XAIAggregator
import torch

# Load model
model = DefectDetector(num_classes=2, device='cuda')
model.load_weights('models/checkpoints/best_model.pth')

# Test Grad-CAM
gradcam = GradCAM(model.model)
# ... generate heatmaps
```

### Step 5.3: Generate Calibration Report
```powershell
python scripts/calibrate_model.py
```

---

## PHASE 6: API Development (Optional - Later)

After successful training, you can:
1. Implement FastAPI routes (`backend/api/routes.py`)
2. Create Docker containers
3. Set up CI/CD pipeline
4. Integrate with Makerkit frontend

---

## Quick Commands Reference

### Activate Environment
```powershell
cd "c:\Users\Amine EL-Hend\Documents\GitHub\RadiKal"
.\venv\Scripts\Activate.ps1
```

### Check GPU
```powershell
nvidia-smi
```

### Run Tests
```powershell
cd backend
pytest tests/ -v
```

### Start Training
```powershell
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

### Start MLflow
```powershell
cd backend
mlflow ui  # Access at http://localhost:5000
```

### Monitor GPU Usage
```powershell
nvidia-smi -l 1  # Updates every second
```

---

## Troubleshooting

### Issue: CUDA Out of Memory
**Solution**: Reduce batch_size in `configs/train_config.json` from 8 to 4 or 6

### Issue: PyTorch not using GPU
**Solution**: 
```powershell
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Slow data loading
**Solution**: 
- Move data to SSD if on HDD
- Increase `num_workers` in config (try 4 or 8)

### Issue: Training crashes
**Solution**:
- Close GPU-intensive apps (Chrome, Spotify, etc.)
- Check `nvidia-smi` for other processes
- Reduce batch_size

---

## Expected Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Environment Setup | 10-15 min | ⏳ TODO |
| Dataset Preparation | 30-60 min | ⏳ TODO |
| System Testing | 15 min | ⏳ TODO |
| Model Training | 3-5 hours | ⏳ TODO |
| Evaluation | 30 min | ⏳ TODO |
| **TOTAL** | **~5-7 hours** | |

---

## Success Criteria

✅ PyTorch detects RTX 4050
✅ All tests pass
✅ Training starts without errors
✅ GPU utilization >90% during training
✅ Training completes with mAP@0.5 > 0.5
✅ XAI methods generate heatmaps
✅ Model calibration improves ECE

---

## Next Steps After Training

1. Generate XAI explanations for test images
2. Create visualization dashboard
3. Export reports (PDF/Excel)
4. Deploy with FastAPI
5. Integrate with Makerkit frontend

---

**Ready to start?** 
Begin with Phase 1: Environment Setup!
