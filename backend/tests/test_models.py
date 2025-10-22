"""Unit tests for detection models."""

import pytest
import numpy as np
import torch
from core.models.detector import DefectDetector, BaseDetector


class TestDefectDetector:
    """Test suite for DefectDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a DefectDetector instance."""
        return DefectDetector(num_classes=2, device='cpu')
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample RGB image."""
        return np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    
    def test_initialization(self):
        """Test DefectDetector initialization."""
        detector = DefectDetector(num_classes=3, device='cpu')
        assert detector.num_classes == 3
        assert detector.device.type == 'cpu'
        assert detector.model is not None
    
    def test_initialization_auto_device(self):
        """Test DefectDetector initialization with auto device selection."""
        detector = DefectDetector(num_classes=2)
        assert detector.device.type in ['cpu', 'cuda']
    
    def test_build_model(self, detector):
        """Test model building."""
        model = detector._build_model()
        assert model is not None
        assert hasattr(model, 'roi_heads')
    
    def test_preprocess_image_uint8(self, detector, sample_image):
        """Test image preprocessing with uint8 input."""
        tensor = detector.preprocess_image(sample_image)
        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape[0] == 3
        assert tensor.dtype == torch.float32
        assert tensor.max() <= 1.0
        assert tensor.min() >= 0.0
    
    def test_preprocess_image_float(self, detector):
        """Test image preprocessing with float input."""
        image = np.random.rand(512, 512, 3).astype(np.float32)
        tensor = detector.preprocess_image(image)
        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape[0] == 3
    
    def test_preprocess_image_grayscale(self, detector):
        """Test image preprocessing with grayscale input."""
        image = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
        tensor = detector.preprocess_image(image)
        assert tensor.shape[0] == 3
    
    def test_detect(self, detector, sample_image):
        """Test defect detection."""
        result = detector.detect(sample_image, confidence_threshold=0.5)
        
        assert isinstance(result, dict)
        assert 'boxes' in result
        assert 'scores' in result
        assert 'labels' in result
        assert isinstance(result['boxes'], list)
        assert isinstance(result['scores'], list)
        assert isinstance(result['labels'], list)
    
    def test_detect_with_different_threshold(self, detector, sample_image):
        """Test detection with different confidence thresholds."""
        result_high = detector.detect(sample_image, confidence_threshold=0.9)
        result_low = detector.detect(sample_image, confidence_threshold=0.1)
        
        assert len(result_low['boxes']) >= len(result_high['boxes'])
    
    def test_segment(self, detector, sample_image):
        """Test defect segmentation."""
        result = detector.segment(sample_image, confidence_threshold=0.5)
        
        assert isinstance(result, dict)
        assert 'masks' in result
        assert 'boxes' in result
        assert 'scores' in result
        assert 'labels' in result
        assert isinstance(result['masks'], list)
    
    def test_segment_mask_shape(self, detector, sample_image):
        """Test that segmentation masks have correct shape."""
        result = detector.segment(sample_image, confidence_threshold=0.5)
        
        if len(result['masks']) > 0:
            mask = result['masks'][0]
            assert mask.shape == sample_image.shape[:2]
            assert mask.dtype == np.uint8
            assert np.all((mask == 0) | (mask == 1))
    
    def test_get_feature_maps(self, detector, sample_image):
        """Test feature map extraction."""
        features = detector.get_feature_maps(sample_image)
        assert isinstance(features, torch.Tensor)
        assert len(features.shape) == 4
    
    def test_detect_batch_consistency(self, detector, sample_image):
        """Test that detection produces consistent results."""
        result1 = detector.detect(sample_image)
        result2 = detector.detect(sample_image)
        
        assert len(result1['boxes']) == len(result2['boxes'])
        if len(result1['boxes']) > 0:
            assert np.allclose(result1['boxes'], result2['boxes'], rtol=1e-5)
    
    def test_base_detector_interface(self):
        """Test that DefectDetector implements BaseDetector interface."""
        assert issubclass(DefectDetector, BaseDetector)
        detector = DefectDetector(num_classes=2, device='cpu')
        assert hasattr(detector, 'detect')
        assert hasattr(detector, 'segment')
        assert callable(detector.detect)
        assert callable(detector.segment)
