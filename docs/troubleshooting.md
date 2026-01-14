# Troubleshooting

Common issues and solutions for RadiKal V2.0.

## Installation Issues

### Python ImportError

**Problem**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
cd backend
pip install -r requirements.txt
```

### CUDA Not Available

**Problem**: `torch.cuda.is_available()` returns `False`

**Solutions**:
1. Check NVIDIA driver:
```bash
nvidia-smi
```

2. Verify PyTorch CUDA version matches system CUDA:
```python
import torch
print(torch.version.cuda)  # Should match: nvidia-smi output
```

3. Reinstall PyTorch with correct CUDA version:
```bash
pip install torch==2.5.1+cu121 -f https://download.pytorch.org/whl/torch_stable.html
```

### SAM2 Checkpoint Not Found

**Problem**: `FileNotFoundError: SAM2 checkpoint not found`

**Solution**:
```bash
mkdir -p models/sam2
cd models/sam2
curl -L -o sam2_hiera_small.pt https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_small.pt
```

---

## Runtime Issues

### Backend Won't Start

**Problem**: Backend crashes on startup

**Solutions**:

1. Check logs:
```bash
cd backend
python run_server.py
# Review error messages
```

2. Verify environment variables:
```bash
# Check .env file exists
cat backend/.env

# Verify critical variables
echo $SECRET_KEY
echo $DATABASE_URL
```

3. Test database connection:
```python
from db import get_db
next(get_db())  # Should not raise error
```

### Frontend Won't Start

**Problem**: `Error: Cannot find module 'next'`

**Solution**:
```bash
cd frontend-makerkit
pnpm install  # Reinstall dependencies
cd apps/web
pnpm run dev
```

### Port Already in Use

**Problem**: `Error: Port 8000 is already in use`

**Solutions**:

Windows:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

Linux/Mac:
```bash
lsof -ti:8000 | xargs kill -9
```

Or change port in configuration.

---

## Analysis Issues

### Low Confidence Scores

**Problem**: Consistently getting low confidence (<70%)

**Possible Causes**:
1. Poor image quality
2. Unusual defect types
3. Incorrect model loaded
4. Image preprocessing issues

**Solutions**:
1. Check image quality:
   - Resolution >= 224x224
   - Good contrast
   - Proper lighting
   - Clear focus

2. Verify model:
```python
from core.models.yolo_classifier import YOLOClassifier
classifier = YOLOClassifier()
print(classifier.model_path)  # Should point to trained model
```

3. Review XAI explanations to understand model reasoning

### Segmentation Not Working

**Problem**: `has_segmentation: false` in results

**Solutions**:

1. Verify SAM2 is enabled:
```python
analyzer.enable_sam2  # Should be True
```

2. Check guidance strategy:
```python
# Try different strategies
result = analyzer.analyze(image, segmentation_guidance='auto')
result = analyzer.analyze(image, segmentation_guidance='grid')
```

3. Verify defect is detected:
```python
# Classification must succeed for hybrid mode
if result['classification']['is_defect']:
    # Segmentation should work
```

### Out of Memory Errors

**Problem**: `RuntimeError: CUDA out of memory`

**Solutions**:

1. Use smaller SAM2 model:
```env
# backend/.env
SAM2_CHECKPOINT=../models/sam2/sam2_hiera_tiny.pt
```

2. Process on CPU:
```python
analyzer = HybridDefectAnalyzer(device='cpu')
```

3. Reduce image size:
```python
from PIL import  Image
img = Image.open('large_image.png')
img = img.resize((640, 640))
```

4. Clear GPU cache:
```python
import torch
torch.cuda.empty_cache()
```

---

## Performance Issues

### Slow API Response

**Problem**: Requests taking >10 seconds

**Solutions**:

1. Use faster analysis mode:
```bash
# Instead of hybrid mode
curl -X POST "http://localhost:8000/api/xai-qc/detect"

# Or reduce XAI methods
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=gradcam"
```

2. Check GPU utilization:
```bash
nvidia-smi
# GPU usage should be >50% during inference
```

3. Enable model caching (check backend logs)

4. Reduce image size before upload

### High Memory Usage

**Problem**: Backend using >16GB RAM

**Solutions**:

1. Restart backend periodically
2. Limit concurrent requests
3. Configure  memory limits in Docker:
```yaml
deploy:
  resources:
    limits:
      memory: 16G
```

---

## Database Issues

### Connection Errors

**Problem**: `psycopg2.OperationalError: could not connect`

**Solutions**:

1. Verify database is running:
```bash
# PostgreSQL
sudo systemctl status postgresql

