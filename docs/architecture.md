# Architecture

System architecture documentation for RadiKal V2.0.

## Overview

RadiKal V2.0 is built on a modern, production-ready architecture using:

- **Backend**: FastAPI + PyTorch (Python 3.10+)
- **Frontend**: Next.js 15 + Makerkit (TypeScript)
- **Database**: Supabase (PostgreSQL)
- **ML Models**: YOLOv8 + SAM2
- **Deployment**: Docker + Kubernetes ready

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Next.js 15 + Makerkit (Port 3000)             │ │
│  │  - React 18 Components                                 │ │
│  │  - TypeScript + TailwindCSS v4                        │ │
│  │  - Shadcn UI Components                               │ │
│  │  - Supabase Auth Integration                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST
                           │
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          FastAPI Server (Port 8000)                    │ │
│  │  - CORS Middleware                                     │ │
│  │  - Rate Limiting                                       │ │
│  │  - JWT Authentication                                  │ │
│  │  - Error Handling                                      │ │
│  │  - Request Validation                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                    │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Detection   │  │     XAI      │  │  Segmentation   │  │
│  │    Service    │  │   Service    │  │     Service     │  │
│  │   (YOLOv8)    │  │ (4 Methods)  │  │     (SAM2)      │  │
│  └───────────────┘  └──────────────┘  └─────────────────┘  │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │    Hybrid     │  │    Batch     │  │     Export      │  │
│  │   Analyzer    │  │  Processor   │  │    Service      │  │
│  └───────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────┐
│                       Model Layer                            │
│  ┌────────────────────────┐  ┌───────────────────────────┐ │
│  │   YOLOv8 Classifier   │  │    SAM2 Segmenter        │ │
│  │   - 4 Defect Classes   │  │    - Zero-shot model      │ │
│  │   - GPU Accelerated    │  │    - Pixel-level masks    │ │
│  │   - ~50ms inference    │  │    - ~2s inference        │ │
│  └────────────────────────┘  └───────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              XAI Models                                │ │
│  │  Grad-CAM  │  SHAP  │  LIME  │  Integrated Gradients │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ┌────────────────────────┐  ┌───────────────────────────┐ │
│  │  Supabase (PostgreSQL) │  │   File Storage            │ │
│  │  - Analysis results    │  │   - Uploaded images       │ │
│  │  - User data           │  │   - Generated reports     │ │
│  │  - Audit logs          │  │   - Model checkpoints     │ │
│  └────────────────────────┘  └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────┐
│                   Monitoring & Logging                       │
│  ┌────────────┐  ┌──────────┐  ┌─────────┐  ┌───────────┐ │
│  │ Prometheus │  │  Grafana │  │ MLflow  │  │   Sentry  │ │
│  │  Metrics   │  │Dashboard │  │Tracking │  │   Errors  │ │
│  └────────────┘  └──────────┘  └─────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Frontend Architecture

**Technology Stack**:
- Framework: Next.js 15 (App Router)
- Language: TypeScript
- Styling: TailwindCSS v4
- UI Library: Shadcn UI
- Icons: Lucide
- State Management: React Context + Hooks
- API Client: Fetch API with custom wrapper

**Key Features**:
- Server-Side Rendering (SSR)
- Static Site Generation (SSG)
- API Routes
- Internationalization (i18n)
- Authentication (Supabase)
- Real-time updates (SSE)

**Directory Structure**:
```
frontend-makerkit/apps/web/
├── app/                    # Next.js App Router
│   ├── home/              # Main application
│   │   ├── analysis/      # Image analysis page
│   │   ├── batch/         # Batch processing
│   │   └── settings/      # User settings
│   └── auth/              # Authentication pages
├── components/            # React components
│   ├── radikal/          # RadiKal-specific components
│   └── ui/               # Shared UI components
├── lib/                   # Utilities and helpers
│   └── radikal/          # RadiKal API client
└── types/                # TypeScript definitions
```

### Backend Architecture

**Technology Stack**:
- Framework: FastAPI 0.104+
- Language: Python 3.10+
- ML Framework: PyTorch 2.5.1
- Database ORM: SQLAlchemy
- Task Queue: (Planned: Celery)
- Caching: (Planned: Redis)

