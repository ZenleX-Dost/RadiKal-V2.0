# API Testing Guide

Complete guide for testing the RadiKal XAI Quality Control API endpoints.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Testing Each Endpoint](#testing-each-endpoint)
4. [Automated Testing](#automated-testing)
5. [Load Testing](#load-testing)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Start the API Server

```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the server
python main.py
```

Server will start at: **http://localhost:8000**

### Access API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Authentication

All endpoints (except `/health`) require authentication using Makerkit JWT tokens.

### Get a Token (Mock for Testing)

```python
# For testing purposes only
# In production, get this from Makerkit
mock_token = "test_jwt_token_replace_with_real_makerkit_token"
headers = {"Authorization": f"Bearer {mock_token}"}
```

### Using curl

```bash
export TOKEN="your_makerkit_jwt_token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/xai-qc/health
```

---

## Testing Each Endpoint

### 1. Health Check (No Auth Required)

**Endpoint**: `GET /api/xai-qc/health`

#### Using curl:
```bash
curl -X GET http://localhost:8000/api/xai-qc/health
```

#### Using Python:
```python
import requests

response = requests.get("http://localhost:8000/api/xai-qc/health")
print(response.json())
```

#### Expected Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-14T12:00:00",
  "model_loaded": true,
  "device": "cuda",
  "version": "1.0.0"
}
```

---

### 2. Detect Defects

**Endpoint**: `POST /api/xai-qc/detect`

#### Using curl:
```bash
curl -X POST http://localhost:8000/api/xai-qc/detect \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_image.jpg"
```

#### Using Python:
```python
import requests

url = "http://localhost:8000/api/xai-qc/detect"
headers = {"Authorization": f"Bearer {token}"}

with open("test_image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers=headers, files=files)

result = response.json()
print(f"Found {result['num_detections']} defects")
for detection in result['detections']:
    print(f"  - {detection['class_name']}: {detection['confidence']:.2f}")
```

#### Expected Response:
```json
{
  "image_id": "img_1697289600.123",
  "timestamp": "2025-10-14T12:00:00",
  "detections": [
    {
      "detection_id": "det_1697289600_0",
      "bbox": [100, 100, 200, 200],
      "confidence": 0.95,
      "class_name": "defect",
      "severity": "high",
      "mask_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ],
  "num_detections": 1,
  "mean_uncertainty": 0.042,
  "processed_by": "user_123"
}
```

---

### 3. Generate Explanations

**Endpoint**: `POST /api/xai-qc/explain`

#### Using Python:
```python
import requests
import base64

url = "http://localhost:8000/api/xai-qc/explain"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Read and encode image
with open("test_image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "image_id": "img_1697289600.123",
    "detection_id": "det_1697289600_0",
    "image_base64": image_base64,
    "target_class": 1
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print(f"Consensus Score: {result['consensus_score']:.3f}")
for explanation in result['explanations']:
    print(f"  - {explanation['method']}: {explanation['confidence_score']:.3f}")
```

#### Expected Response:
```json
{
  "image_id": "img_1697289600.123",
  "detection_id": "det_1697289600_0",
  "explanations": [
    {
      "method": "gradcam",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.87
    },
    {
      "method": "shap",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.82
    },
    {
      "method": "lime",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.79
    },
    {
      "method": "integrated_gradients",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.85
    },
    {
      "method": "aggregated",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.84
    }
  ],
  "consensus_score": 0.856,
  "timestamp": "2025-10-14T12:01:00"
}
```

---

### 4. Get Metrics

**Endpoint**: `GET /api/xai-qc/metrics`

#### Using curl:
```bash
curl -X GET "http://localhost:8000/api/xai-qc/metrics?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

#### Using Python:
```python
import requests
from datetime import datetime, timedelta

url = "http://localhost:8000/api/xai-qc/metrics"
headers = {"Authorization": f"Bearer {token}"}

params = {
    "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
    "end_date": datetime.now().isoformat()
}

response = requests.get(url, headers=headers, params=params)
metrics = response.json()

print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print(f"F1 Score: {metrics['f1_score']:.3f}")
print(f"mAP@0.5: {metrics['map_at_50']:.3f}")
```

#### Expected Response:
```json
{
  "start_date": "2025-09-14T00:00:00",
  "end_date": "2025-10-14T00:00:00",
  "false_negatives": 12,
  "false_positives": 8,
  "true_positives": 185,
  "true_negatives": 795,
  "precision": 0.958,
  "recall": 0.939,
  "f1_score": 0.948,
  "map_at_50": 0.872,
  "auroc": 0.945,
  "mean_iou": 0.783,
  "mean_dice_score": 0.856,
  "mean_ece": 0.042,
  "total_images_processed": 1000
}
```

---

### 5. Export Report

**Endpoint**: `POST /api/xai-qc/export`

#### Using Python:
```python
import requests

url = "http://localhost:8000/api/xai-qc/export"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "image_ids": ["img_001", "img_002", "img_003"],
    "format": "pdf"  # or "excel"
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print(f"Report generated: {result['download_url']}")

# Download the report
download_url = f"http://localhost:8000{result['download_url']}"
report = requests.get(download_url, headers=headers)

with open("report.pdf", "wb") as f:
    f.write(report.content)

print("Report downloaded!")
```

---

### 6. Get Calibration Status

**Endpoint**: `GET /api/xai-qc/calibration`

#### Using curl:
```bash
curl -X GET http://localhost:8000/api/xai-qc/calibration \
  -H "Authorization: Bearer $TOKEN"
```

#### Using Python:
```python
import requests

url = "http://localhost:8000/api/xai-qc/calibration"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
calibration = response.json()

print(f"ECE: {calibration['ece']:.4f}")
print(f"Temperature: {calibration['temperature']:.2f}")
print(f"Calibrated: {calibration['is_calibrated']}")
```

---

## Automated Testing

### Run Unit Tests

```powershell
cd backend
pytest tests/ -v
```

### Run Integration Tests

```powershell
pytest tests/test_api_integration.py -v
```

### Run with Coverage

```powershell
pytest tests/ --cov=core --cov=api --cov-report=html
start htmlcov/index.html
```

### Run Specific Test

```powershell
pytest tests/test_api_integration.py::TestDetectionEndpoint::test_detect_with_mock_auth -v
```

---

## Load Testing

### Using Apache Bench

```bash
# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/api/xai-qc/health

# Test with authentication
ab -n 100 -c 5 -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/xai-qc/metrics
```

### Using Locust

Create `locustfile.py`:

```python
from locust import HttpUser, task, between

class RadiKalUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.token = "your_test_token"
    
    @task(3)
    def health_check(self):
        self.client.get("/api/xai-qc/health")
    
    @task(1)
    def get_metrics(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/xai-qc/metrics", headers=headers)
```

Run:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused
**Error**: `Connection refused`
**Solution**: Make sure server is running: `python main.py`

#### 2. 401 Unauthorized
**Error**: `{"detail":"Not authenticated"}`
**Solution**: Provide valid JWT token in Authorization header

#### 3. 422 Validation Error
**Error**: `{"detail":[{"loc":["body","image_base64"],"msg":"field required"}]}`
**Solution**: Check request payload matches schema in `/api/docs`

#### 4. 500 Internal Server Error
**Error**: `{"detail":"Detection failed: ..."}` 
**Solution**: Check server logs for detailed error message

#### 5. Model Not Found
**Error**: `Model weights not found`
**Solution**: Train model first: `python scripts/train.py`

### Check Logs

```powershell
# View server logs
tail -f logs/api.log

# Or if running with uvicorn directly
# Logs appear in console
```

### Debug Mode

```python
# In main.py, enable debug mode
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
```

---

## Performance Benchmarks

### Expected Latencies (GPU - RTX 4050)

- **Health Check**: <10ms
- **Detection**: 150-200ms per image
- **Explanation (single method)**: 300-500ms
- **Explanation (all 4 methods)**: 1-2 seconds
- **Metrics Retrieval**: <50ms
- **Export Generation**: 500ms-2s

### Expected Throughput

- **Detection**: 5-10 images/second
- **Explanations**: 1-2 images/second (all methods)

---

## Best Practices

1. **Always use HTTPS in production**
2. **Implement rate limiting** to prevent abuse
3. **Cache frequently accessed data** (Redis)
4. **Use async/await** for I/O operations
5. **Monitor API performance** with APM tools
6. **Log all requests** for audit trail
7. **Validate input sizes** to prevent DoS
8. **Use connection pooling** for database
9. **Implement circuit breakers** for external services
10. **Test with realistic data** before production

---

**Last Updated**: October 14, 2025  
**API Version**: 1.0.0
