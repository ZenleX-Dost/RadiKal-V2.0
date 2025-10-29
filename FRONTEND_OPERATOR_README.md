# Frontend XAI Visualization - Quick Start

## 🎯 What's New

Enhanced frontend visualization for explainable AI (XAI) with operator-friendly interfaces:

### New Components

1. **DefectLocalizationView** (`components/DefectLocalizationView.tsx`)
   - Interactive heatmap visualization with zoom/pan
   - Click and hover region highlighting
   - Real-time coverage metrics
   - Class probability bars

2. **OperatorMessaging** (`components/OperatorMessaging.tsx`)
   - `DefectBadge`: Severity-based color-coded badges
   - `SeverityIndicator`: Visual risk level bars (1-5)
   - `ActionRecommendation`: Actionable next steps
   - `DefectSummaryCard`: Comprehensive defect overview

3. **Enhanced XAIExplanations** (`components/XAIExplanations.tsx`)
   - Unified interface combining all components
   - Advanced details panel
   - Responsive design

4. **Example Page** (`app/xai-analysis/page.tsx`)
   - Complete working example
   - File upload interface
   - Real-time API integration

## 🚀 Quick Start

### 1. Start Backend
```bash
cd backend
python run_server.py
```

Backend will start on `http://localhost:8000`

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
```

Make sure `lucide-react` is installed for icons.

### 3. Start Frontend
```bash
npm run dev
```

Frontend will start on `http://localhost:3000`

### 4. Test the Integration
```bash
# In a new terminal, from project root:
python backend/test_frontend_integration.py
```

This validates that backend API matches frontend TypeScript types.

### 5. Use the Application

Navigate to: `http://localhost:3000/xai-analysis`

**Steps:**
1. Click upload area or drag/drop a radiographic image
2. Click "Analyze Defects" button
3. View results with:
   - Defect classification and confidence
   - Interactive heatmap with zoom controls
   - Detected regions with bounding boxes
   - Severity assessment
   - Actionable recommendations

## 📦 New Files

### Frontend Components
```
frontend/
├── components/
│   ├── DefectLocalizationView.tsx    (NEW - 470 lines)
│   ├── OperatorMessaging.tsx         (NEW - 330 lines)
│   └── XAIExplanations.tsx          (UPDATED - Enhanced UI)
├── app/
│   └── xai-analysis/
│       └── page.tsx                  (NEW - Example page)
└── types/
    └── index.ts                      (UPDATED - New types)
```

### Backend Tests
```
backend/
└── test_frontend_integration.py      (NEW - Integration test)
```

### Documentation
```
FRONTEND_XAI_GUIDE.md                 (NEW - Complete guide)
FRONTEND_OPERATOR_README.md           (NEW - This file)
```

## 🎨 Features

### Interactive Visualization
- ✅ Grad-CAM heatmaps showing defect locations
- ✅ Zoom controls (0.5x - 3x magnification)
- ✅ Pan by scrolling within zoomed view
- ✅ Toggle between heatmap and overlay modes
- ✅ Interactive canvas with region bounding boxes
- ✅ Hover highlighting with yellow border
- ✅ Click to select regions (red border)

### Operator Communication
- ✅ Color-coded severity badges (Red=Critical, Green=Acceptable)
- ✅ Visual risk level indicators (1-5 bars)
- ✅ Clear action recommendations
- ✅ Tooltips with defect descriptions
- ✅ Natural language location descriptions
- ✅ Confidence percentages for all classes

### Data Display
- ✅ Defect regions with coverage/intensity metrics
- ✅ Class probability bars
- ✅ Computation time and metadata
- ✅ Advanced details panel (expandable)
- ✅ Summary card with key information

## 🔧 Integration

### Using in Your Pages

```tsx
import XAIExplanations from '@/components/XAIExplanations';
import { ExplanationResponse } from '@/types';

// After calling /explain API:
const response = await fetch('http://localhost:8000/api/explain', {
  method: 'POST',
  body: formData,
});
const explanation: ExplanationResponse = await response.json();

// Render:
<XAIExplanations 
  explanation={explanation} 
  originalImage={base64Image} 
/>
```

### Using Individual Components

```tsx
import { 
  DefectBadge, 
  SeverityIndicator,
  ActionRecommendation,
  DefectSummaryCard 
} from '@/components/OperatorMessaging';

// Display badge
<DefectBadge prediction={metadata.prediction} size="lg" />

// Show severity
<SeverityIndicator 
  severity="CRITICAL" 
  confidence={0.98} 
/>

// Action recommendation
<ActionRecommendation
  prediction={metadata.prediction}
  recommendation={metadata.recommendation}
/>

// Summary card
<DefectSummaryCard
  prediction={metadata.prediction}
  locationDescription={metadata.location_description}
  numRegions={metadata.regions.length}
/>
```

