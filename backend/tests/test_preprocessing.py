"""Unit tests for image preprocessing module."""

import pytest
import numpy as np
import tempfile
import os
from PIL import Image
from core.preprocessing.image_processor import (
    ImageProcessor,
    validate_image_format
)


class TestImageProcessor:
    """Test suite for ImageProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create an ImageProcessor instance."""
        return ImageProcessor(target_size=(512, 512))
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample RGB image."""
        return np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    
    @pytest.fixture
    def temp_image_file(self, sample_image):
        """Create a temporary image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.fromarray(sample_image)
            img.save(f.name)
            yield f.name
        os.unlink(f.name)
    
    def test_initialization(self):
        """Test ImageProcessor initialization."""
        processor = ImageProcessor(
            target_size=(224, 224),
            normalize=True,
            mean=(0.5, 0.5, 0.5),
            std=(0.5, 0.5, 0.5)
        )
        assert processor.target_size == (224, 224)
        assert processor.normalize is True
        assert np.array_equal(processor.mean, np.array([0.5, 0.5, 0.5]))
    
    def test_load_image(self, processor, temp_image_file):
        """Test loading image from file."""
        image = processor.load_image(temp_image_file)
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3
        assert image.shape[2] == 3
    
    def test_load_image_invalid_path(self, processor):
        """Test loading image from invalid path."""
        with pytest.raises(ValueError):
            processor.load_image('nonexistent.jpg')
    
    def test_load_image_from_bytes(self, processor, sample_image):
        """Test loading image from bytes."""
        img = Image.fromarray(sample_image)
        import io
        bytes_io = io.BytesIO()
        img.save(bytes_io, format='PNG')
        image_bytes = bytes_io.getvalue()
        
        image = processor.load_image_from_bytes(image_bytes)
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3
    
    def test_resize_image(self, processor, sample_image):
        """Test image resizing."""
        resized = processor.resize_image(sample_image)
        assert resized.shape[:2] == processor.target_size
    
    def test_resize_image_custom_size(self, processor, sample_image):
        """Test image resizing with custom size."""
        custom_size = (128, 128)
        resized = processor.resize_image(sample_image, target_size=custom_size)
        assert resized.shape[:2] == custom_size
    
    def test_normalize_image(self, processor, sample_image):
        """Test image normalization."""
        normalized = processor.normalize_image(sample_image)
        assert normalized.dtype == np.float32
        assert normalized.max() <= 3.0
        assert normalized.min() >= -3.0
    
    def test_normalize_image_invalid_dtype(self, processor):
        """Test normalization with invalid dtype."""
        invalid_image = np.array(['a', 'b', 'c'])
        with pytest.raises(ValueError, match="Invalid image dtype"):
            processor.normalize_image(invalid_image)
    
    def test_preprocess_from_path(self, processor, temp_image_file):
        """Test complete preprocessing from file path."""
        preprocessed = processor.preprocess(temp_image_file)
        assert isinstance(preprocessed, np.ndarray)
        assert preprocessed.shape[:2] == processor.target_size
    
    def test_preprocess_from_array(self, processor, sample_image):
        """Test complete preprocessing from numpy array."""
        preprocessed = processor.preprocess(sample_image)
        assert isinstance(preprocessed, np.ndarray)
        assert preprocessed.shape[:2] == processor.target_size
    
    def test_preprocess_no_resize(self, processor, sample_image):
        """Test preprocessing without resizing."""
        preprocessed = processor.preprocess(sample_image, resize=False)
        assert preprocessed.shape[:2] == sample_image.shape[:2]
    
    def test_to_tensor(self, processor, sample_image):
        """Test converting image to tensor format."""
        preprocessed = processor.normalize_image(sample_image)
        tensor = processor.to_tensor(preprocessed)
        assert tensor.shape[0] == 3
        assert len(tensor.shape) == 3
    
    def test_add_batch_dimension(self, processor, sample_image):
        """Test adding batch dimension."""
        tensor = processor.to_tensor(sample_image)
        batched = processor.add_batch_dimension(tensor)
        assert batched.shape[0] == 1
        assert len(batched.shape) == 4


class TestValidateImageFormat:
    """Test suite for validate_image_format function."""
    
    def test_valid_2d_image(self):
        """Test validation of 2D grayscale image."""
        image = np.random.rand(100, 100)
        assert validate_image_format(image) is True
    
    def test_valid_3d_rgb_image(self):
        """Test validation of 3D RGB image."""
        image = np.random.rand(100, 100, 3)
        assert validate_image_format(image) is True
    
    def test_valid_3d_rgba_image(self):
        """Test validation of 3D RGBA image."""
        image = np.random.rand(100, 100, 4)
        assert validate_image_format(image) is True
    
    def test_invalid_not_array(self):
        """Test validation with non-array input."""
        with pytest.raises(ValueError, match="must be a numpy array"):
            validate_image_format([1, 2, 3])
    
    def test_invalid_shape(self):
        """Test validation with invalid shape."""
        image = np.random.rand(10, 10, 10, 10)
        with pytest.raises(ValueError, match="must be 2D or 3D"):
            validate_image_format(image)
    
    def test_invalid_channels(self):
        """Test validation with invalid number of channels."""
        image = np.random.rand(100, 100, 5)
        with pytest.raises(ValueError, match="must have 1, 3, or 4 channels"):
            validate_image_format(image)
