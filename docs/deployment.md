# Deployment Guide

Production deployment guide for RadiKal V2.0.

## Prerequisites

### Hardware Requirements

**Minimum (Development/Small Scale)**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD

**Recommended (Production)**:
- CPU: 8-16 cores
- RAM: 32 GB
- Storage: 500 GB SSD
- GPU: NVIDIA GPU with 6GB+ VRAM (RTX 3060, RTX 4050, or better)

**Enterprise (High Volume)**:
- CPU: 16-32 cores
- RAM: 64-128 GB
- Storage: 1 TB NVMe SSD
- GPU: NVIDIA A100, A40, or equivalent

### Software Requirements

- Operating System: Ubuntu 22.04 LTS (recommended) or Rocky Linux 9
- Docker Engine 24.0+
- Docker Compose 2.20+
- Kubernetes 1.28+ (optional)
- PostgreSQL 15+ or Supabase
- NVIDIA Driver 535+ (if using GPU)
- CUDA 12.1+

---

## Pre-Deployment Checklist

### Security

- [ ] Generate strong SECRET_KEY (32+ characters)
- [ ] Update all default passwords
- [ ] Configure firewall rules (allow only 80, 443, 22)
- [ ] Set up SSL/TLS certificates
- [ ] Enable database encryption at rest
- [ ] Configure Row Level Security (RLS)
- [ ] Enable 2FA for admin accounts

### Configuration

- [ ] Update `.env.production` with real credentials
- [ ] Configure CORS allowed origins for production domain
- [ ] Set up Sentry DSN for error tracking
- [ ] Configure email SMTP for alerts
- [ ] Set up log rotation
- [ ] Configure backup automation

### Testing

- [ ] Run full test suite
- [ ] Load test API endpoints (1000+ concurrent users)
- [ ] Test database backups and restore
- [ ] Verify SSL certificate validity
- [ ] Test rollback procedures

---

## Environment Setup

### 1. Create Production Environment File

```bash
cd backend
cp .env.production .env
```

### 2. Required Environment Variables

```bash
# CRITICAL - Change these!
SECRET_KEY="$(openssl rand -hex 32)"
SUPABASE_DB_URL="postgresql://postgres:PASSWORD@host:6543/postgres"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Domain configuration
ALLOWED_ORIGINS="https://radikal.yourdomain.com"

# Monitoring
SENTRY_DSN="https://your-sentry-dsn@sentry.io/project"

# Email alerts
SMTP_HOST="smtp.gmail.com"
SMTP_USER="alerts@yourdomain.com"
SMTP_PASSWORD="your-app-specific-password"
```

---

## Docker Deployment

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
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

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
    depends_on:
      - backend
      - frontend

volumes:
  backend-data:
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
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

#  Get certificate
sudo certbot --nginx -d radikal.yourdomain.com

# Auto-renewal is set up automatically
sudo systemctl status certbot.timer
```

### Option 2: Commercial Certificate

```bash
# Generate CSR
openssl req -new -newkey rsa:2048 -nodes \
  -keyout radikal.key \
  -out radikal.csr

# Install certificate after purchase
sudo cp radikal.crt /etc/ssl/certs/
sudo cp radikal.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/radikal.key
```

---

## Database Setup

### Supabase (Recommended)

1. Create Supabase project at https://supabase.com
2. Configure connection pooling
3. Run migrations
4. Enable Row Level Security

### Self-Hosted PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql-15

# Create database
sudo -u postgres psql
CREATE DATABASE radikal_production;
CREATE USER radikal WITH ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE radikal_production TO radikal;
```

---

## Monitoring Setup

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'radikal'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/health/metrics'
    scrape_interval: 30s
```

### Grafana

```bash
# Import dashboard
Dashboard ID: 15000 (custom RadiKal dashboard)

# Metrics to monitor:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (%)
- CPU/Memory/GPU usage
```

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: radikal
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
      
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
```

---

## Backup Strategy

### Daily Backups

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/radikal"

# Database backup
pg_dump radikal_production | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Files backup
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" /data/uploads

# Upload to S3
aws s3 sync $BACKUP_DIR s3://radikal-backups/

# Keep 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

### Automated Cron

```bash
# crontab -e
0 2 * * * /opt/radikal/scripts/backup.sh
```

---

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace radikal-prod
```

### 2. Create Secrets

```bash
kubectl create secret generic radikal-secrets \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=db-password="password" \
  -n radikal-prod
```

### 3. Deploy

```bash
kubectl apply -f k8s/ -n radikal-prod
```

---

## Performance Tuning

### Backend Optimization

```env
# backend/.env
WORKERS=4
WORKER_CONNECTIONS=1000
KEEP_ALIVE=5
TIMEOUT=60
```

### Database Optimization

```sql
# PostgreSQL tuning
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
max_connections = 200
```

###  Nginx Optimization

```nginx
worker_processes auto;
worker_connections 4096;
keepalive_timeout 65;
gzip on;
gzip_types text/plain application/json;
```

---

## Rollback Procedures

### Docker Rollback

```bash
# Stop current version
docker-compose down

# Start previous version
docker-compose -f docker-compose.prod.v1.9.yml up -d
```

### Database Rollback

```bash
# Restore from backup
gunzip -c /backups/db_20260114.sql.gz | psql radikal_production
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs radikal-backend

# Check database connection
docker exec radikal-backend python -c "from db import get_db; next(get_db())"

# Check GPU
docker exec radikal-backend nvidia-smi
```

### High Memory Usage

```bash
# Check memory
docker stats radikal-backend

# Increase limit
docker update --memory=16g radikal-backend
docker restart radikal-backend
```

---

## Post-Deployment

1. Verify health endpoints
2. Test all critical paths
3. Monitor logs for errors
4. Check metric dashboards
5. Test backup/restore
6. Document any custom configurations

---

## Support

For deployment issues:

- Review this guide
- Check logs in `backend/logs/`
- Monitor Grafana dashboards
- Contact DevOps team

For complete deployment details, see the full [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) file.
