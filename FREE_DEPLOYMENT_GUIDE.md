# Free Deployment Guide for RadiKal V2.0

Complete guide to deploying RadiKal V2.0 using free hosting services.

## Overview

RadiKal V2.0 consists of three main components:
1. **Documentation** - Read the Docs (Free)
2. **Backend API** - FastAPI with ML models (Limited free options)
3. **Frontend** - Next.js application (Free)
4. **Database** - PostgreSQL/Supabase (Free tier available)

## Important Limitations

### GPU Requirements

RadiKal requires GPU for:
- YOLOv8 classification (~2GB VRAM)
- SAM2 segmentation (~4-6GB VRAM)

**Free hosting services do NOT provide GPU access.**

### Solutions:
1. **CPU-only mode** - Slower but works (10-30x slower)
2. **Local backend** - Run ML backend locally, deploy frontend only
3. **Model API services** - Use cloud ML APIs (limited free tier)

---

## Option 1: Full Stack Free Deployment (CPU-only)

### Components

| Component | Service | Free Tier Limits |
|-----------|---------|------------------|
| Documentation | Read the Docs | Unlimited for open source |
| Frontend | Vercel | Unlimited for personal projects |
| Backend | Render | 750 hours/month, CPU-only |
| Database | Supabase | 500MB database, 2GB bandwidth |

### Step-by-Step Deployment

#### 1. Deploy Documentation (Read the Docs)

**Steps:**
1. Push your repository to GitHub
2. Go to https://readthedocs.org
3. Click "Import a Project"
4. Connect your GitHub account
5. Select `RadiKal-V2.0` repository
6. Click "Build"

**Result:** Documentation live at `https://radikal-v2.readthedocs.io`

**Cost:** FREE

---

#### 2. Deploy Database (Supabase)

**Steps:**
1. Go to https://supabase.com
2. Create free account
3. Click "New Project"
4. Configure:
   - Name: `radikal-v2`
   - Database Password: (strong password)
   - Region: Closest to you
5. Wait for database provisioning (~2 minutes)
6. Copy credentials:
   - Project URL
   - Anon key
   - Service role key
   - Database connection string

**Free Tier:**
- 500MB database storage
- 2GB bandwidth/month
- Unlimited API requests

**Cost:** FREE

---

#### 3. Deploy Backend (Render)

**Prepare Backend:**

Create `backend/Dockerfile.cpu`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run on CPU only
ENV CUDA_VISIBLE_DEVICES=""
ENV TORCH_DEVICE="cpu"

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `render.yaml`:
```yaml
services:
  - type: web
    name: radikal-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.11
      - key: CUDA_VISIBLE_DEVICES
        value: ""
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_ORIGINS
        value: https://your-frontend.vercel.app
```

**Deploy Steps:**
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect `RadiKal-V2.0` repository
5. Configure:
   - Name: `radikal-backend`
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `DATABASE_URL`: (from Supabase)
   - `SECRET_KEY`: (auto-generate)
   - `ALLOWED_ORIGINS`: (will add after frontend deploy)
7. Click "Create Web Service"

**Free Tier:**
- 750 hours/month
- 512MB RAM
- CPU-only
- Auto-sleep after 15min inactivity
- Slow cold starts

**Cost:** FREE

**Note:** Backend will be SLOW (~10-30s per analysis) due to CPU-only inference.

---

#### 4. Deploy Frontend (Vercel)

**Prepare Frontend:**

Create `frontend-makerkit/apps/web/.env.production`:
```env
NEXT_PUBLIC_API_URL=https://radikal-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

**Deploy Steps:**
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Add New..." → "Project"
4. Import `RadiKal-V2.0` repository
5. Configure:
   - Framework Preset: `Next.js`
   - Root Directory: `frontend-makerkit/apps/web`
   - Build Command: `pnpm run build`
   - Output Directory: `.next`
6. Add environment variables:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
7. Click "Deploy"

**Free Tier:**
- Unlimited bandwidth
- 100GB bandwidth/month
- Automatic HTTPS
- Global CDN
- Instant deployments

**Cost:** FREE

**Result:** Frontend live at `https://radikal-v2.vercel.app`

---

## Option 2: Hybrid Deployment (Best Free Option)

Run ML backend locally with GPU, deploy frontend and docs.

### Architecture

```
Frontend (Vercel) → API Gateway (Free Cloudflare Tunnel) → Local Backend (Your PC with GPU)
Database (Supabase)
Docs (Read the Docs)
```

### Components

| Component | Location | Cost |
|-----------|----------|------|
| Frontend | Vercel | FREE |
| Backend | Your PC (GPU) | FREE |
| Tunnel | Cloudflare | FREE |
| Database | Supabase | FREE |
| Docs | Read the Docs | FREE |

### Setup

#### 1. Install Cloudflare Tunnel

```bash
# Windows
winget install Cloudflare.cloudflared

# Verify
cloudflared --version
```

#### 2. Create Tunnel

```bash
# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create radikal-backend

# Note the Tunnel ID
```

#### 3. Configure Tunnel