**API Layer**:
```
backend/api/
├── routes.py              # API endpoints
├── schemas.py             # Pydantic schemas
├── dependencies.py        # DI and middleware
└── middleware/
    ├── auth.py           # JWT authentication
    ├── rate_limit.py     # Rate limiting
    └── error_handler.py  # Error handling
```

**Business Logic Layer**:
```
backend/core/
├── models/
│   ├── yolo_classifier.py         # YOLOv8 wrapper
│   ├── sam2_segmenter.py          # SAM2 wrapper
│   └── hybrid_defect_analyzer.py  # Combined analyzer
├── xai/
│   ├── gradcam.py                 # Grad-CAM explainer
│   ├── shap_explainer.py          # SHAP explainer
│   ├── lime_explainer.py          # LIME explainer
│   └── integrated_gradients.py    # IG explainer
├── preprocessing/
│   └── image_processor.py         # Image preprocessing
└── metrics/
    └── evaluator.py               # Performance metrics
```

---

## Data Flow

### Single Image Analysis Flow

```
1. User uploads image via frontend
   │
   ↓
2. Frontend sends POST request to /api/xai-qc/analyze-hybrid
   │
   ↓
3. API Gateway validates request
   - Authentication
   - File type validation
   - Rate limiting
   │
   ↓
4. Business Logic Layer
   ├─→ YOLOv8 Classifier
   │   │
   │   ↓
   │   Classification result (LP/PO/CR/ND)
   │
   └─→ SAM2 Segmenter (if hybrid mode)
       │
       ↓
       Segmentation mask
   │
   ↓
5. XAI Service (if requested)
   - Generate explanations
   - Create heatmaps
   - Calculate consensus
   │
   ↓
6. Response aggregation
   - Combine all results
   - Generate visualizations
   - Create response JSON
   │
   ↓
7. Save to database
   │
   ↓
8. Return results to frontend
   │
   ↓
9. Frontend displays results
   - Classification
   - Segmentation overlay
   - XAI heatmaps
```

### Batch Processing Flow

```
1. User uploads multiple images
   │
   ↓
2. Frontend creates batch job
   │
   ↓
3. Backend queues images
   │
   ↓
4. Concurrent processing (3 images at a time)
   ├─→ Image 1 analysis
   ├─→ Image 2 analysis
   └─→ Image 3 analysis
   │
   ↓
5. Results aggregation
   │
   ↓
6. Real-time updates via SSE
   │
   ↓
7. Final batch report generation
```

---

## Database Schema

### Tables

**analyses**
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    account_id UUID,
    image_path VARCHAR(500),
    predicted_class INT,
    predicted_class_name VARCHAR(50),
    confidence FLOAT,
    mode VARCHAR(20),
    created_at TIMESTAMP,
    metadata JSONB
);
```

**segmentations**
```sql
CREATE TABLE segmentations (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analyses(id),
    num_segments INT,
    total_coverage_percent FLOAT,
    bbox JSONB,
    centroid JSONB,
    created_at TIMESTAMP
);
```

**xai_explanations**
```sql
CREATE TABLE xai_explanations (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analyses(id),
    method VARCHAR(50),
    confidence_score FLOAT,
    heatmap_path VARCHAR(500),
    created_at TIMESTAMP
);
```

---

## Security Architecture

### Authentication Flow

```
1. User enters credentials
   │
   ↓
2. Frontend sends to Supabase Auth
   │
   ↓
3. Supabase validates and issues JWT
   │
   ↓
4. Frontend stores JWT
   │
   ↓
5. All API requests include JWT in Authorization header
   │
   ↓
6. Backend validates JWT
   - Verify signature
   - Check expiration
   - Validate claims
   │
   ↓
