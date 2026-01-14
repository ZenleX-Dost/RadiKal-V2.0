# API Reference

Complete API documentation for RadiKal V2.0 backend.

## Base URL

```
http://localhost:8000
```

For production, replace with your domain:
```
https://api.yourdomain.com
```

## Authentication

Currently, the API uses optional JWT authentication. For production deployments, enable authentication:

```http
Authorization: Bearer <your_jwt_token>
```

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/xai-qc/detect` | POST | Detect defects in uploaded image |
| `/api/xai-qc/explain` | POST | Generate XAI explanations |
| `/api/xai-qc/analyze-hybrid` | POST | Hybrid YOLOv8 + SAM2 analysis |
| `/api/xai-qc/batch` | POST | Process multiple images |
| `/api/xai-qc/metrics` | GET | Retrieve performance metrics |
| `/api/xai-qc/history` | GET | Get analysis history |
| `/api/xai-qc/export` | POST | Export results (PDF/Excel) |

---

## 1. Detect Defects

Classify defect type using YOLOv8.

### Endpoint

```http
POST /api/xai-qc/detect
```

### Request

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (required): Image file (PNG, JPG, JPEG)
- `return_probabilities` (optional): Include class probabilities (default: true)

### Example

```bash
curl -X POST "http://localhost:8000/api/xai-qc/detect?return_probabilities=true" \
  -F "file=@weld_image.png"
```

### Response

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "predicted_class": 0,
  "predicted_class_name": "LP",
  "predicted_class_full_name": "Lack of Penetration",
  "confidence": 0.95,
  "all_probabilities": {
    "LP": 0.95,
    "PO": 0.03,
    "CR": 0.01,
    "ND": 0.01
  },
  "is_defect": true,
  "defect_type": "LP",
  "timestamp": "2026-01-14T14:25:00Z"
}
```

---

## 2. Generate XAI Explanations

Generate explainability visualizations for a defect classification.

### Endpoint

```http
POST /api/xai-qc/explain
```

### Request

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (required): Image file
- `methods` (optional): Comma-separated XAI methods (default: "gradcam,shap,lime,ig")
  - `gradcam`: Gradient-weighted Class Activation Mapping
  - `shap`: SHapley Additive exPlanations
  - `lime`: Local Interpretable Model-agnostic Explanations
  - `ig`: Integrated Gradients
- `target_class` (optional): Target class index for explanation

### Example

```bash
curl -X POST "http://localhost:8000/api/xai-qc/explain?methods=gradcam,shap" \
  -F "file=@weld_image.png"
```

### Response

```json
{
  "image_id": "550e8400-e29b-41d4-a716-446655440000",
  "classification": {
    "predicted_class": 0,
    "predicted_class_name": "LP",
    "confidence": 0.95
  },
  "explanations": [
    {
      "method": "gradcam",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.92,
      "computation_time_ms": 150
    },
    {
      "method": "shap",
      "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "confidence_score": 0.88,
      "computation_time_ms": 850
    }
  ],
  "aggregated_heatmap": "iVBORw0KGgoAAAANSUhEUgAA...",
  "consensus_score": 0.90,
  "timestamp": "2026-01-14T14:25:00Z"
}
```

---

## 3. Hybrid Analysis (YOLOv8 + SAM2)

Perform combined classification and segmentation analysis.

### Endpoint

```http
POST /api/xai-qc/analyze-hybrid
```

### Request

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (required): Image file
- `mode` (optional): Analysis mode (default: "hybrid")
  - `classification`: YOLOv8 only
  - `segmentation`: SAM2 only
  - `hybrid`: Both models
- `segmentation_guidance` (optional): Guidance strategy (default: "auto")
  - `auto`: Automatic based on classification
  - `center`: Use center point
  - `grid`: Grid-based segmentation
- `return_visualization` (optional): Include visualization overlays (default: true)
- `methods` (optional): XAI methods to include

### Example

```bash
curl -X POST "http://localhost:8000/api/xai-qc/analyze-hybrid?mode=hybrid&segmentation_guidance=auto" \
  -F "file=@weld_image.png"
```

