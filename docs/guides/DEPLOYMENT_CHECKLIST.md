# Production Deployment Checklist

This checklist ensures all critical components are ready for production deployment.

## Pre-Deployment Checklist

### 1. Environment Configuration ✅
- [ ] Copy `.env.example` to `.env`
- [ ] Set strong `JWT_SECRET` (min 32 characters)
- [ ] Configure `MAKERKIT_API_URL` for your frontend
- [ ] Set appropriate `CORS_ORIGINS`
- [ ] Configure `MLFLOW_TRACKING_URI` for production
- [ ] Set `LOG_LEVEL=WARNING` for production
- [ ] Configure monitoring (Sentry DSN if using)

### 2. Model Training ✅
- [ ] Train model on production dataset (not synthetic)
- [ ] Achieve target mAP > 0.7
- [ ] Validate on held-out test set
- [ ] Save best model to `models/checkpoints/best_model.pth`
- [ ] Document model performance in `models/model_card.yaml`
- [ ] Run calibration on validation set
- [ ] Calculate and document ECE

### 3. Data Preparation ✅
- [ ] Organize training data in `data/train/`
- [ ] Organize validation data in `data/val/`
- [ ] Organize test data in `data/test/`
- [ ] Create COCO-format annotations
- [ ] Document dataset in `data/dataset_card.yaml`
- [ ] Initialize DVC for data versioning
- [ ] Push data to DVC remote

