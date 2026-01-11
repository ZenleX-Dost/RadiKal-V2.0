# 🚀 Quick Start: SAM2 Integration

## Install SAM2 in 3 Steps

### Option 1: Automated Setup (Windows)
```powershell
.\setup_sam2.ps1
```

### Option 2: Manual Setup

#### Step 1: Install Dependencies
```bash
cd backend
pip install segment-anything-2 timm
```

#### Step 2: Download SAM2 Checkpoint
```bash
# Create directory
mkdir -p models/sam2
cd models/sam2

# Download (choose one)
# Tiny (fast, testing)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt

# Small (RECOMMENDED for production)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_small.pt

# Base (better accuracy)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt

# Large (best accuracy)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_large.pt
```

#### Step 3: Test
```bash
cd backend
python test_sam2_integration.py
```

---

## Usage Examples

### API Endpoint
```bash
# Hybrid analysis (classification + segmentation)
curl -X POST "http://localhost:8000/api/xai-qc/analyze-hybrid?mode=hybrid" \
  -F "file=@defect_image.jpg"

# Classification only (fast)
curl -X POST "http://localhost:8000/api/xai-qc/analyze-hybrid?mode=classification" \
  -F "file=@defect_image.jpg"
```

### Python Code
```python
from core.models.hybrid_defect_analyzer import HybridDefectAnalyzer
from PIL import Image
import numpy as np

# Initialize
analyzer = HybridDefectAnalyzer(
    classifier_path="models/yolo/classification_defect_focused/weights/best.pt",
    segmenter_size="small",
    device='cuda'
)

# Analyze
image = np.array(Image.open("defect.jpg").convert('RGB'))
result = analyzer.analyze(image, mode='hybrid')

# Results
print(f"Type: {result['classification']['predicted_class_name']}")
print(f"Confidence: {result['classification']['confidence']:.3f}")
print(f"Coverage: {result['segmentation']['coverage_percent']:.2f}%")
```

---

## What You Get

### Before (YOLOv8 Only)
- ✅ Defect type identification
- ❌ No precise location

### After (YOLOv8 + SAM2)
- ✅ Defect type identification
- ✅ Pixel-level masks
- ✅ Bounding boxes
- ✅ Centroid locations
- ✅ Coverage metrics

---

## Documentation

- **Full Guide**: [docs/SAM2_INTEGRATION.md](docs/SAM2_INTEGRATION.md)
- **Implementation Summary**: [SAM2_IMPLEMENTATION_SUMMARY.md](SAM2_IMPLEMENTATION_SUMMARY.md)
- **Project Docs**: [RADIKAL_COMPLETE_DOCUMENTATION.md](RADIKAL_COMPLETE_DOCUMENTATION.md)

---

## Model Comparison

| Size | Speed | VRAM | Use Case |
|------|-------|------|----------|
| Tiny | ⚡⚡⚡ | ~2GB | Testing |
| **Small** | ⚡⚡ | ~4GB | **Production** ⭐ |
| Base | ⚡ | ~6GB | High accuracy |
| Large | 🐌 | ~8GB | Maximum accuracy |

---

## Troubleshooting

**SAM2 not found?**
```bash
pip install segment-anything-2
```

**Checkpoint missing?**
```bash
Download from: https://github.com/facebookresearch/segment-anything-2/tree/main/checkpoints
```

**Out of memory?**
- Use `tiny` or `small` model
- Switch to CPU: `device='cpu'`

---

## Status

✅ **Ready for Production**

The system gracefully falls back to classification-only if SAM2 is not available.

**Questions?** See [SAM2_INTEGRATION.md](docs/SAM2_INTEGRATION.md)
