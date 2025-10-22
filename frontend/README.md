# RadiKal XAI Visual Quality Control - Frontend

## 🚀 STATUS: STARTER FOUNDATION READY (25-30% Complete)

This is a **working starter template** with core functionality. **3-4 weeks of development needed** to complete all features.

### ✅ What's Included

- ✅ Next.js 14 + TypeScript + Tailwind CSS configuration
- ✅ Complete API client with authentication support
- ✅ TypeScript types for all backend responses
- ✅ **3 Core React Components** (fully functional):
  - `ImageUpload` - Drag-and-drop image upload with preview
  - `DetectionResults` - Display defect detections with bounding boxes & severity
  - `XAIExplanations` - Visualize XAI heatmaps (Grad-CAM, SHAP, LIME, Integrated Gradients)
- ✅ **Dashboard page** - Complete upload → detect → explain workflow
- ✅ Responsive design with Tailwind CSS
- ✅ Error handling & loading states

### ❌ What's Missing (Need to Build)

- ❌ Authentication (Makerkit integration) - 1 week
- ❌ Navigation menu & routing - 2 days
- ❌ Metrics dashboard with charts (Recharts) - 1 week
- ❌ Export/download functionality - 3 days
- ❌ History/logs page with search & filter - 1 week
- ❌ Settings page - 3 days
- ❌ Batch image processing - 1 week
- ❌ State management (Zustand) - 2 days
- ❌ Testing suite (Jest + Playwright) - 1 week
- ❌ Advanced error boundaries - 2 days

**Estimated completion time**: 3-4 weeks full-time development

---

## Overview

The frontend provides an intuitive interface for operators and administrators to:
- ✅ Upload and review radiographic images (DONE)
- ✅ View defect detection results with confidence scores (DONE)
- ✅ Explore XAI explanations with interactive heatmaps (DONE)
- ❌ Monitor performance metrics and model calibration (TODO)
- ❌ Export detailed reports (TODO)

## Prerequisites

- Node.js 18.x or higher
- npm or yarn
- Valid Makerkit license
- Backend service running (see backend/README.md)

## Makerkit Integration

This application is built on [Makerkit](https://makerkit.dev/), a Next.js SaaS starter kit. You'll need:

1. A valid Makerkit license
2. Makerkit CLI installed
3. Access to Makerkit documentation

## Installation

### Initial Setup

1. Install Makerkit CLI:
```bash
npm install -g @makerkit/cli
```

2. Initialize the Makerkit project:
```bash
makerkit init xai-quality-control
```

3. Install dependencies:
```bash
cd xai-quality-control
npm install
```

4. Configure environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=XAI Quality Control
```

## Development

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Backend API Integration

The frontend communicates with the backend service through these endpoints:

- **POST /api/xai-qc/detect**: Upload images for detection
- **POST /api/xai-qc/explain**: Request XAI explanations
- **GET /api/xai-qc/metrics**: Retrieve performance metrics
- **POST /api/xai-qc/export**: Generate reports
- **GET /api/xai-qc/calibration**: Get calibration status
- **GET /api/xai-qc/health**: Health check

All requests include JWT authentication tokens from Makerkit's auth system.

## Features to Implement

### 1. Image Upload & Detection View
- Drag-and-drop image upload
- Display uploaded images with detection overlays
- Bounding boxes and segmentation masks
- Confidence scores and severity levels

### 2. XAI Explanation Viewer
- Tabbed interface for different XAI methods
- Side-by-side comparison of heatmaps
- Grad-CAM, SHAP, LIME, Integrated Gradients views
- Aggregated explanation view
- Consensus score display

### 3. Dashboard & Metrics
- Real-time performance metrics display
- Charts for FN, FP, mAP, IoU trends
- Calibration status indicators
- Uncertainty metrics visualization

### 4. Report Export
- Export button with format selection (PDF/Excel)
- Date range picker for reports
- Download progress indicator
- Report history

### 5. Authentication & Authorization
- Makerkit JWT integration
- Role-based access (operator, admin)
- Protected routes
- Session management

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Dashboard pages
│   ├── api/               # API routes
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── image-upload/      # Image upload components
│   ├── detection-view/    # Detection display
│   ├── xai-viewer/        # XAI explanation viewer
│   ├── metrics/           # Metrics dashboard
│   └── reports/           # Report generation
├── lib/                   # Utility libraries
│   ├── api/               # API client
│   ├── auth/              # Auth helpers
│   └── utils/             # General utilities
├── public/                # Static assets
├── styles/                # CSS/SCSS files
└── types/                 # TypeScript definitions
```

## Authentication Flow

1. User authenticates through Makerkit
2. Makerkit issues JWT token
3. Frontend includes token in API requests
4. Backend validates token via middleware
5. Backend maps Makerkit roles to module permissions

## Building for Production

```bash
npm run build
npm start
```

## Docker Deployment

Build the frontend container:
```bash
docker build -t xai-qc-frontend .
docker run -p 3000:3000 xai-qc-frontend
```

Or use the root docker-compose.yml to run the full stack.

## Testing

Run tests:
```bash
npm test
```

Run E2E tests:
```bash
npm run test:e2e
```

## API Client Example

```typescript
import { apiClient } from '@/lib/api/client';

// Upload image for detection
const detectDefects = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/api/xai-qc/detect', formData);
  return response.data;
};

// Request explanations
const getExplanations = async (imageId: string) => {
  const response = await apiClient.post('/api/xai-qc/explain', {
    image_id: imageId,
    methods: ['gradcam', 'shap', 'lime', 'ig']
  });
  return response.data;
};
```

## Contributing

Follow the project's contribution guidelines and ensure:
- Code is properly formatted (Prettier)
- TypeScript types are defined
- Components are tested
- Changes are documented

## Resources

- [Makerkit Documentation](https://makerkit.dev/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- Backend API Documentation: http://localhost:8000/docs

## License

MIT License - see LICENSE file for details