### Response

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "hybrid",
  "classification": {
    "predicted_class": 0,
    "predicted_class_name": "LP",
    "predicted_class_full_name": "Lack of Penetration",
    "confidence": 0.95,
    "all_probabilities": {
      "LP": 0.95,
      "PO": 0.03,
      "CR": 0.01,
      "ND": 0.01
    },
    "is_defect": true
  },
  "segmentation": {
    "has_segmentation": true,
    "num_segments": 1,
    "segments": [
      {
        "id": 0,
        "area": 3200,
        "bbox": [120, 80, 200, 150],
        "centroid": [220.5, 155.3],
        "coverage_percent": 7.32
      }
    ],
    "total_coverage_percent": 7.32,
    "masks_base64": ["iVBORw0KGgoAAAANSUhEUgAA..."]
  },
  "visualization": {
    "overlay_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "heatmap_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
  },
  "metadata": {
    "image_size": [640, 640],
    "sam2_model": "small",
    "segmentation_guidance": "auto",
    "processing_time_ms": 2250
  },
  "timestamp": "2026-01-14T14:25:00Z"
}
```

---

## 4. Batch Processing

Process multiple images concurrently.

### Endpoint

```http
POST /api/xai-qc/batch
```

### Request

**Content-Type**: `multipart/form-data`

**Parameters**:
- `files` (required): Multiple image files
- `mode` (optional): Analysis mode (default: "hybrid")
- `methods` (optional): XAI methods
- `concurrent_limit` (optional): Max concurrent processes (default: 3)

### Example

```bash
curl -X POST "http://localhost:8000/api/xai-qc/batch?mode=hybrid" \
  -F "files=@image1.png" \
  -F "files=@image2.png" \
  -F "files=@image3.png"
```

### Response

```json
{
  "batch_id": "batch_550e8400-e29b-41d4-a716-446655440000",
  "total_images": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "image_name": "image1.png",
      "status": "success",
      "analysis_id": "550e8400-e29b-41d4-a716-446655440001",
      "classification": {...},
      "segmentation": {...}
    },
    {
      "image_name": "image2.png",
      "status": "success",
      "analysis_id": "550e8400-e29b-41d4-a716-446655440002",
      "classification": {...},
      "segmentation": {...}
    },
    {
      "image_name": "image3.png",
      "status": "success",
      "analysis_id": "550e8400-e29b-41d4-a716-446655440003",
      "classification": {...},
      "segmentation": {...}
    }
  ],
  "processing_time_ms": 5430,
  "timestamp": "2026-01-14T14:25:00Z"
}
```

---

## 5. Get Metrics

Retrieve system and model performance metrics.

### Endpoint

```http
GET /api/xai-qc/metrics
```

### Query Parameters

- `timeframe` (optional): Time period (default: "24h")
  - `1h`, `24h`, `7d`, `30d`, `all`

### Example

```bash
curl -X GET "http://localhost:8000/api/xai-qc/metrics?timeframe=24h"
```

### Response

```json
{
  "timeframe": "24h",
  "total_analyses": 1523,
  "classification_metrics": {
    "accuracy": 0.94,
    "precision": 0.93,
    "recall": 0.92,
    "f1_score": 0.925,
    "class_distribution": {
      "LP": 456,
      "PO": 389,
      "CR": 234,
      "ND": 444
    }
  },
  "segmentation_metrics": {
    "average_coverage": 8.5,
    "average_segments": 1.2,
    "success_rate": 0.98
  },
  "performance_metrics": {
    "avg_processing_time_ms": 2340,
    "p50_processing_time_ms": 2150,
    "p95_processing_time_ms": 3200,
    "p99_processing_time_ms": 4100
  },
  "system_metrics": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 62.8,
    "gpu_usage_percent": 78.5,
    "disk_usage_percent": 34.1
  },
  "timestamp": "2026-01-14T14:25:00Z"
}
```

---

## 6. Get Analysis History

Retrieve historical analysis results.

### Endpoint

```http
GET /api/xai-qc/history
```

### Query Parameters

- `limit` (optional): Number of results (default: 50, max: 500)
- `offset` (optional): Pagination offset (default: 0)
- `class_filter` (optional): Filter by defect class
- `start_date` (optional): Start date (ISO 8601)
- `end_date` (optional): End date (ISO 8601)

### Example

```bash
curl -X GET "http://localhost:8000/api/xai-qc/history?limit=10&class_filter=LP"
```

### Response

```json
{
  "total_count": 456,
  "limit": 10,
  "offset": 0,
  "results": [
    {
      "analysis_id": "550e8400-e29b-41d4-a716-446655440001",
      "timestamp": "2026-01-14T14:20:00Z",
      "classification": {
        "predicted_class_name": "LP",
        "confidence": 0.95
      },
      "segmentation_summary": {
        "has_segmentation": true,
        "coverage_percent": 7.32
      },
      "image_metadata": {
        "size": [640, 640],
        "format": "PNG"
      }
    }
  ]
}
```

---

## 7. Export Results

Export analysis results to PDF or Excel.

### Endpoint

```http
POST /api/xai-qc/export
```

### Request

**Content-Type**: `application/json`

**Body**:
```json
{
  "analysis_ids": ["id1", "id2", "id3"],
  "format": "pdf",
  "include_images": true,
  "include_xai": true,
  "include_metadata": true,
  "include_summary": true
}
```

### Parameters

- `analysis_ids` (required): List of analysis IDs to export
- `format` (required): Export format (`pdf` or `excel`)
- `include_images` (optional): Include original images (default: true)
- `include_xai` (optional): Include XAI visualizations (default: true)
- `include_metadata` (optional): Include metadata (default: true)
- `include_summary` (optional): Include summary statistics (default: true)

### Example

```bash
curl -X POST "http://localhost:8000/api/xai-qc/export" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_ids": ["550e8400-e29b-41d4-a716-446655440001"],
    "format": "pdf",
    "include_images": true,
    "include_xai": true
  }' \
  --output report.pdf