7. Grant or deny access
```

### Security Layers

1. **Network Security**
   - HTTPS/TLS encryption
   - CORS policy
   - Rate limiting

2. **Application Security**
   - JWT authentication
   - RBAC (Role-Based Access Control)
   - Input validation
   - SQL injection prevention

3. **Data Security**
   - Encryption at rest
   - Encryption in transit
   - Row-level security (Supabase)
   - Audit logging

---

## Scalability

### Horizontal Scaling

**Backend**:
- Stateless API design
- Load balancer distribution
- Multiple API instances
- Shared database connection pool

**Frontend**:
- Multiple frontend instances
- CDN for static assets
- Edge caching

### Vertical Scaling

**GPU Resources**:
- Larger GPU for faster inference
- Multi-GPU support (planned)
- GPU memory optimization

**Database**:
- Connection pooling
- Read replicas
- Query optimization

---

## Performance Optimization

### Backend Optimizations

1. **Model Loading**
   - Lazy loading
   - Model caching
   - GPU pre-allocation

2. **Request Processing**
   - Async/await patterns
   - Concurrent image processing
   - Background tasks

3. **Database**
   - Connection pooling
   - Index optimization
   - Query caching

### Frontend Optimizations

1. **Code Splitting**
   - Dynamic imports
   - Route-based splitting
   - Component lazy loading

2. **Image Optimization**
   - Client-side compression
   - Progressive loading
   - Thumbnail generation

3. **Caching**
   - API response caching
   - Static asset caching
   - Service worker (planned)

---

## Deployment Architecture

### Docker Deployment

```
docker-compose.yml 
├── backend (Port 8000)
│   - FastAPI server
│   - GPU access
│   - Model volumes
├── frontend (Port 3000)
│   - Next.js server
│   - Static assets
└── nginx (Ports 80, 443)
    - Reverse proxy
    - SSL termination
    - Load balancing
```

### Kubernetes Deployment

```
k8s/
├── namespace.yaml
├── backend-deployment.yaml
│   - 3 replicas
│   - GPU node affinity
│   - Resource limits
├── frontend-deployment.yaml
│   - 2 replicas
│   - Auto-scaling
├── nginx-ingress.yaml
│   - SSL certificates
│   - Load balancing
└── services.yaml
    - Backend service
    - Frontend service
```

---

## Monitoring Architecture

### Metrics Collection

**Prometheus**:
- API request rates
- Response times (p50, p95, p99)
- Error rates
- Resource usage

**Custom Metrics**:
- Inference times
- Model accuracy
- XAI generation times
- Batch processing throughput

### Visualization

**Grafana Dashboards**:
- System health overview
- API performance metrics
- Model performance metrics
- Business metrics

### Alerting

**Alert Conditions**:
- High error rate (>5%)
- Slow response time (>5s p95)
- High resource usage (>80%)
- Low accuracy (<90%)

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend Framework | Next.js 15 | React framework |
| Frontend Language | TypeScript | Type safety |
| Frontend Styling | TailwindCSS v4 | CSS framework |
| Frontend UI | Shadcn UI | Component library |
| Backend Framework | FastAPI | API server |
| Backend Language | Python 3.10+ | Main language |
| ML Framework | PyTorch 2.5.1 | Deep learning |
| Classification Model | YOLOv8 | Defect detection |
| Segmentation Model | SAM2 | Pixel-level masks |
| Database | Supabase/PostgreSQL | Data storage |
| Authentication | Supabase Auth | User management |
| Monitoring | Prometheus | Metrics |
| Visualization | Grafana | Dashboards |
| ML Tracking | MLflow | Experiments |
| Error Tracking | Sentry | Error monitoring |
| Deployment | Docker | Containerization |
| Orchestration | Kubernetes | Container orchestration |

---

## Design Principles

1. **Separation of Concerns**: Clear layer boundaries
2. **Modularity**: Independent, reusable components
3. **Scalability**: Horizontal and vertical scaling support
4. **Security**: Defense in depth
5. **Performance**: Optimized at every layer
6. **Maintainability**: Clean code, documentation
7. **Observability**: Comprehensive monitoring
8. **Reliability**: Error handling, fallbacks

---

## Future Architecture Enhancements

- Microservices architecture
- Redis caching layer
- Celery task queue
- WebSocket real-time updates
- Multi-region deployment
- Auto-scaling policies
- Advanced monitoring (APM)
- ML model versioning system
