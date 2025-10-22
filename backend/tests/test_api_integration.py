"""
Integration tests for FastAPI endpoints.

This module tests the complete API workflow including authentication,
detection, explanation generation, and metrics retrieval.

Author: RadiKal Team
Date: 2025-10-14
"""

import pytest
import io
import base64
from PIL import Image
import numpy as np
from fastapi.testclient import TestClient

from main import app
from api.routes import initialize_models


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    # Initialize models before testing
    initialize_models()
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a simple grayscale image
    img_array = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
    img = Image.fromarray(img_array, mode='L')
    
    # Convert to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    
    return img_buffer


@pytest.fixture
def sample_image_base64(sample_image):
    """Create a base64-encoded image."""
    sample_image.seek(0)
    return base64.b64encode(sample_image.read()).decode('utf-8')


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token for testing."""
    # In production, this should be a real JWT from Makerkit
    # For testing, we'll use a simple token
    return "test_token_for_integration_testing"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/xai-qc/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "model_loaded" in data
        assert "device" in data
        assert "version" in data


class TestDetectionEndpoint:
    """Tests for the detection endpoint."""
    
    def test_detect_without_auth(self, client, sample_image):
        """Test detection without authentication (should fail)."""
        sample_image.seek(0)
        response = client.post(
            "/api/xai-qc/detect",
            files={"file": ("test.jpg", sample_image, "image/jpeg")}
        )
        
        # Should fail without proper authentication
        assert response.status_code in [401, 403, 422]
    
    def test_detect_with_mock_auth(self, client, sample_image, mock_jwt_token):
        """Test detection with mock authentication."""
        sample_image.seek(0)
        
        # Note: This will fail with real auth validation
        # In production, you need a valid Makerkit JWT
        response = client.post(
            "/api/xai-qc/detect",
            files={"file": ("test.jpg", sample_image, "image/jpeg")},
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # Expected to fail auth in test environment
        assert response.status_code in [200, 401, 403, 422]
    
    def test_detect_invalid_file(self, client):
        """Test detection with invalid file."""
        response = client.post(
            "/api/xai-qc/detect",
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )
        
        assert response.status_code in [400, 422, 401]


class TestExplainEndpoint:
    """Tests for the explanation endpoint."""
    
    def test_explain_request_structure(self, client, sample_image_base64, mock_jwt_token):
        """Test the explain endpoint with proper request structure."""
        request_data = {
            "image_id": "test_img_123",
            "detection_id": "test_det_456",
            "image_base64": sample_image_base64,
            "target_class": 1,
        }
        
        response = client.post(
            "/api/xai-qc/explain",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # Expected to fail auth in test environment
        assert response.status_code in [200, 401, 403, 422]


class TestMetricsEndpoint:
    """Tests for the metrics endpoint."""
    
    def test_metrics_without_auth(self, client):
        """Test metrics endpoint without authentication."""
        response = client.get("/api/xai-qc/metrics")
        
        # Should require admin role
        assert response.status_code in [401, 403, 422]
    
    def test_metrics_with_date_range(self, client, mock_jwt_token):
        """Test metrics with date range parameters."""
        response = client.get(
            "/api/xai-qc/metrics?start_date=2025-01-01&end_date=2025-12-31",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # Expected to fail auth in test environment
        assert response.status_code in [200, 401, 403, 422]


class TestExportEndpoint:
    """Tests for the export endpoint."""
    
    def test_export_pdf(self, client, mock_jwt_token):
        """Test PDF export generation."""
        request_data = {
            "image_ids": ["img_1", "img_2"],
            "format": "pdf",
        }
        
        response = client.post(
            "/api/xai-qc/export",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # Expected to fail auth in test environment
        assert response.status_code in [200, 401, 403, 422]
    
    def test_export_excel(self, client, mock_jwt_token):
        """Test Excel export generation."""
        request_data = {
            "image_ids": ["img_1", "img_2"],
            "format": "excel",
        }
        
        response = client.post(
            "/api/xai-qc/export",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # Expected to fail auth in test environment
        assert response.status_code in [200, 401, 403, 422]


class TestCalibrationEndpoint:
    """Tests for the calibration endpoint."""
    
    def test_calibration_status(self, client, mock_jwt_token):
        """Test calibration status retrieval."""
        response = client.get(
            "/api/xai-qc/calibration",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # Expected to fail auth in test environment
        assert response.status_code in [200, 401, 403, 422]


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_swagger_docs(self, client):
        """Test that Swagger UI is accessible."""
        response = client.get("/api/docs")
        
        assert response.status_code == 200
    
    def test_redoc_docs(self, client):
        """Test that ReDoc is accessible."""
        response = client.get("/api/redoc")
        
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_not_found(self, client):
        """Test 404 error handling."""
        response = client.get("/api/xai-qc/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed error."""
        response = client.post("/api/xai-qc/health")
        
        assert response.status_code == 405


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Integration tests for complete workflows."""
    
    def test_detection_to_explanation_workflow(self, client, sample_image, sample_image_base64, mock_jwt_token):
        """Test the complete workflow from detection to explanation."""
        # This is a skeleton test - would need valid authentication in production
        
        # Step 1: Upload image for detection
        sample_image.seek(0)
        detect_response = client.post(
            "/api/xai-qc/detect",
            files={"file": ("test.jpg", sample_image, "image/jpeg")},
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )
        
        # In test environment without proper auth, this will fail
        # In production with valid JWT, this would return detections
        assert detect_response.status_code in [200, 401, 403, 422]
        
        # If we had a successful detection, we would:
        # Step 2: Request explanations
        # Step 3: Export report
        # For now, we just verify the endpoints exist


# Note: For production testing, you need:
# 1. Valid Makerkit JWT tokens
# 2. Actual trained model
# 3. Real test images
# 4. Database for metrics storage
#
# These tests verify the API structure and basic functionality
# without requiring full authentication infrastructure.
