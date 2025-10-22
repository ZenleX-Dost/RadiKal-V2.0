# RadiKal Frontend - Complete Documentation

## 🎉 Status: 100% COMPLETE (No Authentication)

**Version**: 2.0.0  
**Last Updated**: October 18, 2025  
**Completion**: Production-Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Components](#components)
6. [State Management](#state-management)
7. [API Integration](#api-integration)
8. [Export Functionality](#export-functionality)
9. [Deployment](#deployment)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)

---

## Overview

RadiKal is a complete Next.js 14 application for AI-powered weld defect detection with explainable AI (XAI) capabilities. The frontend provides a professional, production-ready interface with:

- ✅ Real-time defect detection
- ✅ 4 XAI methods (GradCAM, LIME, SHAP, Saliency)
- ✅ Performance metrics dashboard
- ✅ Analysis history management
- ✅ PDF & Excel export
- ✅ Comprehensive settings
- ✅ Dark/Light theme
- ✅ Fully responsive design
- ✅ Error handling & notifications

---

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see `backend/README.md`)

### Installation

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your backend URL
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev

# Open browser
http://localhost:3000
```

### Production Build

```bash
npm run build
npm start
```

---

## Features

### 🎯 Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Image Upload** | ✅ Complete | Drag-and-drop or click to upload (PNG/JPG, max 10MB) |
| **Defect Detection** | ✅ Complete | Real-time AI-powered defect detection |
| **XAI Explanations** | ✅ Complete | 4 methods with consensus scoring |
| **Metrics Dashboard** | ✅ Complete | Performance charts (Precision, Recall, F1, mAP) |
| **Analysis History** | ✅ Complete | Search, filter, paginate past analyses |
| **PDF Export** | ✅ Complete | Comprehensive PDF reports with heatmaps |
| **Excel Export** | ✅ Complete | Detailed Excel spreadsheets |
| **Settings** | ✅ Complete | User preferences, API config, theme |
| **Dark Mode** | ✅ Complete | Toggle between light/dark themes |
| **Responsive** | ✅ Complete | Mobile, tablet, desktop optimized |
| **Error Handling** | ✅ Complete | Toast notifications, error boundaries |
| **Loading States** | ✅ Complete | Skeleton loaders, spinners |

### 📊 Dashboard Features

- **Image Upload**: Drag-and-drop interface with preview
- **Real-time Detection**: Instant API calls with progress indicators
- **Results Display**: Bounding boxes, confidence scores, severity indicators
- **XAI Visualization**: Interactive heatmap viewer with method comparison
- **Export Options**: One-click PDF/Excel export
- **Auto-save**: Automatically save analyses to history

### 📈 Metrics Page

- **Performance Trends**: Line charts for Precision, Recall, F1 Score
- **Detection Volume**: Bar charts showing daily/weekly activity
- **Confusion Matrix**: Visual matrix with TP/TN/FP/FN counts
- **Time Range Selection**: 7/30/90 day views
- **Summary Cards**: Quick stats with trend indicators

### 📚 History Page

- **Analysis Table**: All past analyses with metadata
- **Search**: Find by image name or date
- **Filters**: Filter by severity, date range
- **Pagination**: 20 items per page
- **Detail View**: Click to see full analysis
- **Delete**: Remove old analyses

### ⚙️ Settings Page

- **Detection Settings**:
  - Confidence threshold (0.0 - 1.0)
  - Max detections
  - Preferred XAI method
- **UI Settings**:
  - Theme (light/dark/system)
  - Auto-save analyses
  - Show notifications
- **Export Settings**:
  - Default format (PDF/Excel)
  - Include heatmaps
  - Include metadata
- **API Settings**:
  - Backend URL
  - Request timeout

---

## Project Structure

```
frontend/
├── app/                      # Next.js 14 App Router
│   ├── layout.tsx           # Root layout with nav + sidebar
│   ├── page.tsx             # Redirects to /dashboard
│   ├── dashboard/
│   │   └── page.tsx         # Main detection interface
│   ├── metrics/
│   │   └── page.tsx         # Performance metrics
│   ├── history/
│   │   └── page.tsx         # Analysis history
│   ├── settings/
│   │   └── page.tsx         # User settings
│   └── globals.css          # Global styles
│
├── components/              # React components
│   ├── Navbar.tsx           # Top navigation bar
│   ├── Sidebar.tsx          # Side navigation panel
│   ├── ImageUpload.tsx      # File upload component
│   ├── DetectionResults.tsx # Detection display
│   ├── XAIExplanations.tsx  # XAI heatmap viewer
│   ├── ExportButton.tsx     # Export functionality
│   ├── Toast.tsx            # Notification system
│   ├── ErrorBoundary.tsx    # Error catching
│   ├── SkeletonLoader.tsx   # Loading skeletons
│   └── ui/                  # Reusable UI components
│       ├── Button.tsx
│       ├── Card.tsx
│       └── Spinner.tsx
│
├── store/                   # Zustand state management
│   ├── settingsStore.ts     # User settings state
│   ├── analysisStore.ts     # Analysis + history state
│   ├── uiStore.ts           # UI state (modals, toasts)
│   └── authStore.ts         # Auth state (unused, for future)
│
├── lib/                     # Utilities
│   ├── api.ts               # API client (Axios)
│   ├── exportPDF.ts         # PDF generation
│   └── exportExcel.ts       # Excel generation
│
├── types/
│   └── index.ts             # TypeScript interfaces
│
├── public/                  # Static assets
├── .env.example             # Environment template
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── tailwind.config.js       # Tailwind CSS config
└── next.config.js           # Next.js config
```

---

## Components

### Navigation Components

#### `Navbar.tsx`
- **Purpose**: Top navigation bar
- **Features**:
  - Mobile menu toggle
  - Breadcrumb navigation
  - Notification bell
  - Theme toggle (dark/light)
  - User avatar placeholder
- **Props**: `onMenuClick: () => void`

#### `Sidebar.tsx`
- **Purpose**: Side navigation panel
- **Features**:
  - Links to all pages
  - Active page highlighting
  - Mobile slide-out drawer
  - Logo and branding
- **Props**: `isOpen: boolean, onClose: () => void`

### Core Components

#### `ImageUpload.tsx`
- **Purpose**: File upload interface
- **Features**:
  - Drag-and-drop zone
  - Click to browse
  - Image preview
  - File validation
  - Progress indicator
- **Props**: `onUpload: (file: File) => void, isUploading?: boolean`

#### `DetectionResults.tsx`
- **Purpose**: Display detection results
- **Features**:
  - Image with bounding boxes (visual)
  - Detection list with confidence scores
  - Severity indicators (high/medium/low)
  - Mean uncertainty display
- **Props**: `imageUrl: string, detections: Detection[], meanUncertainty: number`

#### `XAIExplanations.tsx`
- **Purpose**: XAI heatmap visualization
- **Features**:
  - Method tabs (GradCAM, LIME, SHAP, Saliency)
  - Heatmap overlay display
  - Confidence score per method
  - Consensus score
- **Props**: `explanations: ExplanationHeatmap[], consensusScore: number`

#### `ExportButton.tsx`
- **Purpose**: Export functionality
- **Features**:
  - PDF export with heatmaps
  - Excel export with data
  - Format selection
  - Loading state
- **Props**: `imageName, imageUrl, detectionResult, explanationResult?, format?`

### UI Components

#### `Toast.tsx`
- **Purpose**: Notification system
- **Types**: success, error, warning, info
- **Auto-dismiss**: Configurable timeout
- **Position**: Top-right corner

#### `ErrorBoundary.tsx`
- **Purpose**: Catch React errors
- **Features**:
  - Error display
  - Reload button
  - Try again option

#### `SkeletonLoader.tsx`
- **Variants**:
  - `Skeleton` - Basic skeleton
  - `CardSkeleton` - Card placeholder
  - `TableSkeleton` - Table placeholder
  - `ChartSkeleton` - Chart placeholder
  - `DashboardSkeleton` - Full dashboard
  - `PageSkeleton` - Full page

---

## State Management

### Zustand Stores

#### `settingsStore.ts`

```typescript
interface Settings {
  // Detection
  confidenceThreshold: number;
  maxDetections: number;
  preferredXAIMethod: 'gradcam' | 'lime' | 'shap' | 'saliency';
  
  // UI
  theme: 'light' | 'dark' | 'system';
  autoSaveAnalyses: boolean;
  showNotifications: boolean;
  
  // Export
  defaultExportFormat: 'pdf' | 'excel';
  includeHeatmaps: boolean;
  includeMetadata: boolean;
  
  // API
  backendUrl: string;
  timeout: number;
  
  // Batch
  maxBatchSize: number;
  parallelProcessing: boolean;
}

// Usage
import { useSettingsStore } from '@/store/settingsStore';

const { settings, updateSettings, resetSettings } = useSettingsStore();
```

#### `analysisStore.ts`

```typescript
interface AnalysisHistory {
  id: string;
  timestamp: Date;
  imageName: string;
  imageUrl: string;
  detections: number;
  highSeverity: number;
  mediumSeverity: number;
  lowSeverity: number;
  result: DetectionResponse;
  explanation?: ExplanationResponse;
}

// Usage
import { useAnalysisStore } from '@/store/analysisStore';

const { 
  history, 
  addToHistory, 
  removeFromHistory, 
  clearHistory 
} = useAnalysisStore();
```

#### `uiStore.ts`

```typescript
interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

// Usage
import { useUIStore } from '@/store/uiStore';

const { addToast, toasts, setLoading } = useUIStore();

addToast({
  type: 'success',
  title: 'Success!',
  message: 'Operation completed',
  duration: 5000
});
```

---

## API Integration

### API Client (`lib/api.ts`)

```typescript
import { apiClient } from '@/lib/api';

// Health check
const health = await apiClient.healthCheck();

// Detect defects
const result = await apiClient.detectDefects(file);

// Get explanations
const explanations = await apiClient.getExplanations({
  image_id: 'img_123',
  detection_id: 'det_456',
  image_base64: 'base64string',
  target_class: 0
});

// Get metrics
const metrics = await apiClient.getMetrics('2025-01-01', '2025-01-31');

// Export report
const report = await apiClient.exportReport(['img1', 'img2'], 'pdf');

// Get calibration
const calibration = await apiClient.getCalibration();
```

---

## Export Functionality

### PDF Export

```typescript
import { exportToPDF } from '@/lib/exportPDF';

await exportToPDF(
  imageName,
  imageUrl,
  detectionResult,
  explanationResult,
  {
    includeHeatmaps: true,
    includeMetadata: true,
    companyName: 'Your Company'
  }
);
```

**PDF Contents**:
- Header with company name
- Detection summary table
- Detections list with bounding boxes
- Original image
- XAI heatmaps (all 4 methods)
- Page numbers and footer

### Excel Export

```typescript
import { exportToExcel } from '@/lib/exportExcel';

exportToExcel(imageName, detectionResult, 'Your Company');
```

**Excel Sheets**:
1. **Summary**: Metadata and statistics
2. **Detections**: All detections with full data
3. **Severity Analysis**: Breakdown by severity
4. **Type Analysis**: Breakdown by defect type

---

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production
vercel --prod
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

```bash
docker build -t radikal-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 radikal-frontend
```

### Environment Variables

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://your-api.com
```

---

## Configuration

### Tailwind Dark Mode

Theme is controlled by:
1. Settings store (`theme` property)
2. `document.documentElement.classList.add('dark')`
3. Tailwind `dark:` prefix on classes

### API Timeout

Default: 30 seconds

Configure in Settings page or directly:

```typescript
updateSettings({ timeout: 60000 }); // 60 seconds
```

---

## Troubleshooting

### Common Issues

**Issue**: "Failed to fetch from API"
- **Solution**: Check backend is running and `NEXT_PUBLIC_API_URL` is correct

**Issue**: "Export not working"
- **Solution**: Ensure images are loaded (CORS enabled on backend)

**Issue**: "Dark mode not applying"
- **Solution**: Check Tailwind config has `darkMode: 'class'`

**Issue**: "History not persisting"
- **Solution**: Check localStorage is enabled in browser

### Debug Mode

```typescript
// Enable detailed logs
if (typeof window !== 'undefined') {
  localStorage.setItem('debug', 'radikal:*');
}
```

---

## 🎉 Completion Summary

### What's Included

✅ **100% Feature Complete** (without authentication)
✅ **Production-Ready Code**
✅ **Comprehensive Error Handling**
✅ **Full TypeScript Coverage**
✅ **Responsive Design**
✅ **Dark Mode Support**
✅ **Export Functionality**
✅ **State Persistence**
✅ **Professional UI/UX**
✅ **Complete Documentation**

### What's NOT Included

❌ Authentication (can be added with NextAuth/Clerk/Makerkit)
❌ Unit Tests (can add Jest + React Testing Library)
❌ E2E Tests (can add Playwright/Cypress)
❌ Backend Analytics Tracking
❌ Real-time Collaboration

### Next Steps (Optional)

1. **Add Authentication**: Integrate NextAuth.js or Clerk
2. **Add Testing**: Jest + React Testing Library
3. **Performance Optimization**: Add React Query for caching
4. **Advanced Analytics**: Add Mixpanel/Google Analytics
5. **WebSockets**: Real-time updates

---

## 📞 Support

For issues, questions, or contributions:
- Check existing documentation
- Review TypeScript types
- Inspect browser console for errors
- Check backend API is responding

---

**RadiKal Frontend v2.0.0 - 100% Complete! 🚀**
