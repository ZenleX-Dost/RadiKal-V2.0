# Getting Started

This guide will help you get RadiKal V2.0 up and running quickly.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** (tested with 3.10.11)
- **NVIDIA GPU** with 6GB+ VRAM (tested on RTX 4050)
- **CUDA 12.1+** (PyTorch 2.5.1+cu121)
- **Node.js 18+** with pnpm package manager
- **Git** for version control
- **Docker** (optional, for containerized deployment)

## Quick Launch

The fastest way to start RadiKal V2.0 is using the startup script:

### Windows

```batch
# Clone the repository
git clone https://github.com/ZenleX-Dost/RadiKal-V2.0.git
cd RadiKal-V2.0

# Run the startup script
START_RADIKAL.bat
```

This script will:
1. Start the backend API server on port 8000
2. Launch the Makerkit frontend on port 3000
3. Open your default browser to the application

### Access Points

Once running, you can access:

- **Frontend Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health/detailed

## Manual Launch

If you prefer to start components separately:

### Backend API

```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment (if created)
..\venv\Scripts\Activate.ps1

# Start the server
python run_server.py

# Or with auto-reload for development
python run_server.py --reload
```

### Makerkit Frontend

```powershell
# Navigate to frontend directory
cd frontend-makerkit/apps/web

# Start development server
pnpm run dev
```

## First Steps

### 1. Verify Installation

Check that the system is running correctly by visiting the health endpoint:

```powershell
curl http://localhost:8000/health/detailed
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T14:25:00",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 4050 Laptop GPU",
  "models_loaded": true
}
```

### 2. Test Basic Detection

Upload a test image through the web interface:

1. Navigate to http://localhost:3000
2. Click on "Analysis" in the navigation menu
3. Upload a radiographic weld image
4. Select "Classification" mode
5. Click "Analyze"

You should see:
- Predicted defect class
- Confidence score
- Class probabilities

### 3. Try Hybrid Analysis

Test the SAM2 integration:

1. Upload an image with a defect
2. Select "Hybrid" mode
3. Choose guidance strategy: "Auto"
4. Click "Analyze"

Results will include:
- Classification: defect type and confidence
- Segmentation: pixel-level mask overlay
- Coverage percentage
- Centroid coordinates

### 4. Explore XAI Explanations

Generate explainable AI visualizations:

1. After analyzing an image, navigate to the XAI tab
2. Select an XAI method: Grad-CAM, SHAP, LIME, or Integrated Gradients
3. View the heatmap overlay showing important regions
4. Compare different methods using the method selector

### 5. Batch Processing

Process multiple images simultaneously:

1. Navigate to http://localhost:3000/home/batch
2. Drag and drop multiple images (up to 10)
3. Select XAI methods to apply
4. Click "Start Batch Analysis"
5. Monitor progress in real-time
6. Export results when complete

## Configuration

### Environment Variables

The system uses environment variables for configuration. Key settings:

**Backend** (`backend/.env`):
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST=8.9

# Model Paths
YOLO_MODEL_PATH=../models/best.pt
SAM2_CHECKPOINT=../models/sam2/sam2_hiera_small.pt
SAM2_CONFIG=sam2_hiera_s.yaml
```

**Frontend** (`frontend-makerkit/apps/web/.env.local`):
```env
# API Endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
```

### Advanced Settings

Access advanced configuration through the web interface:

1. Navigate to http://localhost:3000/home/settings/advanced
2. Configure:
   - Notification preferences
   - API timeout and retry settings
   - Performance tuning (GPU memory, concurrent analysis)
   - Security settings (MFA, audit logging)

## Common Tasks

### Viewing API Documentation

Visit http://localhost:8000/docs to access interactive API documentation powered by Swagger UI. You can:

- Browse all available endpoints
- View request/response schemas
- Test API calls directly in the browser
- Download OpenAPI specification

### Stopping Services

**Windows:**
```powershell
# Stop all services
.\STOP_ALL.ps1
```

**Manual:**
- Press `Ctrl+C` in each terminal window running backend/frontend

### Updating the Application

```powershell
# Pull latest changes
git pull origin main

# Update backend dependencies
cd backend
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd ../frontend-makerkit
pnpm install
```

### Checking GPU Status

Verify GPU is being utilized:

```powershell
# Monitor GPU usage
nvidia-smi -l 1

# Check PyTorch CUDA availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

## Next Steps

Now that you have RadiKal running:

1. **Read the User Guide**: Learn about all features in the [User Guide](user-guide.md)
2. **Explore the API**: Check the [API Reference](api-reference.md) for integration options
3. **Understand XAI**: Learn about explainability methods in [XAI Methods](xai-methods.md)
4. **Review Architecture**: Understand the system in [Architecture](architecture.md)
5. **Deploy to Production**: Follow the [Deployment Guide](deployment.md)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review log files:
   - Backend: `backend/logs/radikal.log`
   - Frontend: Browser console (F12)
3. Verify system requirements and GPU configuration
4. Check GitHub issues for known problems
5. Review the comprehensive documentation in this site

## Additional Resources

- [SAM2 Integration Guide](sam2-guide.md) - Deep dive into segmentation
- [Testing Guide](testing.md) - Running tests and validation
- [Dataset Information](RIAWELC_DATASET_INFO.md) - RIAWELC dataset details
- Main GitHub Repository: https://github.com/ZenleX-Dost/RadiKal-V2.0