## 📊 API Response Format

Backend `/explain` endpoint returns:

```typescript
interface ExplanationResponse {
  image_id: string;
  explanations: Array<{
    method: string;              // "gradcam" or "overlay"
    heatmap_base64: string;      // PNG base64
    confidence_score: number;    // 0.0-1.0
  }>;
  aggregated_heatmap: string;    // Base64 PNG
  consensus_score: number;       // 0.0-1.0
  computation_time_ms: number;
  timestamp: string;
  metadata: {
    prediction: {
      predicted_class: number;
      predicted_class_name: string;        // "LP", "PO", "CR", "ND"
      predicted_class_full_name: string;   // "Lack of Penetration", etc.
      confidence: number;
      severity: string;                     // "CRITICAL", "MEDIUM", "ACCEPTABLE"
      color: [number, number, number];     // BGR color
    };
    probabilities: Record<string, number>; // All class probabilities
    regions: Array<{
      x: number;
      y: number;
      width: number;
      height: number;
      coverage: number;   // 0.0-1.0
      intensity: number;  // 0.0-1.0
    }>;
    location_description: string;
    description: string;
    recommendation: string;
  };
}
```

## 🎨 Color Coding

### Severity Levels
- 🔴 **CRITICAL** - Red (Cracks, Lack of Penetration)
- 🟠 **HIGH** - Orange
- 🟡 **MEDIUM** - Yellow (Porosity)
- 🔵 **LOW** - Blue
- 🟢 **ACCEPTABLE** - Green (No Defect)

### Actions by Severity
- **CRITICAL**: "Reject Weld" (Red alert)
- **HIGH**: "Review Required" (Orange warning)
- **MEDIUM**: "Assess & Document" (Yellow caution)
- **LOW**: "Monitor" (Blue info)
- **ACCEPTABLE**: "Accept Weld" (Green check)

## 🐛 Troubleshooting

### Backend Connection Error
```
Error: Cannot connect to backend
```
**Solution**: Start backend server
```bash
cd backend
python run_server.py
```

### TypeScript Errors
```
Property 'metadata' does not exist on type 'ExplanationResponse'
```
**Solution**: Update types
```bash
# Make sure frontend/types/index.ts is up to date
# The types have been updated in this implementation
```

### Missing Icons
```
Error: Cannot find module 'lucide-react'
```
**Solution**: Install dependencies
```bash
cd frontend
npm install lucide-react
```

### Canvas Not Interactive
**Solution**: Ensure regions exist in metadata and canvas is sized correctly

## ✅ Testing Checklist

Before deploying:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can upload test image
- [ ] Heatmap displays correctly
- [ ] Regions are highlighted
- [ ] Zoom controls work
- [ ] Severity badge shows correct color
- [ ] Recommendations display
- [ ] All class probabilities show
- [ ] Integration test passes

## 📚 Documentation

- **Complete Guide**: `FRONTEND_XAI_GUIDE.md` - Full technical documentation
- **This File**: Quick start and operator guide
- **Backend Docs**: `XAI_EXPLAINABILITY_IMPLEMENTATION.md`
- **API Docs**: `XAI_QUICK_REFERENCE.md`

## 🎓 For Operators

**Simple Guide**:

1. **Upload**: Click and select radiograph image
2. **Analyze**: Press blue "Analyze Defects" button
3. **Read Badge**: 
   - 🟢 Green = Good, accept
   - 🟡 Yellow = Check carefully
   - 🔴 Red = Reject, do not use
4. **Inspect**: Use zoom buttons to see details
5. **Follow**: Read and follow recommendation box
6. **Document**: Screenshot or export results

**What Each Part Means**:
- **Heatmap Colors**: Red/yellow areas = where defect is located
- **Confidence**: Higher % = more certain
- **Regions**: Boxes show exact defect locations
- **Severity Bars**: More bars = more serious
- **Recommendation**: What to do next

## 🚀 Next Steps

Optional enhancements:
- Add PDF export functionality
- Implement batch processing UI
- Add comparison view (before/after)
- Create historical tracking dashboard
- Add measurement tools
- Multi-language support

## 📞 Support

For issues or questions:
1. Check documentation in `FRONTEND_XAI_GUIDE.md`
2. Run integration test: `python backend/test_frontend_integration.py`
3. Check console logs in browser DevTools (F12)
4. Verify backend logs for API errors

---

**Status**: ✅ Production Ready  
**Version**: 2.0  
**Last Updated**: October 23, 2025
