# RIAWELC Dataset - RadiKal XAI Integration

## 📊 Dataset Information

**Name**: RIAWELC (Radiographic Images for Automatic Weld Defects Classification)

**Source**: Research dataset for weld defect classification

**Total Images**: 24,407 radiographic images
- Format: PNG (224x224 pixels, 8-bit grayscale)
- Quality: High-quality digitalized radiographic images

---

## 🎯 Defect Classes

The dataset contains **4 classes** of weld defects:

| Class | Original Name | Code | Description | Training | Validation | Testing | Total |
|-------|---------------|------|-------------|----------|------------|---------|-------|
| 0 | **No Defect (ND)** | NoDifetto | Clean welds without defects | 3,900 | 1,500 | 600 | **6,000** |
| 1 | **Lack of Penetration (LP)** | Difetto1 | Incomplete weld penetration | 4,962 | 1,908 | 765 | **7,635** |
| 2 | **Porosity (PO)** | Difetto2 | Gas pockets/voids in weld | 4,108 | 1,580 | 632 | **6,320** |
| 3 | **Cracks (CR)** | Difetto4 | Structural cracks in weld | 2,893 | 1,113 | 446 | **4,452** |

**Total**: 15,863 training + 6,101 validation + 2,443 testing = **24,407 images**

---

## 🔬 Defect Descriptions

### 1. Lack of Penetration (LP) - Difetto1
- **Severity**: High
- **Description**: Occurs when the weld metal fails to completely penetrate the joint
- **Impact**: Weakens structural integrity, reduces load-bearing capacity
- **Detection**: Shows as incomplete fusion at the weld root
- **XAI Focus**: Should highlight areas where fusion is incomplete

### 2. Porosity (PO) - Difetto2
- **Severity**: Medium
- **Description**: Gas pockets or voids trapped in the solidified weld
- **Impact**: Reduces weld strength, can propagate cracks
- **Detection**: Appears as dark circular/irregular voids in radiographs
- **XAI Focus**: Should highlight bubble-like defect regions

### 3. Cracks (CR) - Difetto4
- **Severity**: Critical
- **Description**: Linear discontinuities in the weld material
- **Impact**: Severe structural weakness, high failure risk
- **Detection**: Shows as sharp linear features in radiographs
- **XAI Focus**: Should highlight crack propagation paths

### 4. No Defect (ND) - NoDifetto
- **Description**: Clean, defect-free welds
- **Purpose**: Baseline for comparison, reduces false positives
- **XAI Focus**: Should show uniform activation across weld region

---

## 📁 Dataset Structure

### Original Structure (DATA/)
```
DATA/
├── training/
│   ├── Difetto1/    (4,962 images - LP)
│   ├── Difetto2/    (4,108 images - PO)
│   ├── Difetto4/    (2,893 images - CR)
│   └── NoDifetto/   (3,900 images - ND)
├── validation/
│   ├── Difetto1/    (1,908 images - LP)
│   ├── Difetto2/    (1,580 images - PO)
│   ├── Difetto4/    (1,113 images - CR)
│   └── NoDifetto/   (1,500 images - ND)
├── testing/
│   ├── Difetto1/    (765 images - LP)
│   ├── Difetto2/    (632 images - PO)
│   ├── Difetto4/    (446 images - CR)
│   └── NoDifetto/   (600 images - ND)
└── README.md
```

### Converted Structure (backend/data/)
```
backend/data/
├── train/
│   ├── images/           (15,863 images)
│   └── annotations/
│       └── annotations.json  (COCO format)
├── val/
│   ├── images/           (6,101 images)
│   └── annotations/
│       └── annotations.json
├── test/
│   ├── images/           (2,443 images)
│   └── annotations/
│       └── annotations.json
└── dataset_metadata.json
```

---

## 📊 Class Distribution Analysis

### Balance Analysis
- **Most Common**: Lack of Penetration (31.3%) - Makes sense, common welding issue
- **Least Common**: Cracks (18.2%) - Critical but less frequent
- **Well Balanced**: Dataset is reasonably balanced (18-31% per class)
- **No Defect**: 24.6% - Good baseline proportion

### Split Distribution
| Split | No Defect | LP | PO | CR | Total |
|-------|-----------|----|----|-----|-------|
| **Train** | 24.6% | 31.3% | 25.9% | 18.2% | 100% |
| **Val** | 24.6% | 31.3% | 25.9% | 18.2% | 100% |
| **Test** | 24.6% | 31.3% | 25.9% | 18.2% | 100% |

✅ **Excellent**: All splits maintain the same class distribution!

---

## 🎓 Citations

If you use the RIAWELC dataset or this RadiKal XAI integration, please cite:

### Original Dataset Papers:

**[1] ICMECE 2022 Conference Paper:**
```bibtex
@inproceedings{totino2022riawelc,
  title={RIAWELC: A Novel Dataset of Radiographic Images for Automatic Weld Defects Classification},
  author={Totino, Benito and Spagnolo, Fanny and Perri, Stefania},
  booktitle={Proceedings of the Interdisciplinary Conference on Mechanics, Computers and Electrics (ICMECE 2022)},
  year={2022},
  month={October},
  address={Barcelona, Spain}
}
```

**[2] Manufacturing Letters Journal:**
```bibtex
@article{perri2023welding,
  title={Welding Defects Classification Through a Convolutional Neural Network},
  author={Perri, Stefania and Spagnolo, Fanny and Frustaci, Fabio and Corsonello, Pasquale},
  journal={Manufacturing Letters},
  publisher={Elsevier},
  note={In Press}
}
```

---

## 🚀 Usage with RadiKal XAI

### Quick Start
```powershell
# 1. Dataset already converted (✅ done!)
cd backend

# 2. Verify dataset
python -c "import json; print(json.dumps(json.load(open('data/dataset_metadata.json')), indent=2))"

# 3. Start training
python scripts/train.py --config configs/train_config.json --gpu 0

# 4. Monitor with MLflow
mlflow ui  # Open http://localhost:5000
```

### Expected Training Performance

With RTX 4050 (6GB VRAM) on 24,407 images:

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| **Training Time** | 4-6 hours | ~50 epochs, batch size 8 |
| **mAP@0.5** | 0.75-0.90 | High-quality dataset |
| **Precision** | 0.80-0.92 | Clean labels |
| **Recall** | 0.75-0.88 | Balanced classes |
| **F1 Score** | 0.78-0.90 | Per-class F1 |
| **GPU Utilization** | 85-95% | Efficient training |

---

## 🎯 XAI Visualization Focus

### What to Look For in Heatmaps:

**Lack of Penetration (LP)**:
- XAI should highlight weld root areas
- Focus on incomplete fusion zones
- Grad-CAM: Bright regions at fusion boundaries

**Porosity (PO)**:
- XAI should highlight void regions
- Multiple small circular hotspots
- SHAP: Strong contribution from void pixels

**Cracks (CR)**:
- XAI should highlight linear crack paths
- Sharp, elongated activation regions
- LIME: Clear crack propagation visualization

**No Defect (ND)**:
- XAI should show uniform, low activation
- No specific focus regions
- Validates model isn't overfitting to artifacts

---

## 📈 Recommended Training Strategy

### Phase 1: Initial Training (2-3 hours)
```powershell
python scripts/train.py --config configs/train_config.json --gpu 0 --epochs 30
```
- Learn basic defect patterns
- Monitor validation mAP

### Phase 2: Fine-tuning (1-2 hours)
```powershell
python scripts/train.py --config configs/train_config.json --gpu 0 --epochs 50 --lr 0.0001
```
- Refine decision boundaries
- Improve per-class performance

### Phase 3: XAI Validation (30 min)
```powershell
python scripts/generate_xai_explanations.py --model models/checkpoints/best_model.pth
```
- Generate heatmaps for all XAI methods
- Validate explanations make sense
- Check consensus scores

---

## 🔍 Data Quality Notes

### Strengths:
- ✅ Large dataset (24K+ images)
- ✅ Real radiographic images (not synthetic)
- ✅ Balanced class distribution
- ✅ Consistent image size (224x224)
- ✅ Professional digitalization quality
- ✅ Academic validation (published papers)
- ✅ Proper train/val/test splits

### Considerations:
- Images are 224x224 (relatively small) - May want to check if upscaling improves detection
- 8-bit grayscale - Standard for radiographs
- Missing class: Difetto3 - Not in dataset, naming gap is intentional
- Focus: Weld defects specifically - May not generalize to other defect types

---

## 🛠️ Integration Status

- [x] Dataset converted to COCO format
- [x] Class mappings defined
- [x] Metadata created
- [x] Documentation complete
- [x] Ready for training

---

## 📞 Dataset Contact

For questions about the RIAWELC dataset, contact the original authors:
- Benito Totino
- Fanny Spagnolo  
- Stefania Perri
- Pasquale Corsonello

**Institution**: Research institution (check papers for current affiliations)

---

## 🎉 Ready to Train!

Your dataset is now fully integrated and ready for RadiKal XAI training:

```powershell
# Start training now!
cd backend
python scripts/train.py --config configs/train_config.json --gpu 0
```

**Estimated completion**: 4-6 hours  
**Expected mAP**: 0.75-0.90  
**GPU**: RTX 4050 (6GB) - Perfect for this dataset!

Good luck! 🚀
