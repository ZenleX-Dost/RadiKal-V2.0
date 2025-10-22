# 🚀 RadiKal - Quick Start Guide

**Status**: ✅ Frontend 100% Complete  
**Last Updated**: October 18, 2025

---

## ⚡ 60-Second Start

```bash
# 1. Start Backend (Terminal 1)
cd backend
python main.py

# 2. Start Frontend (Terminal 2)
cd frontend
npm run dev

# 3. Open Browser
http://localhost:3000
```

**That's it!** The app is ready to use.

---

## 🎯 First Steps

1. **Upload an Image**
   - Click or drag-and-drop a weld image (PNG/JPG)
   - Max size: 10MB
   - Supported formats: PNG, JPG, JPEG

2. **View Detection Results**
   - Defects automatically detected
   - See confidence scores and severity
   - Bounding boxes on image

3. **Explore XAI Explanations**
   - Click tabs: GradCAM, LIME, SHAP, Saliency
   - See what the AI is looking at
   - Compare consensus scores

4. **Export Your Results**
   - Click "Export PDF" for full report with heatmaps
   - Click "Export Excel" for data analysis
   - Reports include all detection data

5. **Check Your History**
   - Navigate to "History" page
   - See all past analyses
   - Search and filter results

6. **View Performance Metrics**
   - Navigate to "Metrics" page
   - See precision, recall, F1 scores
   - View confusion matrix

7. **Configure Settings**
   - Navigate to "Settings" page
   - Adjust confidence threshold
   - Change theme (dark/light)
   - Configure export options

---

## 📱 Pages Overview

### Dashboard (`/dashboard`)
**Main detection interface**
- Upload images
- View detection results
- See XAI explanations
- Export reports
- Auto-save to history

### Metrics (`/metrics`)
**Performance analytics**
- Precision/Recall/F1 trends
- Detection volume charts
- Confusion matrix
- Time range selection (7/30/90 days)

### History (`/history`)
**Past analyses**
- View all previous detections
- Search by image name
- Filter by severity/date
- Paginated results
- Delete old analyses

### Settings (`/settings`)
**Configuration**
- Detection settings (threshold, max detections)
- UI preferences (theme, notifications)
- Export options (format, include heatmaps)
- API configuration (backend URL, timeout)

---

## 🎨 Features

### ✅ What Works Right Now

- **Image Upload**: Drag-and-drop or click to select
- **Real-time Detection**: Instant AI analysis
- **XAI Visualization**: 4 explanation methods
- **PDF Export**: Comprehensive reports
- **Excel Export**: Data analysis spreadsheets
- **History Management**: Save and review past analyses
- **Performance Metrics**: Track model accuracy
- **Settings**: Customize your experience
- **Dark Mode**: Toggle light/dark theme
- **Responsive**: Works on mobile, tablet, desktop
- **Error Handling**: Graceful error messages
- **Notifications**: Toast messages for actions

### 🎯 Keyboard Shortcuts (Coming Soon)

- `Ctrl/Cmd + U`: Upload image
- `Ctrl/Cmd + E`: Export
- `Ctrl/Cmd + H`: View history
- `Ctrl/Cmd + ,`: Settings

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in `frontend/` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Settings Page Options

**Detection Settings**:
- Confidence Threshold: 0.0 - 1.0 (default: 0.5)
- Max Detections: Number of detections to show
- Preferred XAI Method: Default explanation method

**UI Settings**:
- Theme: Light / Dark / System
- Auto-save Analyses: Automatically save to history
- Show Notifications: Enable toast notifications

**Export Settings**:
- Default Format: PDF / Excel
- Include Heatmaps: Add XAI heatmaps to PDF
- Include Metadata: Add analysis metadata

**API Settings**:
- Backend URL: API endpoint
- Timeout: Request timeout in milliseconds

---

## 💡 Tips & Tricks

### Best Practices

1. **Image Quality**: Use high-resolution images for better detection
2. **File Format**: PNG preferred for best quality
3. **File Size**: Keep under 10MB for faster processing
4. **Auto-save**: Enable auto-save in settings to never lose analyses
5. **Exports**: Use PDF for sharing, Excel for data analysis

### Performance Tips

1. **Browser**: Use Chrome/Edge for best performance
2. **Cache**: Clear browser cache if seeing old data
3. **Network**: Ensure stable connection to backend
4. **Storage**: History limited to 100 items (oldest auto-deleted)

---

## 🐛 Troubleshooting

### "Cannot connect to backend"
**Solution**: 
1. Check backend is running (`python main.py`)
2. Verify `NEXT_PUBLIC_API_URL` in `.env`
3. Check firewall settings

### "Upload failed"
**Solution**:
1. Check file size (< 10MB)
2. Ensure file is PNG or JPG
3. Check network connection

### "Export not working"
**Solution**:
1. Allow pop-ups in browser
2. Check browser download settings
3. Ensure sufficient disk space

### "Dark mode not applying"
**Solution**:
1. Go to Settings
2. Select Theme preference
3. Refresh page if needed

### "History not showing"
**Solution**:
1. Check localStorage is enabled
2. Enable auto-save in settings
3. Manually click "Save to History"

---

## 📚 Documentation

### Full Documentation
- **Complete Guide**: `frontend/FRONTEND_COMPLETE.md`
- **Delivery Report**: `FRONTEND_DELIVERY_REPORT.md`
- **Completion Plan**: `frontend/COMPLETION_PLAN.md`

### Code Documentation
- All components have inline documentation
- TypeScript types are self-documenting
- Check `types/index.ts` for data structures

---

## 🎓 Learn More

### Technologies
- **Next.js**: https://nextjs.org
- **React**: https://react.dev
- **Tailwind CSS**: https://tailwindcss.com
- **Zustand**: https://docs.pmnd.rs/zustand
- **Recharts**: https://recharts.org

### Project Structure
```
frontend/
├── app/            # Pages (Next.js 14 App Router)
├── components/     # React components
├── store/          # Zustand state management
├── lib/            # Utilities (API, export)
├── types/          # TypeScript interfaces
└── public/         # Static assets
```

---

## 🚀 Production Deployment

### Vercel (Easiest)
```bash
npm i -g vercel
vercel
```

### Docker
```bash
docker build -t radikal-frontend .
docker run -p 3000:3000 radikal-frontend
```

### Manual Build
```bash
npm run build
npm start
```

---

## ✅ Checklist

Before first use:
- [ ] Backend is running on port 8000
- [ ] Frontend .env file configured
- [ ] Browser allows downloads/pop-ups
- [ ] Have test weld images ready

---

## 🎉 You're Ready!

**The frontend is 100% complete and ready to use.**

1. Start the app (`npm run dev`)
2. Upload an image
3. Explore the features
4. Export your first report

**Need help?** Check the full documentation in `FRONTEND_COMPLETE.md`

---

**Happy analyzing! 🚀**
