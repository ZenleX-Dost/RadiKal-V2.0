# Frontend XAI Visualization - Complete Guide

## 📋 Overview

This guide covers the enhanced frontend visualization components for explainable AI (XAI) in the RadiKal application. These components provide operator-friendly interfaces for defect localization, severity assessment, and actionable recommendations.

## 🎯 Features

### 1. **DefectLocalizationView** - Interactive Visualization
- **Heatmap Overlay**: Grad-CAM visualization showing where the AI detected defects
- **Zoom & Pan Controls**: Interactive inspection of defect regions
- **Region Highlighting**: Click and hover to highlight detected defect areas
- **Coverage Metrics**: Percentage coverage and intensity for each region
- **Multi-view Display**: Toggle between heatmap and overlay modes

### 2. **OperatorMessaging** - Clear Communication
- **DefectBadge**: Color-coded severity badges with tooltips
- **SeverityIndicator**: Visual bars showing risk level (1-5 scale)
- **ActionRecommendation**: Actionable next steps based on severity
- **DefectSummaryCard**: Comprehensive at-a-glance defect information

### 3. **XAIExplanations** - Complete Analysis
- Combines all components into a unified interface
- Displays prediction confidence, probabilities, and metadata
- Advanced details panel with computation metrics
- Responsive design for mobile and desktop

---

## 🏗️ Architecture

### Component Hierarchy
```
XAIExplanations (Main Container)
├── DefectBadge (Header)
├── DefectSummaryCard (Overview)
├── DefectLocalizationView (Visualization)
│   ├── Heatmap Display
│   ├── Canvas Overlay (Interactive Regions)
│   ├── Zoom Controls
│   ├── Region Cards
│   └── Class Probabilities
└── ActionRecommendation (Next Steps)
```

### Data Flow
```
Backend API (/explain)
    ↓
ExplanationResponse (with metadata)
    ↓
XAIExplanations Component
    ↓
├→ DefectLocalizationView
├→ OperatorMessaging Components
└→ User Interactions
```

---

## 📦 Components Reference

### DefectLocalizationView

**Purpose**: Interactive visualization of defect locations with Grad-CAM heatmaps.

**Props**:
```typescript
interface DefectLocalizationViewProps {
  explanation: ExplanationResponse;  // Full explanation from backend
  originalImage?: string;            // Base64 original image (optional)
  onRegionClick?: (region: DefectRegion) => void;  // Callback for region clicks
}
```

**Features**:
- ✅ Heatmap/overlay toggle
- ✅ Zoom controls (0.5x - 3x)
- ✅ Interactive canvas with region bounding boxes
- ✅ Hover highlighting
- ✅ Click to select regions
- ✅ Coverage and intensity metrics
- ✅ Class probability bars

**Usage**:
```tsx
import DefectLocalizationView from '@/components/DefectLocalizationView';

<DefectLocalizationView
  explanation={explanationResponse}
  originalImage={base64Image}
  onRegionClick={(region) => console.log('Region clicked:', region)}
/>
```

---

### DefectBadge

**Purpose**: Display defect type with severity-based coloring and tooltips.

**Props**:
```typescript
interface DefectBadgeProps {
  prediction: PredictionInfo;  // Prediction with class, confidence, severity
  size?: 'sm' | 'md' | 'lg';   // Badge size (default: 'md')
  showTooltip?: boolean;       // Show hover tooltip (default: true)
}
```

**Severity Colors**:
- 🔴 **CRITICAL**: Red background (Cracks, LP)
- 🟠 **HIGH**: Orange background
- 🟡 **MEDIUM**: Yellow background (Porosity)
- 🔵 **LOW**: Blue background
- 🟢 **ACCEPTABLE**: Green background (No Defect)

**Usage**:
```tsx
import { DefectBadge } from '@/components/OperatorMessaging';

<DefectBadge 
  prediction={metadata.prediction} 
  size="lg" 
  showTooltip={true} 
/>
```

---

### SeverityIndicator

**Purpose**: Visual bar indicator showing risk level (1-5).

**Props**:
```typescript
interface SeverityIndicatorProps {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'ACCEPTABLE';
  confidence: number;     // 0.0 - 1.0
  showLabel?: boolean;    // Show text label (default: true)
}
```

**Severity Levels**:
- Level 5: CRITICAL (all 5 bars red)
- Level 4: HIGH (4 bars orange)
- Level 3: MEDIUM (3 bars yellow)
- Level 2: LOW (2 bars blue)
- Level 1: ACCEPTABLE (1 bar green)

**Usage**:
```tsx
import { SeverityIndicator } from '@/components/OperatorMessaging';

<SeverityIndicator 
  severity="CRITICAL" 
  confidence={0.987} 
  showLabel={true} 
/>
```

---

### ActionRecommendation

**Purpose**: Display actionable recommendations based on defect severity.