Create `cloudflared-config.yml`:
```yaml
tunnel: <your-tunnel-id>
credentials-file: C:\Users\<YourUsername>\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: radikal-api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

#### 4. Run Tunnel

```bash
# Start tunnel
cloudflared tunnel run radikal-backend
```

#### 5. Start Local Backend

```bash
cd backend
python run_server.py
```

#### 6. Deploy Frontend to Vercel

Use the API URL: `https://radikal-api.yourdomain.com`

### Advantages

- Full GPU acceleration (fast inference)
- No cloud compute costs
- Frontend on CDN (fast)
- Database in cloud (accessible)

### Disadvantages

- Your PC must be running
- Your internet must be stable
- No redundancy

---

## Option 3: Documentation Only (Free)

Deploy only the documentation, provide local installation instructions.

### Steps

1. Deploy docs to Read the Docs (see above)
2. Add comprehensive installation guide
3. Users install locally

**Cost:** FREE

**Best for:** Open source projects, local use

---

## Alternative Free Services

### Backend Alternatives

1. **Railway** (https://railway.app)
   - Free tier: $5 credit/month
   - Good for hobby projects
   - Easy deployment

2. **Fly.io** (https://fly.io)
   - Free tier: 3 small VMs
   - Better performance than Render
   - More configuration needed

3. **Google Cloud Run** (https://cloud.google.com/run)
   - Free tier: 2 million requests/month
   - 180,000 vCPU-seconds
   - 360,000 GiB-seconds memory
   - Serverless (auto-scale to zero)

### Frontend Alternatives

1. **Netlify** (https://netlify.com)
   - Similar to Vercel
   - 100GB bandwidth/month
   - Free SSL

2. **GitHub Pages** (https://pages.github.com)
   - Static sites only
   - Would need to export Next.js as  static

### Database Alternatives

1. **Render PostgreSQL** (https://render.com)
   - Free tier: 90 days
   - Then paid

2. **ElephantSQL** (https://elephantsql.com)
   - Free tier: 20MB storage
   - Very limited

---

## Recommended Free Setup

### For Testing/Portfolio

```
Frontend: Vercel (Free)
Backend: Render (Free, CPU-only)
Database: Supabase (Free tier)
Docs: Read the Docs (Free)
```

**Total Cost:** $0/month

**Limitations:**
- Slow inference (CPU-only)
- Backend sleeps after inactivity
- Limited database storage

### For Production Use

```
Frontend: Vercel (Free)
Backend: Your PC with Cloudflare Tunnel (Free)
Database: Supabase (Free tier)
Docs: Read the Docs (Free)
```

**Total Cost:** $0/month + electricity

**Limitations:**
- Your PC must run 24/7
- Single point of failure

---

## Cost Comparison

### Free Deployment

| Item | Service | Cost |
|------|---------|------|
| Frontend | Vercel | $0 |
| Backend | Render (CPU) | $0 |
| Database | Supabase | $0 |
| Docs | Read the Docs | $0 |
| **Total** | | **$0/month** |

### Paid Deployment (for comparison)

| Item | Service | Cost |
|------|---------|------|
| Frontend | Vercel Pro | $20/month |
| Backend | Render (w/ GPU) | $100+/month |
| Database | Supabase Pro | $25/month |
| Docs | Read the Docs | $0 |
| **Total** | | **$145+/month** |

---

## Step-by-Step: Quick Free Deployment

### 1. Documentation (5 minutes)

```bash
# Already done! Just push to GitHub
git add .
git commit -m "Add Read the Docs documentation"
git push

# Then import on readthedocs.org
```

### 2. Database (5 minutes)

1. Create Supabase account
2. New project
3. Copy credentials

### 3. Frontend (10 minutes)

1. Add environment variables to Vercel
2. Import from GitHub
3. Deploy

### 4. Backend (15 minutes)

1. Create `render.yaml` (see above)
2. Push to GitHub
3. Import on Render
4. Add environment variables
5. Deploy

**Total Time:** ~35 minutes

**Total Cost:** $0

---

## Troubleshooting Free Deployments

### Render Backend Sleeping

**Problem:** Backend sleeps after 15 minutes of inactivity on free tier.

**Solutions:**
1. Upgrade to paid plan ($7/month for always-on)
2. Use cron job to ping every 10 minutes
3. Accept cold starts (15-30s on first request)

### Slow Inference on CPU

**Problem:** Analysis takes 30+ seconds without GPU.

**Solutions:**
1. Use smaller models (YOLOv8n instead of YOLOv8s)
2. Reduce image resolution
3. Skip SAM2 segmentation
4. Use local GPU with Cloudflare Tunnel

### Supabase Storage Limit

**Problem:** 500MB database limit reached.

**Solutions:**
1. Store images externally (Cloudinary free tier)
2. Clean old analyses regularly
3. Upgrade to paid plan ($25/month for 8GB)

---

## Next Steps

1. Choose your deployment option
2. Follow the step-by-step guides above
3. Test the deployment
4. Monitor usage and performance

For detailed deployment guides, see:
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

---

## Summary

**Best Free Option for Most Users:**
- Frontend on Vercel
- Backend on Render (CPU-only, expect slow inference)
- Database on Supabase
- Documentation on Read the Docs

**Best Free Option for Fast Performance:**
- Frontend on Vercel
- Backend locally with Cloudflare Tunnel
- Database on Supabase
- Documentation on Read the Docs

Choose based on your priorities: convenience vs. performance.
