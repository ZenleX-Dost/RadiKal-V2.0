# SAM2 Integration for RadiKal XAI Quality Control

## Overview

RadiKal now supports **dual-model defect analysis** combining:

1. **YOLOv8 Classification** - Identifies defect type (LP, PO, CR, ND)
2. **SAM2 Segmentation** - Provides precise pixel-level defect localization

This hybrid approach offers:
- **Fast classification** for defect type identification
- **Precise segmentation** for exact defect location and boundaries
- **Enhanced XAI** with segmentation overlays
- **Flexible modes** (classification-only, segmentation-only, or hybrid)

---

## Architecture

```
Input Image
    ↓
    ├─→ YOLOv8 Classifier → Defect Type (LP/PO/CR/ND) + Confidence
    │                        ↓
    └─→ SAM2 Segmenter ───→ Pixel Mask + Bounding Box + Location
                             ↓
                        Unified Output:
                        - Classification
                        - Segmentation
                        - XAI Heatmaps
                        - Metrics
```

---

## Installation

### 1. Install SAM2

```bash
cd backend

# Option 1: PyPI (when available)
pip install segment-anything-2

# Option 2: From source (recommended)
pip install git+https://github.com/facebookresearch/segment-anything-2.git

# Also install required dependencies
pip install timm
```

### 2. Download SAM2 Model Checkpoints