```

### Response

Binary file (PDF or Excel) with the following naming:
```
radikal_export_{timestamp}.pdf
radikal_export_{timestamp}.xlsx
```

---

## Health Endpoints

### Basic Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T14:25:00Z"
}
```

### Detailed Health Check

```http
GET  /health/detailed
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T14:25:00Z",
  "version": "2.0.0",
  "components": {
    "database": "healthy",
    "yolo_model": "loaded",
    "sam2_model": "loaded",
    "gpu": "available"
  },
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "gpu_usage": 78.5,
    "gpu_memory": "4.2GB / 6GB"
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "error": "Invalid request",
  "message": "File format not supported. Please upload PNG, JPG, or JPEG.",
  "code": "INVALID_FILE_FORMAT"
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token",
  "code": "AUTH_REQUIRED"
}
```

### 404 Not Found

```json
{
  "error": "Not found",
  "message": "Analysis ID not found",
  "code": "ANALYSIS_NOT_FOUND"
}
```

### 413 Payload Too Large

```json
{
  "error": "Payload too large",
  "message": "File size exceeds 10MB limit",
  "code": "FILE_TOO_LARGE"
}
```

### 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again in 60 seconds.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred",
  "code": "INTERNAL_ERROR"
}
```

---

## Rate Limiting

The API implements rate limiting:

- **Default**: 100 requests per minute per IP
- **Batch processing**: 10 requests per minute per IP
- **Export**: 5 requests per minute per IP

Response headers include:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1610636400
```

---

## WebSocket Support (Planned)

Future versions will support WebSocket connections for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Analysis update:', update);
};
```

---

## SDK and Client Libraries

Official client libraries:

- **Python**: `pip install radikal-client`
- **JavaScript/TypeScript**: `npm install @radikal/client`
- **cURL examples**: See above for each endpoint

---

## Interactive API Documentation

Visit the following URLs when the backend is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## API Versioning

Current version: **v1**

The API version is included in the path:
```
/api/xai-qc/*  (v1, current)
```

Future versions will be accessible via:
```
/api/v2/xai-qc/*  (planned)
```

---

## Support

For API issues or questions:

- Review the [Troubleshooting Guide](troubleshooting.md)
- Check the interactive API docs at `/docs`
- Open an issue on GitHub
- Contact support: support@yourdomain.com
