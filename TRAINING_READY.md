# 🚀 RadiKal Training Ready - RIAWELC Dataset

## ✅ System Status: READY TO TRAIN

Your RadiKal XAI system is fully configured and ready to start training on the RIAWELC weld defect dataset!

---

## 📊 Dataset Information

**RIAWELC - Radiographic Images for Automatic Weld Defects Classification**

- **Total Images**: 24,407 radiographic images (224×224, 8-bit grayscale PNG)
- **Training Set**: 15,863 images → 11,963 annotations
- **Validation Set**: 6,101 images → 4,601 annotations
- **Test Set**: 2,443 images → 1,843 annotations

### 4 Defect Classes:
1. **No Defect (ND)** - Clean, defect-free welds
2. **Lack of Penetration (LP/Difetto1)** - Incomplete weld penetration
3. **Porosity (PO/Difetto2)** - Gas pockets or voids in weld
4. **Cracks (CR/Difetto4)** - Structural cracks in weld material

### Academic Citation:
```
Benito Totino, Fanny Spagnolo, Stefania Perri
RIAWELC: A Novel Dataset of Radiographic Images for Automatic Weld Defects Classification
International Conference on Mechanical, Electric and Control Engineering (ICMECE), 2022
```

---

## 🖥️ Hardware Configuration

- **GPU**: NVIDIA GeForce RTX 4050 Laptop GPU
- **VRAM**: 6 GB
- **CUDA**: Version 12.1
- **PyTorch**: 2.5.1+cu121
- **Driver**: 581.29

---

## ⚙️ Training Configuration

**Updated Settings** (backend/configs/train_config.json):
- ✅ Image size: 224×224 (matches RIAWELC)
- ✅ Number of classes: 4 (ND, LP, PO, CR)
- ✅ Batch size: 16 (optimized for RTX 4050 + 224×224)
- ✅ Epochs: 50
- ✅ Learning rate: 0.0001
- ✅ Mixed precision: Enabled
- ✅ Data paths: Corrected to include /annotations/ subdirectory

**Expected Training Time**: 4-6 hours  
**Expected Performance**: mAP 0.75-0.90

---

## 🎯 How to Start Training

### Step 1: Open 3 PowerShell Terminals

**Terminal 1 - MLflow Tracking UI:**
```powershell
cd backend
mlflow ui
```
Then open browser to: http://localhost:5000

**Terminal 2 - Start Training:**
```powershell
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

**Terminal 3 - Monitor GPU (Optional):**
```powershell
nvidia-smi -l 1
```

---

## 📈 What to Expect During Training

### Metrics to Monitor in MLflow:
- **mAP (mean Average Precision)**: Target 0.75-0.90
- **Precision/Recall**: Per-class performance
- **F1 Score**: Balanced metric
- **Loss Curves**: Should steadily decrease

### Per-Class Performance Expectations:
- **No Defect (ND)**: Easiest class (mAP ~0.90-0.95)
- **Lack of Penetration (LP)**: Good detectability (mAP ~0.75-0.85)
- **Porosity (PO)**: Moderate difficulty (mAP ~0.70-0.80)
- **Cracks (CR)**: Most challenging (mAP ~0.65-0.75)

### Training Progress:
- **Epochs 1-10**: Initial learning, loss drops rapidly
- **Epochs 10-30**: Steady improvement
- **Epochs 30-50**: Fine-tuning, convergence

---

## 🔍 XAI Visualization Guidelines

### Expected Heatmap Patterns:

**Lack of Penetration (LP):**
- Linear/elongated horizontal patterns
- Focus on weld root area (center of weld joint)
- Continuous activation regions

**Porosity (PO):**
- Circular/scattered activation spots
- Multiple small hotspots across weld area
- Irregular distribution pattern

**Cracks (CR):**
- Linear, high-intensity streaks
- Sharp, well-defined edges
- Perpendicular or diagonal to weld direction

**No Defect (ND):**
- Low, diffuse activation
- Uniform distribution
- No concentrated hotspots

---

## 📁 File Structure

```
RadiKal/
├── backend/
│   ├── data/
│   │   ├── train/
│   │   │   ├── images/           (15,863 PNG files)
│   │   │   └── annotations/
│   │   │       └── annotations.json
│   │   ├── val/
│   │   │   ├── images/           (6,101 PNG files)
│   │   │   └── annotations/
│   │   │       └── annotations.json
│   │   ├── test/
│   │   │   ├── images/           (2,443 PNG files)
│   │   │   └── annotations/
│   │   │       └── annotations.json
│   │   └── dataset_metadata.json
│   ├── configs/
│   │   └── train_config.json     (✅ UPDATED)
│   ├── scripts/
│   │   ├── train.py              (Ready to run)
│   │   └── convert_radikal_dataset.py
│   └── models/
│       └── checkpoints/          (Will be created)
├── DATA/
│   └── README.md                 (RIAWELC documentation)
├── RIAWELC_DATASET_INFO.md      (✅ NEW)
└── TRAINING_READY.md            (✅ THIS FILE)
```

---

## 🎓 Post-Training Steps

After training completes (~4-6 hours):

1. **Evaluate on Test Set**
   ```powershell
   cd backend
   python scripts/evaluate.py --checkpoint models/checkpoints/best_model.pth
   ```

2. **Generate XAI Explanations**
   ```powershell
   python scripts/generate_explanations.py --checkpoint models/checkpoints/best_model.pth --num_samples 100
   ```

3. **Start Backend API**
   ```powershell
   uvicorn app.main:app --reload
   ```

4. **Test Frontend Integration**
   ```powershell
   cd ../frontend
   npm run dev
   ```

---

## 📝 Documentation Files

- **RIAWELC_DATASET_INFO.md**: Comprehensive dataset documentation
- **DATASET_RECOMMENDATIONS.md**: Alternative datasets (if needed)
- **CHECKLIST.md**: Project progress tracking
- **DATA/README.md**: Original RIAWELC documentation

---

## 🚨 Troubleshooting

### If training crashes with OOM (Out of Memory):
```json
// In backend/configs/train_config.json, reduce batch size:
"batch_size": 8  // or even 4
```

### If validation loss plateaus early:
- Check for overfitting
- Increase augmentation strength
- Reduce learning rate

### If class imbalance issues:
- Check class distribution in RIAWELC_DATASET_INFO.md
- Consider weighted loss or focal loss

---

## ✨ What's Complete

- ✅ Frontend 60-70% complete (dashboard, metrics, history, settings)
- ✅ Backend 100% complete (FastAPI v1.0.0 production ready)
- ✅ PyTorch CUDA 12.1 installed and verified
- ✅ RTX 4050 GPU working (6GB VRAM)
- ✅ RIAWELC dataset converted to COCO format (24,407 images)
- ✅ Dataset documentation created
- ✅ Training configuration updated for RIAWELC
- ✅ MLflow tracking configured
- ✅ DVC for data versioning set up

---

## 🎯 Ready to Train!

Everything is configured and ready. Just run the commands in **Step 1** above to start training!

**Estimated Time to First Results**: 4-6 hours  
**Expected Final Performance**: mAP 0.75-0.90

Good luck! 🚀

---

*Generated on 2025-01-14 | RadiKal XAI System v1.0*
