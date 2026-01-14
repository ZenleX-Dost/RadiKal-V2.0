# Installation

Complete installation guide for RadiKal V2.0.

## System Requirements

### Hardware Requirements

**Minimum (Development/Testing)**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- GPU: Not required (CPU inference supported)

**Recommended (Production)**:
- CPU: 8-16 cores
- RAM: 32 GB
- Storage: 500 GB SSD
- GPU: NVIDIA GPU with 6GB+ VRAM (RTX 3060, RTX 4050, or better)

**Enterprise (High Volume)**:
- CPU: 16-32 cores
- RAM: 64-128 GB
- Storage: 1 TB NVMe SSD
- GPU: NVIDIA A100, A40, or equivalent (40-80 GB VRAM)

### Software Requirements

- **Operating System**: Windows 10/11, Ubuntu 22.04 LTS, or Rocky Linux 9
- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **NVIDIA GPU Drivers**: 535+ (if using GPU)
- **CUDA**: 12.1+ (if using GPU)
- **cuDNN**: 8.9+ (if using GPU)
- **Docker**: 24.0+ (optional, for containerized deployment)
- **Git**: For repository cloning

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/ZenleX-Dost/RadiKal-V2.0.git
cd RadiKal-V2.0
```

### 2. Backend Setup

#### Create Python Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Install Python Dependencies

```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- **FastAPI**: Web framework for the API
- **PyTorch**: Deep learning framework (with CUDA support)
- **YOLOv8 (Ultralytics)**: Classification model
- **SAM2**: Segmentation model
- **XAI Libraries**: SHAP, LIME, captum
- **MLflow**: Experiment tracking
- **Database**: SQLAlchemy, psycopg2-binary
- **Additional utilities**: Pillow, numpy, pandas, opencv-python

#### Download Model Checkpoints

**YOLOv8 Model:**
```bash
# The trained YOLOv8 model should be placed in:
# models/best.pt
# (This will be provided by the project or trained separately)
```

**SAM2 Model:**
```bash
# Create SAM2 models directory
mkdir -p ../models/sam2
cd ../models/sam2

# Download SAM2 checkpoint (choose based on your needs)

# Option 1: Small model (recommended for most cases)
curl -L -o sam2_hiera_small.pt  https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_small.pt

# Option 2: Tiny model (faster, less accurate)
# curl -L -o sam2_hiera_tiny.pt https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt

# Option 3: Base model (better accuracy, slower)
# curl -L -o sam2_hiera_base_plus.pt https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt
```

### 3. Frontend Setup (Makerkit)

#### Install pnpm

If you don't have pnpm installed:

```bash
npm install -g pnpm
```

#### Install Frontend Dependencies

```bash
cd ../frontend-makerkit
pnpm install
```

This will install all dependencies for the Next.js 15 frontend including:
- **Next.js 15**: React framework
- **React 18**: UI library
- **Supabase**: Backend-as-a-service
- **TailwindCSS v4**: Styling framework
- **Shadcn UI**: Component library
- **TypeScript**: Type-safe JavaScript
- **Lucide Icons**: Icon library

#### Configure Environment Variables

```bash
cd apps/web
cp .env.example .env.local
```

Edit `.env.local` with your configuration:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Optional: Analytics
NEXT_PUBLIC_GA_ID=your_google_analytics_id
```

### 4. GPU Configuration (Optional but Recommended)

#### Verify CUDA Installation

```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA version
nvcc --version
```

#### Verify PyTorch CUDA Support

```python
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

Expected output:
```
CUDA Available: True
CUDA Version: 12.1
GPU Name: NVIDIA GeForce RTX 4050 Laptop GPU
```

### 5. Database Setup

RadiKal uses Supabase (PostgreSQL) for data storage.

#### Option 1: Use Supabase Cloud (Recommended)

1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project
3. Copy the project URL and API keys
4. Update your `.env.local` file with the credentials

#### Option 2: Self-Hosted PostgreSQL

```bash
# Install PostgreSQL
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE radikal;
CREATE USER radikal_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE radikal TO radikal_user;
\q

# Update backend/.env with connection string
DATABASE_URL=postgresql://radikal_user:your_password@localhost:5432/radikal
```

### 6. Verify Installation

#### Start Backend API

```bash
cd backend
python run_server.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Visit http://localhost:8000/health/detailed to check system status.

#### Start Frontend

In a new terminal:

```bash
cd frontend-makerkit/apps/web
pnpm run dev
```

Expected output:
```
   ▲ Next.js 15.0.0
   - Local:        http://localhost:3000
   - Network:      http://192.168.1.x:3000

 ✓ Ready in 2.5s
```

Visit http://localhost:3000 to access the application.

### 7. Test the Installation

#### Run Backend Tests

```bash
cd backend
pytest tests/ -v
```

Expected: All tests should pass with >90% coverage.

#### Test SAM2 Integration

```bash
cd backend
python test_sam2_integration.py
```

Expected:
```
Test 1: SAM2 Import ✓
Test 2: YOLOv8 Classifier ✓
Test 3: SAM2 Segmenter ✓
Test 4: Hybrid Analyzer ✓
Test 5: Real Image Analysis ✓
```

## Docker Installation (Alternative)

For a containerized deployment:

### Build and Run with Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- MLflow UI: http://localhost:5000

### Stop Services

```bash
docker-compose down
```

## Environment Configuration

### Backend Environment Variables

Create `backend/.env` with the following variables:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/radikal
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST=8.9

# Model Paths
YOLO_MODEL_PATH=../models/best.pt
SAM2_CHECKPOINT=../models/sam2/sam2_hiera_small.pt
SAM2_CONFIG=sam2_hiera_s.yaml

# Security
SECRET_KEY=your-secret-key-change-this-in-production

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/radikal.log
```

### Frontend Environment Variables

Create `frontend-makerkit/apps/web/.env.local`:

```env
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# App Configuration
NEXT_PUBLIC_APP_NAME=RadiKal
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Features
NEXT_PUBLIC_ENABLE_THEME_TOGGLE=true
NEXT_PUBLIC_DEFAULT_THEME=light
```

## Troubleshooting

### Common Issues

#### CUDA Out of Memory

**Solution**: Use a smaller SAM2 model or process on CPU:
```python
# In backend/.env
SAM2_CHECKPOINT=../models/sam2/sam2_hiera_tiny.pt
```

#### Module Import Errors

**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
pip install -r backend/requirements.txt
```

#### Port Already in Use

**Solution**: Change ports in configuration or kill the process:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

#### Database Connection Errors

**Solution**: Verify database credentials and network connectivity:
```bash
# Test connection
psql -h localhost -U radikal_user -d radikal
```

### Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review log files in `backend/logs/`
3. Check [GitHub Issues](https://github.com/ZenleX-Dost/RadiKal-V2.0/issues)
4. See the [Getting Started Guide](getting-started.md)

## Next Steps

After successful installation:

1. Read the [Getting Started Guide](getting-started.md) for first steps
2. Review the [User Guide](user-guide.md) for feature documentation
3. Check the [API Reference](api-reference.md) for integration
4. Review the [Deployment Guide](deployment.md) for production setup