# Supabase - check dashboard
```

2. Test connection:
```bash
psql -h localhost -U radikal -d radikal_production
```

3. Check connection string:
```env
# backend/.env
DATABASE_URL=postgresql://user:password@host:port/database
```

4. Increase connection pool:
```env
DATABASE_POOL_SIZE=40
DATABASE_MAX_OVERFLOW=80
```

### Migration Errors

**Problem**: Database schema out of sync

**Solution**:
```bash
cd backend
python -c "from db import init_db; init_db()"
```

---

## Frontend Issues

### "Failed to Fetch" Error

**Problem**: Frontend can't connect to backend

**Solutions**:

1. Verify backend is running:
```bash
curl http://localhost:8000/health
```

2. Check CORS configuration:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Check API_URL in frontend:
```env
# frontend-makerkit/apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Images Not Displaying

**Problem**: Uploaded images don't show

**Solutions**:

1. Check browser console for errors (F12)
2. Verify image format (PNG, JPG, JPEG only)
3. Check file size (<10MB)
4. Clear browser cache
5. Try different browser

### Authentication Issues

**Problem**: Can't log in or session expires

**Solutions**:

1. Check Supabase configuration:
```env
NEXT_PUBLIC_SUPABASE_URL=your_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

2. Clear browser cookies and local storage
3. Verify Supabase project is active
4. Check JWT token expiration settings

---

## Docker Issues

### Container Won't Start

**Problem**: Docker container exits immediately

**Solutions**:

1. Check logs:
```bash
docker logs radikal-backend
docker logs radikal-frontend
```

2. Verify environment variables:
```bash
docker exec radikal-backend env | grep SECRET_KEY
```

3. Check port conflicts:
```bash
docker ps -a
```

### GPU Not Accessible in Docker

**Problem**: CUDA not available in container

**Solutions**:

1. Install NVIDIA Container Toolkit:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. Run with GPU support:
```bash
docker run --gpus all radikal-backend:2.0.0
```

3. In docker-compose:
```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## Common Error Messages

### "Model not loaded"

**Cause**: Model checkpoint not found or loading failed

**Solution**:
```bash
# Verify model exists
ls -lh models/best.pt
ls -lh models/sam2/sam2_hiera_small.pt

# Check model path in config
grep MODEL_PATH backend/.env
```

### "Invalid file format"

**Cause**: Unsupported image format

**Solution**: Convert image to PNG or JPG:
```python
from PIL import Image
img = Image.open('image.bmp')
img.save('image.png')
```

### "Rate limit exceeded"

**Cause**: Too many requests

**Solution**: Wait 60 seconds or configure rate limiting:
```env
# backend/.env
RATE_LIMIT_PER_MINUTE=100
```

### "Database connection pool exhausted"

**Cause**: Too many concurrent database connections

**Solution**:
```env
# backend/.env
DATABASE_POOL_SIZE=40
DATABASE_MAX_OVERFLOW=80
```

---

## Debugging Tips

### Enable Debug Logging

```env
# backend/.env
LOG_LEVEL=DEBUG
DEBUG=true
```

### Check Backend Logs

```bash
# Development
tail -f backend/logs/radikal.log

# Docker
docker logs -f radikal-backend

# Kubernetes
kubectl logs -f deployment/radikal-backend -n radikal-prod
```

### Test Individual Components

```python
# Test YOLOv8
from core.models.yolo_classifier import YOLOClassifier
classifier = YOLOClassifier()
# Test with sample image

# Test SAM2
from core.models.sam2_segmenter import SAM2Segmenter
segmenter = SAM2Segmenter()
# Test with sample image
```

### Monitor Resource Usage

```bash
# CPU/Memory
htop

# GPU
watch -n1 nvidia-smi

# Disk
df -h
```

---

## Getting Additional Help

If issues persist:

1. Check [GitHub Issues](https://github.com/ZenleX-Dost/RadiKal-V2.0/issues)
2. Review backend logs in `backend/logs/`
3. Run diagnostics:
```bash
cd backend
python test_sam2_integration.py
pytest tests/ -v
```
4. Check system requirements
5. Open new GitHub issue with:
   - Error message
   - Log output
   - System information
   - Steps to reproduce

---

## Known Issues

### Issue: Slow first inference

**Status**: Expected behavior  
**Reason**: Model loading and GPU warmup  
**Workaround**: First inference takes ~10s, subsequent ones are fast

### Issue: Memory leak with many requests

**Status**: Under investigation  
**Workaround**: Restart backend periodically

### Issue: SAM2 segmentation timeout

**Status**: Configuration needed  
**Workaround**: Increase timeout in frontend or use smaller SAM2 model