### 4. Security ✅
- [ ] Change default `JWT_SECRET`
- [ ] Enable HTTPS in production
- [ ] Configure firewall rules
- [ ] Set up rate limiting (optional)
- [ ] Enable CORS with specific origins only
- [ ] Review and update Makerkit auth integration
- [ ] Set up secret management (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Enable API key authentication (optional)

### 5. Testing ✅
- [ ] Run all unit tests: `pytest tests/ -v`
- [ ] Verify test coverage > 85%: `pytest tests/ --cov=core --cov=api`
- [ ] Run integration tests: `pytest tests/test_api_integration.py`
- [ ] Load test API endpoints (Apache Bench, Locust, etc.)
- [ ] Test with real images from production
- [ ] Verify XAI explanations are meaningful
- [ ] Test error handling and edge cases

### 6. Performance Optimization ✅
- [ ] Enable mixed precision training if using GPU
- [ ] Optimize batch size for your GPU
- [ ] Configure proper number of workers for DataLoader
- [ ] Enable model caching if needed
- [ ] Set up Redis for caching (optional)
- [ ] Configure CDN for static assets (optional)
- [ ] Optimize Docker image size (multi-stage build)

### 7. MLOps Setup ✅
- [ ] MLflow server is running and accessible
- [ ] DVC remote is configured (S3, Azure Blob, etc.)
- [ ] CI/CD pipeline is set up (GitHub Actions)
- [ ] Automated tests run on every commit
- [ ] Model versioning is enabled
- [ ] Experiment tracking is working
- [ ] Set up automated retraining pipeline (optional)

### 8. Monitoring & Logging ✅
- [ ] Configure structured logging
- [ ] Set up log aggregation (ELK, CloudWatch, etc.)
- [ ] Enable application monitoring (Sentry, New Relic, etc.)
- [ ] Set up health check endpoint monitoring
- [ ] Configure alerting for errors
- [ ] Set up metrics dashboard (Grafana, etc.)
- [ ] Monitor GPU usage and memory
- [ ] Track API latency and throughput

### 9. Docker Deployment ✅
- [ ] Build Docker image: `docker build -t radikal-backend .`
- [ ] Test Docker image locally: `docker run -p 8000:8000 radikal-backend`
- [ ] Push to container registry (Docker Hub, ECR, ACR, etc.)
- [ ] Configure docker-compose for production
- [ ] Set up persistent volumes for models and data
- [ ] Configure resource limits (CPU, memory)
- [ ] Test container orchestration (Kubernetes, Docker Swarm, etc.)

### 10. Database (If Applicable) ⚠️
- [ ] Set up PostgreSQL/MySQL database
- [ ] Configure connection pooling
- [ ] Run database migrations
- [ ] Set up automated backups
- [ ] Configure replication (optional)
- [ ] Test database failover

### 11. Frontend Integration ⚠️
- [ ] Frontend is deployed and accessible
- [ ] API endpoints are reachable from frontend
- [ ] CORS is properly configured
- [ ] Authentication flow works end-to-end
- [ ] Test all user workflows
- [ ] Verify XAI visualizations render correctly

### 12. Documentation ✅
- [ ] API documentation is up-to-date (`/api/docs`)
- [ ] README.md has deployment instructions
- [ ] Environment variables are documented
- [ ] Architecture diagrams are current
- [ ] Troubleshooting guide is available
- [ ] User manual is complete (if applicable)

### 13. Backup & Recovery ✅
- [ ] Automated model backups
- [ ] Data backup strategy
- [ ] Disaster recovery plan
- [ ] Test restore procedure
- [ ] Document RTO and RPO

### 14. Compliance & Legal ⚠️
- [ ] Review data privacy requirements (GDPR, HIPAA, etc.)
- [ ] Obtain necessary approvals for AI system
- [ ] Document model limitations
- [ ] Set up audit logging
- [ ] Review liability and insurance
- [ ] Prepare for regulatory inspection

## Production Deployment

### Option 1: Docker Compose (Recommended for Small-Medium)
```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 2. Start services
docker-compose up -d

# 3. Verify health
curl http://localhost:8000/api/xai-qc/health

# 4. Check logs
docker-compose logs -f backend
```

### Option 2: Kubernetes (Recommended for Large-Scale)
```bash
# 1. Create namespace
kubectl create namespace radikal

# 2. Create secrets
kubectl create secret generic radikal-secrets \
  --from-env-file=.env \
  -n radikal

# 3. Deploy
kubectl apply -f k8s/ -n radikal

# 4. Verify
kubectl get pods -n radikal
kubectl get svc -n radikal
```

### Option 3: Cloud Platforms

#### AWS (ECS + ECR)
```bash
# 1. Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag radikal-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/radikal-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/radikal-backend:latest

# 2. Create ECS task definition and service
# 3. Configure load balancer
# 4. Set up auto-scaling
```

#### Azure (Container Instances + ACR)
```bash
# 1. Push to ACR
az acr login --name <registry>
docker tag radikal-backend:latest <registry>.azurecr.io/radikal-backend:latest
docker push <registry>.azurecr.io/radikal-backend:latest

# 2. Deploy to ACI
az container create \
  --resource-group radikal-rg \
  --name radikal-backend \
  --image <registry>.azurecr.io/radikal-backend:latest \
  --cpu 2 --memory 4 \
  --ports 8000
```

#### GCP (Cloud Run + GCR)
```bash
# 1. Push to GCR
gcloud auth configure-docker
docker tag radikal-backend:latest gcr.io/<project>/radikal-backend:latest
docker push gcr.io/<project>/radikal-backend:latest

# 2. Deploy to Cloud Run
gcloud run deploy radikal-backend \
  --image gcr.io/<project>/radikal-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Post-Deployment Checklist

### Immediate (Day 1)
- [ ] Verify all endpoints are accessible
- [ ] Test detection workflow end-to-end
- [ ] Monitor error logs for first 24 hours
- [ ] Check system resource usage
- [ ] Verify MLflow is tracking experiments
- [ ] Test backup and restore procedures

### Short-Term (Week 1)
- [ ] Analyze API performance metrics
- [ ] Review and tune model performance
- [ ] Gather user feedback
- [ ] Fix any critical bugs
- [ ] Document lessons learned
- [ ] Set up on-call rotation

### Medium-Term (Month 1)
- [ ] Review security audit
- [ ] Analyze model drift
- [ ] Plan for model retraining
- [ ] Optimize costs
- [ ] Scale infrastructure if needed
- [ ] Implement user-requested features

## Rollback Plan

If deployment fails:

1. **Immediate Rollback**
   ```bash
   # Docker Compose
   docker-compose down
   git checkout <previous-tag>
   docker-compose up -d
   
   # Kubernetes
   kubectl rollout undo deployment/radikal-backend -n radikal
   ```

2. **Notify Users**: Send notification about temporary service interruption

3. **Investigate**: Review logs and identify root cause

4. **Fix**: Implement fix in development environment

5. **Test**: Thoroughly test fix before redeploying

6. **Redeploy**: Follow deployment checklist again

## Support Contacts

- **Development Team**: dev@example.com
- **Operations Team**: ops@example.com
- **Security Team**: security@example.com
- **On-Call**: +1-XXX-XXX-XXXX

## Important URLs

- **Production API**: https://api.radikal.example.com
- **MLflow**: https://mlflow.radikal.example.com
- **Monitoring**: https://monitoring.radikal.example.com
- **Docs**: https://docs.radikal.example.com
- **Status Page**: https://status.radikal.example.com

---

**Last Updated**: October 14, 2025  
**Version**: 1.0.0  
**Owner**: RadiKal DevOps Team
