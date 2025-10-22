# XAI Visual Quality Control Module - Backend

A production-grade backend service for Explainable AI (XAI) visual quality control, specifically designed for radiographic and standard vision images. This service provides robust defect detection, segmentation, and comprehensive explainability features.

## Features

- **Defect Detection & Segmentation**: Identify and segment defects in radiographic images
- **XAI Methods**: Grad-CAM, SHAP, LIME, and Integrated Gradients for model explainability
- **Uncertainty Quantification**: MC-Dropout and ensemble methods with calibration
- **Comprehensive Metrics**: Business and technical KPIs (FN, FP, mAP, IoU, Dice Score)
- **MLOps Integration**: MLflow for experiment tracking, DVC for data/model versioning
- **Production-Ready API**: FastAPI with full OpenAPI documentation
- **Makerkit Integration**: Secure authentication and role-based access control

## Architecture

```
┌─────────────────────────────────────────┐
│  UI Layer (Next.js with Makerkit)       │
│  - Operator HMI Dashboard               │
│  - Image Review & Explanation           │
└──────────────┬──────────────────────────┘
               │ HTTP/REST API Call
┌──────────────▼──────────────────────────┐
│  API Layer (FastAPI)                    │
│  - /api/xai-qc/detect, /explain, etc.   │
│  - Authentication & Validation          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Core ML Layer                          │
│  - Detection/Segmentation Models        │
│  - XAI Engines & Uncertainty Methods    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Tooling & MLOps Layer                  │
│  - MLflow, DVC, Model/Dataset Cards     │
└─────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for containerized deployment)
- Git
- Makerkit license and installation (for frontend integration)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd RadiKal/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Docker Deployment

```bash
docker build -t xai-qc-backend .
docker run -p 8000:8000 xai-qc-backend
```

Or use Docker Compose for the full stack:
```bash
cd ..
docker-compose up
```

## Running the Service

### Development Mode

```bash
uvicorn api.routes:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn api.routes:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Core Endpoints

#### POST /api/xai-qc/detect
Upload an image for defect detection and segmentation.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/xai-qc/detect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.jpg"
```

#### POST /api/xai-qc/explain
Generate XAI explanations for a detected image.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_id": "abc123", "methods": ["gradcam", "shap", "lime", "ig"]}'
```

#### GET /api/xai-qc/metrics
Retrieve performance metrics for a date range.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/xai-qc/metrics?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### POST /api/xai-qc/export
Generate and download a PDF/Excel report.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/xai-qc/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format": "pdf", "start_date": "2025-01-01", "end_date": "2025-01-31"}'
```

#### GET /api/xai-qc/calibration
Get current model calibration status and ECE.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/xai-qc/calibration" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### GET /api/xai-qc/health
Health check endpoint.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/xai-qc/health"
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=core --cov=api --cov-report=html
```

### Run Specific Test Modules

```bash
pytest tests/test_xai.py -v
pytest tests/test_api.py -v
```

## MLOps

### MLflow Tracking

Start MLflow UI:
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Access at http://localhost:5000

### DVC Pipeline

Initialize DVC:
```bash
dvc init
```

Run the pipeline:
```bash
dvc repro
```

## Project Structure

```
backend/
├── api/                    # FastAPI routes, schemas, middleware
├── core/                   # Core ML logic
│   ├── models/            # Detection/segmentation models
│   ├── xai/               # XAI implementations
│   ├── uncertainty/       # Uncertainty quantification
│   ├── preprocessing/     # Image preprocessing
│   └── metrics/           # Metrics calculation
├── data/                   # Dataset storage
├── models/                 # Model checkpoints
├── tests/                  # Unit and integration tests
├── configs/                # Configuration files
├── scripts/                # Training and utility scripts
├── exports/                # Generated reports
├── CHANGELOG.md            # Change log
├── DEVELOPMENT_REGISTER.json  # Machine-readable log
├── module.yaml             # Module configuration
├── requirements.txt        # Python dependencies
└── Dockerfile              # Container definition
```

## Authentication

This backend is designed to integrate with Makerkit's authentication system. All protected endpoints require a valid JWT token:

```bash
Authorization: Bearer <makerkit-jwt-token>
```

Supported roles:
- `operator`: Can view detections and explanations
- `admin`: Full access including metrics and exports

## Configuration

Key configuration files:
- `module.yaml`: Module metadata and feature flags
- `configs/`: Environment-specific configurations
- `.env`: Environment variables (not committed to version control)

## Performance Benchmarks

- **Inference Latency**: <200ms per image on standard CPU
- **Test Coverage**: >90% for core and API modules
- **API Response Time**: <500ms for most endpoints

## Contributing

Please refer to CHANGELOG.md and update DEVELOPMENT_REGISTER.json before every commit.

### Commit Message Format

```
<type>(<scope>): <description>

Examples:
feat(api): add explain endpoint
fix(xai): correct gradcam heatmap normalization
docs(readme): update API examples
```

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on the repository or contact the development team.
