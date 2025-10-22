# RadiKal Defect Classification System

## Weld Defect Classes

The RadiKal system detects 3 types of weld defects plus normal welds using YOLOv8s model (99.88% mAP@0.5):

### Class Mapping

| Label | Code | Full Name | Description |
|-------|------|-----------|-------------|
| 0 | **LP** | Lack of Penetration | Incomplete fusion where the weld metal fails to penetrate the joint completely |
| 1 | **PO** | Porosity | Gas pockets or voids trapped in the weld metal during solidification |
| 2 | **CR** | Cracks | Linear discontinuities caused by rupture of the weld metal |
| 3 | **ND** | No Defect | Clean weld with no detectable defects |

## Severity Levels

Each detected defect is assigned a severity level based on confidence score:

| Severity | Threshold | Color Code | Action Required |
|----------|-----------|------------|-----------------|
| **Critical** | ≥ 90% | 🔴 Red | Immediate action required |
| **High** | ≥ 70% | 🟠 Orange | Significant concern, prompt attention needed |
| **Medium** | ≥ 50% | 🟡 Yellow | Monitor closely, plan corrective action |
| **Low** | < 50% | 🟢 Green | Minor issue, note for inspection |

## Model Performance

- **Architecture**: YOLOv8s (Small)
- **mAP@0.5**: 99.88%
- **mAP@0.75**: 98.56%
- **mAP (0.5:0.95)**: 99.74%
- **Dataset**: RadiKal Weld Defect Dataset
- **Training**: Transfer learning from COCO

## Usage in Code

### Frontend (TypeScript)
```typescript
const DEFECT_CLASSES: Record<number, string> = {
  0: 'LP',  // Lack of Penetration
  1: 'PO',  // Porosity
  2: 'CR',  // Cracks
  3: 'ND',  // No Defect
};
```

### Backend (Python)
```python
CLASS_NAMES = {
    0: "LP",  # Lack of Penetration
    1: "PO",  # Porosity
    2: "CR",  # Cracks
    3: "ND"   # No Defect
}
```

## Visual Display

In the dashboard, defects are displayed with:
- **Code**: Short 2-letter abbreviation (e.g., "LP")
- **Full Name**: Complete description (e.g., "Lack of Penetration")
- **Confidence**: Percentage score (0-100%)
- **Severity**: Color-coded level with emoji indicator
- **Bounding Box**: Visual overlay on image

## Historical Note

Previous class names were:
- Difetto1 → LP (Lack of Penetration)
- Difetto2 → PO (Porosity)
- Difetto4 → CR (Cracks)
- NoDifetto → ND (No Defect)

Updated: October 21, 2025
