# Testing Guide

Comprehensive testing guide for RadiKal V2.0.

## Overview

RadiKal V2.0 includes a comprehensive test suite with >90% code coverage.

## Test Structure

```
backend/tests/
├── test_api/              # API endpoint tests
├── test_models/           # Model tests
├── test_xai/              # XAI method tests
├── test_preprocessing/    # Image processing tests
└── conftest.py           # Pytest fixtures
```

---

## Running Tests

### Prerequisites

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=core --cov=api --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Run Specific Test Categories

```bash
# API tests only
pytest tests/test_api/ -v

# Model tests only
pytest tests/test_models/ -v

# XAI tests only
pytest tests/test_xai/ -v
```

---

## Test Categories

### 1. API Tests

Test all API endpoints:

```bash
pytest tests/test_api/test_routes.py -v
```

**Coverage**:
- Detection endpoint
- Explanation endpoint
- Hybrid analysis endpoint
- Batch processing endpoint
- Metrics endpoint
- History endpoint
- Export endpoint

### 2. Model Tests

Test ML model functionality:

```bash
pytest tests/test_models/ -v
```

**Tests**:
- YOLOv8 initialization
- Classification accuracy
- SAM2 initialization
- Segmentation quality
- Hybrid analyzer
- Model loading/unloading

### 3. XAI Tests

Test explainability methods:

```bash
pytest tests/test_xai/ -v
```

**Methods tested**:
- Grad-CAM
- SHAP
- LIME
- Integrated Gradients
- Consensus scoring

### 4. Integration Tests

Test end-to-end workflows:

```bash
pytest tests/test_integration.py -v
```

---

## SAM2 Integration Tests

Special test suite for SAM2:

```bash
cd backend
python test_sam2_integration.py
```

**Test Coverage**:
1. SAM2 import verification
2. YOLOv8 classifier functionality
3. SAM2 segmenter functionality
4. Hybrid analyzer integration
5. Real image analysis

Expected output:
```
Test 1: SAM2 Import - PASSED
Test 2: YOLOv8 Classifier - PASSED
Test 3: SAM2 Segmenter - PASSED
Test 4: Hybrid Analyzer - PASSED
Test 5: Real Image Analysis - PASSED
```

---

## Load Testing

### Using Locust

Install Locust:
```bash
pip install locust
```

Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class RadiKalUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def analyze_image(self):
        with open('test_image.png', 'rb') as f:
            self.client.post('/api/xai-qc/detect', 
                           files={'file': f})
```

Run load test:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

Access web UI: http://localhost:8089

**Test Scenarios**:
- 100 concurrent users
- 1000 requests/minute
- Sustained load for 10 minutes

---

## Performance Testing

### Inference Speed Test

```python
import time
import numpy as np
from core.models.hybrid_defect_analyzer import HybridDefectAnalyzer

analyzer = HybridDefectAnalyzer()
image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

# Warmup
for _ in range(10):
    analyzer.analyze(image, mode='classification')

# Benchmark
times = []
for _ in range(100):
    start = time.time()
    analyzer.analyze(image, mode='classification')
    times.append(time.time() - start)

print(f"Average: {np.mean(times)*1000:.2f}ms")
print(f"P95: {np.percentile(times, 95)*1000:.2f}ms")
print(f"P99: {np.percentile(times, 99)*1000:.2f}ms")
```

### Expected Performance

**Classification Mode (YOLOv8)**:
- Average: ~50ms
- P95: ~80ms
- P99: ~100ms

**Hybrid Mode (YOLOv8 + SAM2 Small)**:
- Average: ~2.3s
- P95: ~3.5s
- P99: ~4.5s

---

## Manual Testing Checklist

### Frontend Testing

- [ ] Image upload works
- [ ] All analysis modes function
- [ ] Results display correctly
- [ ] XAI visualizations render
- [ ] Batch processing works
- [ ] Export functionality works
- [ ] Settings save correctly
- [ ] Notifications appear
- [ ] Mobile responsive

### Backend Testing

- [ ] All endpoints respond
- [ ] Authentication works
- [ ] Rate limiting enforced
- [ ] Error handling correct
- [ ] File validation works
- [ ] Database operations succeed
- [ ] Logging captures events
- [ ] Health checks pass

### Integration Testing

- [ ] Frontend-backend communication
- [ ] Database connectivity
- [ ] GPU utilization
- [ ] Model loading
- [ ] File uploads/downloads
- [ ] Real-time updates (SSE)
- [ ] Export generation

---

## Continuous Integration

### GitHub Actions Workflow

```.yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ --cov=core --cov=api
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Test Data

### Sample Images

Located in `backend/test_data/`:
- `lp_sample.png` - Lack of Penetration defect
- `po_sample.png` - Porosity defect
- `cr_sample.png` - Crack defect
- `nd_sample.png` - No Defect

### Test Database

Use separate test database:
```env
# backend/.env.test
DATABASE_URL=postgresql://user:pass@localhost:5432/radikal_test
```

---

## Writing New Tests

### Test Template

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_example():
    """Test description"""
    # Arrange
    test_data = {...}
    
    # Act
    response = client.post('/endpoint', json=test_data)
    
    # Assert
    assert response.status_code == 200
    assert 'expected_key' in response.json()
```

### Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def sample_image():
    """Provide sample test image"""
    from PIL import Image
    import numpy as np
    img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    return Image.fromarray(img)

@pytest.fixture
def test_client():
    """Provide test client"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
```

---

## Troubleshooting Tests

### Tests Failing

```bash
# Run with verbose output
pytest tests/ -v -s

# Run single test
pytest tests/test_api/test_routes.py::test_detect -v

# Show print statements
pytest tests/ -v -s --capture=no
```

### CUDA Errors in Tests

```python
# Set CPU-only mode for testing
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

### Database Errors

```bash
# Reset test database
psql -U postgres -c "DROP DATABASE radikal_test;"
psql -U postgres -c "CREATE DATABASE radikal_test;"
```

---

## Coverage Goals

Target coverage by module:

- API routes: >95%
- Models: >90%
- XAI methods: >85%
- Preprocessing: >90%
- Utilities: >80%
- Overall: >90%

---

## Best Practices

1. **Write tests first** (TDD approach)
2. **Test one thing** per test function
3. **Use descriptive names** for test functions
4. **Mock external dependencies** (API calls, database)
5. **Clean up after tests** (fixtures,teardown)
6. **Don't test framework code**
7. **Keep tests fast** (<1s per test)
8. **Use parametrize** for similar tests

---

## Resources

- Pytest documentation: https://docs.pytest.org
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Coverage.py: https://coverage.readthedocs.io