SAM2 requires pre-trained weights. Download from [SAM2 GitHub](https://github.com/facebookresearch/segment-anything-2/tree/main/checkpoints):

```bash
# Create models directory
mkdir -p models/sam2
cd models/sam2

# Download checkpoint (choose one based on your needs)

# Tiny (fastest, good for testing)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt

# Small (balanced)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_small.pt

# Base Plus (better accuracy)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt

# Large (best accuracy, slowest)
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_large.pt
```

### 3. Update Requirements

Already updated in `backend/requirements.txt`:
```txt
# Segmentation Models
segment-anything-2  # SAM2 for defect segmentation
timm  # Vision models library (required by SAM2)
```

---

## Usage

### API Endpoints

#### New Endpoint: `/api/xai-qc/analyze-hybrid`

**POST** request with image file

**Query Parameters:**
- `mode`: Analysis mode (`classification`, `segmentation`, `hybrid`) - default: `hybrid`
- `enable_segmentation`: Enable SAM2 (boolean) - default: `true`
- `segmentation_guidance`: Strategy (`auto`, `center`, `grid`) - default: `auto`
- `methods`: XAI methods (comma-separated) - default: `gradcam`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/xai-qc/analyze-hybrid?mode=hybrid&segmentation_guidance=auto" \
  -F "file=@defect_image.jpg"
```

**Response:**
```json
{
  "image_id": "uuid-here",
  "explanations": [
    {
      "method": "gradcam",
      "heatmap_base64": "...",
      "confidence_score": 0.95
    },
    {
      "method": "sam2_segmentation",
      "heatmap_base64": "...",
      "confidence_score": 0.88
    }
  ],
  "classification": {
    "predicted_class": 0,
    "predicted_class_name": "LP",
    "predicted_class_full_name": "Lack of Penetration",
    "confidence": 0.95,
    "all_probabilities": {
      "LP": 0.95,
      "PO": 0.03,
      "CR": 0.01,
      "ND": 0.01
    },
    "is_defect": true,
    "defect_type": "LP"
  },
  "segmentation": {
    "has_segmentation": true,
    "num_segments": 1,
    "bbox": [120, 80, 200, 150],
    "area": 30000,
    "centroid": [220.5, 155.3],
    "coverage_percent": 7.32
  },
  "metadata": {
    "mode": "hybrid",
    "sam2_enabled": true,
    "segmentation_guidance": "auto",
    "image_size": [640, 640]
  }
}
```

### Python API

#### Hybrid Analyzer

```python
from core.models.hybrid_defect_analyzer import HybridDefectAnalyzer
from PIL import Image
import numpy as np

# Initialize analyzer
analyzer = HybridDefectAnalyzer(
    classifier_path="models/yolo/classification_defect_focused/weights/best.pt",
    segmenter_size="small",  # tiny, small, base, large
    device='cuda',  # or 'cpu'
    nd_threshold=0.7,
    enable_sam2=True
)

# Load image
image = np.array(Image.open("defect.jpg").convert('RGB'))

# Analyze in hybrid mode
result = analyzer.analyze(
    image=image,
    mode='hybrid',  # or 'classification', 'segmentation'
    return_visualization=True,
    segmentation_guidance='auto'  # or 'center', 'grid'
)

# Access results
print(f"Defect Type: {result['classification']['predicted_class_name']}")
print(f"Confidence: {result['classification']['confidence']:.3f}")

if result['segmentation']['has_segmentation']:
    print(f"Segments: {result['segmentation']['num_segments']}")
    print(f"Coverage: {result['segmentation']['coverage_percent']:.2f}%")
    print(f"Centroid: {result['segmentation']['centroid']}")
```

#### Classification Only

```python
# Fast classification without segmentation
result = analyzer.classify_only(image)
print(result['classification'])
```

#### Segmentation Only

```python
# Detailed segmentation without classification
result = analyzer.segment_only(image)
print(result['segmentation'])
```

---

## Analysis Modes

### 1. Classification Mode
**Speed**: ⚡⚡⚡ Fast  
**Use Case**: Quick defect type identification

- Uses YOLOv8 only
- Returns defect class, confidence, probabilities
- No pixel-level localization

### 2. Segmentation Mode
**Speed**: ⚡⚡ Medium  
**Use Case**: Detailed mask generation

- Uses SAM2 only
- Returns pixel masks, bounding boxes
- No defect classification

### 3. Hybrid Mode (Recommended)
**Speed**: ⚡ Slower but comprehensive  
**Use Case**: Complete defect analysis

- Uses both YOLOv8 and SAM2
- Classification guides segmentation
- Complete defect profile

---

## Segmentation Guidance Strategies

### Auto (Recommended)
- **For Defects**: Uses image center as point prompt
- **For ND**: Performs automatic segmentation
- Best balance of speed and accuracy

### Center
- Always uses center point prompt
- Good for centrally-located defects
- Fast and consistent

### Grid
- Grid-based automatic segmentation
- Finds all possible masks
- Slower but most thorough

---

## Testing

Run the comprehensive test suite:

```bash
cd backend
python test_sam2_integration.py
```

**Test Coverage:**
1. ✓ SAM2 import verification
2. ✓ YOLOv8 classifier functionality
3. ✓ SAM2 segmenter functionality
4. ✓ Hybrid analyzer integration
5. ✓ Real image analysis (if test images available)

---

## Model Performance

### YOLOv8 Classification
- **Speed**: ~50ms per image (GPU)
- **Accuracy**: 95%+ on RadiKal dataset
- **Classes**: LP, PO, CR, ND

### SAM2 Segmentation
| Model Size | Speed (GPU) | Accuracy | VRAM |
|------------|-------------|----------|------|
| Tiny       | ~200ms      | Good     | ~2GB |
| Small      | ~300ms      | Better   | ~4GB |
| Base       | ~500ms      | Great    | ~6GB |
| Large      | ~800ms      | Best     | ~8GB |

### Hybrid (Combined)
- **Total Time**: ~250-850ms (depending on SAM2 size)
- **Recommended**: Small model for production

---

## Configuration

### Hybrid Analyzer Options

```python
analyzer = HybridDefectAnalyzer(
    classifier_path="path/to/yolov8.pt",
    segmenter_size="small",  # tiny, small, base, large
    segmenter_path=None,  # Optional custom checkpoint
    device='cuda',  # or 'cpu', None (auto)
    nd_threshold=0.7,  # No Defect confidence threshold
    enable_sam2=True  # Set False to disable segmentation
)
```

### Runtime Configuration

```python
# Enable/disable segmentation at runtime
analyzer.enable_segmentation(True)  # Enable
analyzer.enable_segmentation(False)  # Disable

# Get model info
info = analyzer.get_model_info()
print(info)
```

---

## Troubleshooting

### SAM2 Not Found
```
ImportError: No module named 'sam2'
```
**Solution**: Install SAM2
```bash
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

### Checkpoint Not Found
```
FileNotFoundError: SAM2 checkpoint not found
```
**Solution**: Download checkpoint
```bash
mkdir -p models/sam2
cd models/sam2
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_small.pt
```

### Out of Memory
```
RuntimeError: CUDA out of memory
```
**Solutions**:
1. Use smaller SAM2 model (`tiny` or `small`)
2. Process on CPU: `device='cpu'`
3. Reduce image size before processing
4. Disable segmentation: `enable_sam2=False`

### Slow Performance
**Solutions**:
1. Use GPU if available
2. Use smaller SAM2 model
3. Use `classification` mode only
4. Batch process images

---

## Best Practices

### Production Deployment
1. **Model Size**: Use `small` SAM2 for best speed/accuracy balance
2. **Device**: Use GPU when available
3. **Guidance**: Use `auto` strategy for most cases
4. **Caching**: Cache model instances (don't reload per request)
5. **Timeout**: Set appropriate timeouts for segmentation

### Development/Testing
1. **Model Size**: Use `tiny` SAM2 for faster iteration
2. **Device**: Can use CPU for testing
3. **Guidance**: Try different strategies
4. **Logging**: Enable detailed logging

### Accuracy Optimization
1. Use `base` or `large` SAM2 models
2. Use `grid` guidance for thorough segmentation
3. Adjust confidence thresholds based on use case
4. Fine-tune YOLOv8 on your specific defect types

---

## API Integration Example

### Frontend (JavaScript/TypeScript)

```typescript
async function analyzeDefect(imageFile: File) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch(
    'http://localhost:8000/api/xai-qc/analyze-hybrid?mode=hybrid&segmentation_guidance=auto',
    {
      method: 'POST',
      body: formData
    }
  );
  
  const result = await response.json();
  
  // Display classification
  console.log(`Defect: ${result.classification.predicted_class_name}`);
  console.log(`Confidence: ${result.classification.confidence}`);
  
  // Display segmentation
  if (result.segmentation.has_segmentation) {
    console.log(`Coverage: ${result.segmentation.coverage_percent}%`);
    console.log(`Location: ${result.segmentation.centroid}`);
  }
  
  // Display visualizations
  document.getElementById('heatmap').src = 
    `data:image/png;base64,${result.aggregated_heatmap}`;
}
```

---

## Comparison: YOLOv8 Only vs Hybrid

| Feature | YOLOv8 Only | Hybrid (YOLOv8 + SAM2) |
|---------|-------------|------------------------|
| Defect Type | ✓ | ✓ |
| Confidence | ✓ | ✓ |
| Defect Location | ✗ | ✓ |
| Pixel Mask | ✗ | ✓ |
| Bounding Box | ✗ | ✓ |
| Coverage % | ✗ | ✓ |
| Centroid | ✗ | ✓ |
| Speed | Fast (~50ms) | Medium (~300ms) |
| VRAM | ~2GB | ~4GB (small) |

**Recommendation**: Use hybrid mode for production, classification mode for real-time monitoring.

---

## Future Enhancements

- [ ] Multi-defect segmentation (segment multiple defects per image)
- [ ] Defect severity estimation based on mask size
- [ ] Temporal tracking (track defect evolution across multiple images)
- [ ] 3D visualization of defect depth
- [ ] Custom prompt points from user input
- [ ] Interactive segmentation refinement

---

## References

- [SAM2 GitHub](https://github.com/facebookresearch/segment-anything-2)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [RadiKal Documentation](./RADIKAL_COMPLETE_DOCUMENTATION.md)

---

## Support

For issues or questions:
1. Check this documentation
2. Run `python test_sam2_integration.py` for diagnostics
3. Review backend logs
4. Open GitHub issue with test results

---

**Last Updated**: 2026-01-09  
**Version**: 2.0.0  
**Author**: RadiKal Team
