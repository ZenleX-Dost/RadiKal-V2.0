# RadiKal Frontend - Setup Guide

## ✅ What's Included

This is a **STARTER FOUNDATION** for the RadiKal frontend. It includes:

- ✅ Next.js 14 + TypeScript configuration
- ✅ Tailwind CSS setup
- ✅ API client with authentication
- ✅ TypeScript types for all backend responses
- ✅ Core components:
  - `ImageUpload` - Drag-and-drop image upload
  - `DetectionResults` - Display defect detections
  - `XAIExplanations` - Visualize XAI heatmaps
- ✅ Dashboard page with complete workflow
- ✅ Responsive design with Tailwind

## ⚠️ What's NOT Included (You Need to Build)

This is approximately **25-30% of a complete frontend**. You still need:

- ❌ Authentication (Makerkit integration)
- ❌ User management
- ❌ Metrics dashboard with charts
- ❌ Export/download functionality
- ❌ Settings page
- ❌ History/logs page
- ❌ Multi-image batch processing
- ❌ Advanced visualizations
- ❌ Real-time updates
- ❌ Error boundary components
- ❌ Loading states optimization
- ❌ Responsive navigation
- ❌ State management (Zustand)
- ❌ Form validation
- ❌ Accessibility improvements
- ❌ Testing suite
- ❌ Documentation

**Estimated time to complete**: 3-4 weeks of full-time development

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd frontend
npm install
```

### 2. Configure Environment

```powershell
cp .env.example .env
```

Edit `.env`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```powershell
npm run dev
```

Visit: http://localhost:3000

### 4. Start Backend API

In another terminal:
```powershell
cd ..\backend
python main.py
```

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page (redirects to dashboard)
│   ├── globals.css         # Global styles
│   └── dashboard/
│       └── page.tsx        # Main dashboard
├── components/
│   ├── ImageUpload.tsx     # Drag-and-drop upload
│   ├── DetectionResults.tsx # Display detections
│   └── XAIExplanations.tsx # Display XAI heatmaps
├── lib/
│   └── api.ts              # API client
├── types/
│   └── index.ts            # TypeScript types
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.js
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Check TypeScript types

## 🎨 Customization

### Add New Page

```typescript
// app/metrics/page.tsx
export default function MetricsPage() {
  return <div>Metrics Dashboard</div>;
}
```

### Add New Component

```typescript
// components/MyComponent.tsx
'use client';

export default function MyComponent() {
  return <div>My Component</div>;
}
```

### Use API Client

```typescript
import { apiClient } from '@/lib/api';

// In component
const metrics = await apiClient.getMetrics();
```

## 🔐 Authentication (TODO)

To add Makerkit authentication:

1. Install Makerkit packages:
```powershell
npm install @makerkit/auth @makerkit/ui
```

2. Follow Makerkit documentation:
https://makerkit.dev/docs/authentication

3. Update API client to use Makerkit tokens

## 📊 Next Steps

### Phase 1: Essential Features (Week 1-2)
1. Add authentication (Makerkit)
2. Add navigation menu
3. Build metrics dashboard with charts (Recharts)
4. Add export/download functionality
5. Implement error boundaries

### Phase 2: Advanced Features (Week 3-4)
1. Add history/logs page
2. Implement batch processing
3. Add settings page
4. Implement state management (Zustand)
5. Add real-time updates
6. Improve accessibility

### Phase 3: Polish & Testing (Week 5-6)
1. Add loading skeletons
2. Implement comprehensive error handling
3. Write unit tests (Jest + React Testing Library)
4. Write E2E tests (Playwright)
5. Performance optimization
6. Documentation

## 🐛 Troubleshooting

**Port already in use:**
```powershell
# Kill process on port 3000
npx kill-port 3000
```

**Module not found:**
```powershell
rm -rf node_modules package-lock.json
npm install
```

**TypeScript errors:**
```powershell
npm run type-check
```

**API connection failed:**
- Ensure backend is running on http://localhost:8000
- Check CORS settings in backend
- Verify `.env` configuration

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript](https://www.typescriptlang.org/docs)
- [Makerkit](https://makerkit.dev)
- [React Query](https://tanstack.com/query/latest)

## ⚡ Performance Tips

1. Use Next.js Image component for images
2. Implement lazy loading for heavy components
3. Use React.memo for expensive components
4. Optimize bundle size with dynamic imports
5. Add service worker for offline support

## 🤝 Contributing

This is a starter template. You'll need to:
1. Add proper authentication
2. Implement all missing pages
3. Add comprehensive error handling
4. Write tests
5. Improve accessibility
6. Add documentation

Good luck building your frontend! 🚀