**Props**:
```typescript
interface ActionRecommendationProps {
  prediction: PredictionInfo;
  recommendation: string;
  onAccept?: () => void;   // Optional accept callback
  onReject?: () => void;   // Optional override callback
}
```

**Action Types by Severity**:
- **CRITICAL**: "Reject Weld" (Red alert)
- **HIGH**: "Review Required" (Orange warning)
- **MEDIUM**: "Assess & Document" (Yellow caution)
- **LOW**: "Monitor" (Blue info)
- **ACCEPTABLE**: "Accept Weld" (Green check)

**Usage**:
```tsx
import { ActionRecommendation } from '@/components/OperatorMessaging';

<ActionRecommendation
  prediction={metadata.prediction}
  recommendation={metadata.recommendation}
  onAccept={() => console.log('Accepted')}
  onReject={() => console.log('Overridden')}
/>
```

---

### DefectSummaryCard

**Purpose**: Comprehensive summary card with key information at a glance.

**Props**:
```typescript
interface DefectSummaryCardProps {
  prediction: PredictionInfo;
  locationDescription: string;
  numRegions: number;
}
```

**Contains**:
- Defect name with severity color header
- Confidence meter (progress bar)
- Severity indicator
- Location description
- Number of detected regions

**Usage**:
```tsx
import { DefectSummaryCard } from '@/components/OperatorMessaging';

<DefectSummaryCard
  prediction={metadata.prediction}
  locationDescription={metadata.location_description}
  numRegions={metadata.regions.length}
/>
```

---

## 🔧 Integration Guide

### Step 1: Install Dependencies

Ensure you have the required packages:
```bash
npm install lucide-react  # For icons
```

### Step 2: Update Types

The TypeScript types are already updated in `frontend/types/index.ts`:
- `ExplanationResponse` - Complete response with metadata
- `PredictionInfo` - Prediction details
- `DefectRegion` - Region coordinates and metrics
- `ExplanationMetadata` - Full metadata structure

### Step 3: Create Analysis Page

Use the example page at `frontend/app/xai-analysis/page.tsx`:
```tsx
import XAIExplanations from '@/components/XAIExplanations';

// In your component:
const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);

// After API call:
const response = await fetch('http://localhost:8000/api/explain', {
  method: 'POST',
  body: formData,
});
const result: ExplanationResponse = await response.json();
setExplanation(result);

// Render:
<XAIExplanations explanation={explanation} originalImage={imagePreview} />
```

### Step 4: Test the Integration

1. Start the backend server:
   ```bash
   cd backend
   python run_server.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to `http://localhost:3000/xai-analysis`

4. Upload a test image and verify all components display correctly

---

## 🎨 Styling & Customization

### Tailwind CSS Classes

All components use Tailwind CSS for styling. Key color schemes:

**Severity Colors**:
```css
CRITICAL: bg-red-600, border-red-700, text-red-900
HIGH: bg-orange-600, border-orange-700, text-orange-900
MEDIUM: bg-yellow-500, border-yellow-600, text-yellow-900
LOW: bg-blue-500, border-blue-600, text-blue-900
ACCEPTABLE: bg-green-600, border-green-700, text-green-900
```

**Interactive States**:
```css
Hover: hover:bg-gray-300, hover:border-blue-500
Active: border-red-500, bg-red-50
Disabled: disabled:bg-gray-400
```

### Customizing Colors

To change severity colors, edit the component files:

**DefectBadge** - `OperatorMessaging.tsx` line 27-33:
```typescript
const severityColors = {
  CRITICAL: 'bg-red-600 text-white border-red-700',
  // ... modify as needed
};
```

**ActionRecommendation** - `OperatorMessaging.tsx` line 128-158:
```typescript
const actionTypes = {
  CRITICAL: {
    color: 'red',  // Change this
    // ...
  },
};
```

---

## 🔍 User Interactions

### Zoom Controls
- **Zoom In**: Click "+" button or use mouse wheel
- **Zoom Out**: Click "-" button
- **Reset**: Click maximize icon
- **Range**: 0.5x to 3.0x

### Region Interaction
- **Hover**: Shows yellow border and coverage tooltip
- **Click**: Selects region (red border), triggers callback
- **Deselect**: Click outside regions

### View Modes
- **Heatmap Only**: Raw Grad-CAM visualization
- **Overlay Mode**: Heatmap blended with original image (default)
- **Toggle**: Click "Show/Hide Overlay" button

---

## 📊 Data Requirements

### Backend Response Format

The `/explain` endpoint must return:

```json
{
  "image_id": "uuid-string",
  "explanations": [
    {
      "method": "gradcam",
      "heatmap_base64": "base64-encoded-png",
      "confidence_score": 0.987
    },
    {
      "method": "overlay",
      "heatmap_base64": "base64-encoded-png",
      "confidence_score": 0.987
    }
  ],
  "aggregated_heatmap": "base64-encoded-png",
  "consensus_score": 0.987,
  "computation_time_ms": 123.45,
  "timestamp": "2025-10-23T10:00:00Z",
  "metadata": {
    "prediction": {
      "predicted_class": 2,
      "predicted_class_name": "CR",
      "predicted_class_full_name": "Cracks",
      "confidence": 0.987,
      "severity": "CRITICAL",
      "color": [255, 100, 100]
    },
    "probabilities": {
      "LP": 0.001,
      "PO": 0.002,
      "CR": 0.987,
      "ND": 0.010
    },
    "regions": [
      {
        "x": 150,
        "y": 200,
        "width": 100,
        "height": 80,
        "coverage": 0.45,
        "intensity": 0.89
      }
    ],
    "location_description": "Defect detected in central region",
    "description": "Linear crack detected with high confidence...",
    "recommendation": "Immediate rejection required. Schedule repair..."
  }
}
```

### Fallback Handling

If `metadata` is missing, the component shows a simplified view with just the heatmap:

```tsx
if (!explanation.metadata) {
  // Shows basic heatmap display
  return <SimpleHeatmapView />;
}
```

---

## 🚀 Performance Tips

### Image Optimization
- Backend returns heatmaps as PNG (best quality/size balance)
- Use base64 encoding for inline display (no extra HTTP requests)
- Lazy load original image if not provided

### Canvas Rendering
- Canvas is only created when regions exist
- Redraws only on state changes (selected/hovered region)
- Uses `useEffect` hook for efficient updates

### Zoom Performance
- CSS `transform: scale()` for GPU acceleration
- No re-rendering of images during zoom
- Smooth transitions with `transition: transform 0.2s`

---

## 🐛 Troubleshooting

### Issue: Heatmap not displaying
**Cause**: Backend not returning base64-encoded image  
**Solution**: Verify `/explain` endpoint returns proper base64 string

### Issue: Regions not clickable
**Cause**: Canvas not sized correctly  
**Solution**: Ensure canvas width/height match image natural dimensions

### Issue: Icons not showing
**Cause**: lucide-react not installed  
**Solution**: Run `npm install lucide-react`

### Issue: TypeScript errors
**Cause**: Type definitions out of sync  
**Solution**: Check `frontend/types/index.ts` matches backend schema

### Issue: Zoom not working
**Cause**: Container overflow not set  
**Solution**: Verify parent div has `overflow: auto`

---

## 📈 Future Enhancements

### Planned Features
- [ ] Export visualization as PDF/PNG
- [ ] Batch processing UI for multiple images
- [ ] Comparison view (before/after repairs)
- [ ] Historical defect tracking dashboard
- [ ] Custom severity thresholds
- [ ] Multi-language support for operators

### Suggested Improvements
- Add keyboard shortcuts (arrow keys for region navigation)
- Implement undo/redo for user annotations
- Add measurement tools (ruler, angle)
- Enable side-by-side comparison with previous inspections
- Add audio descriptions for accessibility

---

## 📚 Related Documentation

- [XAI Implementation Guide](../XAI_EXPLAINABILITY_IMPLEMENTATION.md)
- [Operator Quick Start](../OPERATOR_QUICK_START_GUIDE.md)
- [API Reference](../backend/api/routes.py)
- [Type Definitions](./types/index.ts)

---

## 👥 For Operators

**Simple Usage Guide**:

1. **Upload Image**: Click upload area, select radiograph
2. **Analyze**: Click "Analyze Defects" button
3. **Review Results**:
   - **Green badge** = Safe, accept weld
   - **Yellow badge** = Minor defect, assess carefully
   - **Red badge** = Critical defect, reject weld
4. **Inspect Details**: Use zoom to examine highlighted regions
5. **Follow Recommendations**: Read and follow action steps
6. **Document**: Take screenshots or export report

**Color Codes**:
- 🟢 Green = Good (No defect)
- 🔵 Blue = Low risk (Monitor)
- 🟡 Yellow = Medium risk (Assess)
- 🟠 Orange = High risk (Review)
- 🔴 Red = Critical (Reject)

---

## 📝 Changelog

### Version 2.0 (October 2025)
- ✅ Added DefectLocalizationView with interactive regions
- ✅ Created OperatorMessaging components suite
- ✅ Updated XAIExplanations with enhanced UI
- ✅ Added zoom/pan controls
- ✅ Implemented severity-based color coding
- ✅ Added tooltip descriptions
- ✅ Created example analysis page

### Version 1.0 (Previous)
- Basic heatmap display
- Simple method selector
- Consensus score display

---

**Last Updated**: October 23, 2025  
**Status**: ✅ Production Ready  
**Tested**: Chrome, Firefox, Safari, Edge
