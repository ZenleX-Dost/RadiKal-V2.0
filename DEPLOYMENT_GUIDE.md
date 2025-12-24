# 🚀 RadiKal V2.0 - Production Deployment Guide

**Version**: 2.0.0  
**Last Updated**: December 20, 2025  
**Environment**: Production-Ready

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup Strategy](#backup-strategy)
10. [Rollback Procedures](#rollback-procedures)
11. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Hardware Requirements

**Minimum (Development/Small Scale)**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- GPU: Not required (CPU inference)

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
- Load Balancer: 2+ nodes
- Database: Managed PostgreSQL with replicas

### Software Requirements

```bash
# Operating System
Ubuntu 22.04 LTS (recommended) or Rocky Linux 9

# Docker
Docker Engine 24.0+
Docker Compose 2.20+

# Kubernetes (optional)
Kubernetes 1.28+
Helm 3.12+

# Database
PostgreSQL 15+ or Supabase

# Python
Python 3.10+

# Node.js
Node.js 18+
pnpm 8+

# NVIDIA Drivers (if using GPU)
NVIDIA Driver 535+
CUDA 12.1+
cuDNN 8.9+
```

---

## ✅ Pre-Deployment Checklist

### Security

- [ ] Generate strong `SECRET_KEY` (32+ characters random string)
- [ ] Update all default passwords
- [ ] Configure firewall rules (allow only 80, 443, 22)
- [ ] Set up SSL/TLS certificates (Let's Encrypt or commercial)
- [ ] Enable database encryption at rest
- [ ] Configure Supabase Row Level Security (RLS)
- [ ] Set up VPN for admin access
- [ ] Enable 2FA for admin accounts

### Configuration

- [ ] Update `.env.production` with real credentials
- [ ] Configure CORS allowed origins for production domain
- [ ] Set up Sentry DSN for error tracking
- [ ] Configure email SMTP for alerts
- [ ] Set up log rotation
- [ ] Configure backup automation
- [ ] Set resource limits (CPU, memory)

### Testing

- [ ] Run full test suite (`pytest backend/tests/`)
- [ ] Load test API endpoints (1000+ concurrent users)
- [ ] Test database backups and restore
- [ ] Verify SSL certificate validity
- [ ] Test rollback procedures
- [ ] Smoke test all critical features

### Monitoring

- [ ] Set up health check endpoints
- [ ] Configure Prometheus metrics collection
- [ ] Set up Grafana dashboards
- [ ] Configure alerting (email, Slack, PagerDuty)
- [ ] Set up log aggregation (ELK or Loki)
- [ ] Configure uptime monitoring (UptimeRobot, Pingdom)

---

## 🌍 Environment Setup

### 1. Create Production Environment File

```bash
cd backend
cp .env.production .env

# Edit .env with your production values
nano .env
```

### 2. Required Environment Variables

```bash
# CRITICAL - Change these!
SECRET_KEY="$(openssl rand -hex 32)"  # Generate strong secret
SUPABASE_DB_URL="postgresql://postgres.xxx:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Domain configuration
ALLOWED_ORIGINS="https://radikal.yourdomain.com,https://app.yourdomain.com"

# Monitoring
SENTRY_DSN="https://your-sentry-dsn@sentry.io/project"

# Email alerts
SMTP_HOST="smtp.gmail.com"
SMTP_USER="alerts@yourdomain.com"
SMTP_PASSWORD="your-app-specific-password"
ALERT_EMAIL="admin@yourdomain.com"
```

### 3. Verify Configuration

```bash
# Check environment
python -c "from core.config import settings; print(settings.ENVIRONMENT)"
# Should output: production

# Test database connection
python -c "from db import init_db; init_db(); print('DB OK')"

# Test GPU (if available)
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

---

## 🗄️ Database Setup

### Option 1: Supabase (Recommended)

1. **Create Supabase Project**
   ```bash
   # Go to https://supabase.com/dashboard
   # Create new project
   # Note: Project URL, anon key, service role key
   ```

2. **Configure Connection Pooling**
   ```
   Project Settings → Database → Connection Pooling
   Mode: Transaction
   Pool Size: 20
   ```

3. **Run Migrations**
   ```bash
   cd backend
   python -c "from db import init_db; init_db()"
   ```

4. **Enable Row Level Security**
   ```sql
   -- Run in Supabase SQL Editor
   ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
   ALTER TABLE detections ENABLE ROW LEVEL SECURITY;
   
   -- Create policies for multi-tenancy
   CREATE POLICY "Users can only see their account's data"
   ON analyses FOR SELECT
   USING (account_id = auth.jwt() ->> 'account_id');
   ```

### Option 2: Self-Hosted PostgreSQL

1. **Install PostgreSQL**
   ```bash
   sudo apt update
   sudo apt install postgresql-15 postgresql-contrib
   ```

2. **Create Database**
   ```sql
   sudo -u postgres psql
   CREATE DATABASE radikal_production;
   CREATE USER radikal WITH ENCRYPTED PASSWORD 'strong_password_here';
   GRANT ALL PRIVILEGES ON DATABASE radikal_production TO radikal;
   ```

3. **Configure for Production**
   ```bash
   sudo nano /etc/postgresql/15/main/postgresql.conf
   
   # Optimize for production
   shared_buffers = 8GB
   effective_cache_size = 24GB
   maintenance_work_mem = 2GB
   checkpoint_completion_target = 0.9
   wal_buffers = 16MB
   default_statistics_target = 100
   random_page_cost = 1.1
   effective_io_concurrency = 200
   work_mem = 104857kB
   min_wal_size = 1GB
   max_wal_size = 4GB
   ```

---

## 🐳 Docker Deployment

### 1. Build Images

```bash
# Build backend
cd backend
docker build -t radikal-backend:2.0.0 .

# Build frontend
cd ../frontend-makerkit
docker build -t radikal-frontend:2.0.0 .
```

### 2. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: radikal-backend:2.0.0
    container_name: radikal-backend
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/models:/app/models:ro
      - backend-data:/app/data
      - backend-exports:/app/exports
      - backend-logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
        reservations:
          cpus: '4'
          memory: 8G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: radikal-frontend:2.0.0
    container_name: radikal-frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G

  nginx:
    image: nginx:alpine
    container_name: radikal-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - backend
      - frontend

volumes:
  backend-data:
  backend-exports:
  backend-logs:
```

### 3. Deploy

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Health check
curl http://localhost:8000/api/health
```

---

## ☸️ Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace radikal-prod
```

### 2. Create Secrets

```bash
kubectl create secret generic radikal-secrets \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=db-password="your-db-password" \
  --from-literal=supabase-key="your-supabase-key" \
  -n radikal-prod
```

### 3. Deploy with Helm

```bash
# Add Helm repo
helm repo add radikal https://charts.radikal.io

# Install
helm install radikal radikal/radikal \
  --namespace radikal-prod \
  --set image.tag=2.0.0 \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=radikal.yourdomain.com \
  --set resources.backend.requests.memory=8Gi \
  --set resources.backend.requests.cpu=4000m
```

### 4. Verify Deployment

```bash
kubectl get pods -n radikal-prod
kubectl get services -n radikal-prod
kubectl get ingress -n radikal-prod
```

---

## 🔒 SSL/TLS Configuration

### Option 1: Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d radikal.yourdomain.com -d api.yourdomain.com

# Auto-renewal is set up automatically
sudo systemctl status certbot.timer
```

### Option 2: Commercial Certificate

```bash
# Generate CSR
openssl req -new -newkey rsa:2048 -nodes \
  -keyout radikal.key \
  -out radikal.csr

# Purchase certificate from CA
# Download certificate files

# Install certificate
sudo cp radikal.crt /etc/ssl/certs/
sudo cp radikal.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/radikal.key
```

---

## 📊 Monitoring Setup

### 1. Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'radikal'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/api/health/metrics'
    scrape_interval: 30s
```

### 2. Grafana Dashboard

```bash
# Import dashboard
Dashboard ID: 15000 (custom RadiKal dashboard)

# Metrics to monitor:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- CPU usage (%)
- Memory usage (%)
- GPU utilization (%)
- Database connections
- Queue depth
```

### 3. Alerting Rules

```yaml
# alerts.yml
groups:
  - name: radikal
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        annotations:
          summary: "CPU usage above 80%"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "Database is down"
```

---

## 💾 Backup Strategy

### Daily Backups

```bash
#!/bin/bash
# /opt/radikal/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/radikal"

# Database backup
pg_dump -h localhost -U radikal -d radikal_production | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Files backup
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" /data/uploads /data/exports

# Model backups
tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" /app/models

# Logs backup
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /app/logs

# Upload to S3
aws s3 sync $BACKUP_DIR s3://radikal-backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### Automated Backup Cron

```bash
# crontab -e
0 2 * * * /opt/radikal/scripts/backup.sh >> /var/log/radikal/backup.log 2>&1
```

---

## 🔄 Rollback Procedures

### Quick Rollback (Docker)

```bash
# Stop current version
docker-compose down

# Start previous version
docker-compose -f docker-compose.prod.v1.9.yml up -d

# Verify
curl http://localhost:8000/api/health
```

### Database Rollback

```bash
# Restore from backup
gunzip -c /backups/radikal/db_20251220_020000.sql.gz | psql -h localhost -U radikal -d radikal_production

# Verify data
psql -h localhost -U radikal -d radikal_production -c "SELECT COUNT(*) FROM analyses;"
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs radikal-backend

# Check database connection
docker exec radikal-backend python -c "from db import get_db; next(get_db())"

# Check GPU
docker exec radikal-backend nvidia-smi

# Check environment
docker exec radikal-backend env | grep SECRET_KEY
```

### High Memory Usage

```bash
# Check memory
docker stats radikal-backend

# Restart with more memory
docker update --memory=16g radikal-backend
docker restart radikal-backend
```

### Database Connection Issues

```bash
# Test connection
psql -h your-db-host -U radikal -d radikal_production

# Check connection pool
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

# Increase pool size in .env
DATABASE_POOL_SIZE=40
DATABASE_MAX_OVERFLOW=80
```

---

## 📞 Support

- **Documentation**: https://docs.radikal.yourdomain.com
- **Status Page**: https://status.radikal.yourdomain.com
- **Support Email**: support@yourdomain.com
- **Emergency Hotline**: +1-XXX-XXX-XXXX

---

## 🎯 Next Steps

1. Set up monitoring dashboards
2. Configure automated alerts
3. Run load tests
4. Train team on operations
5. Document runbooks
6. Schedule maintenance windows

**Deployment Complete! 🎉**
