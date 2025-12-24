
import pytest
import numpy as np
import cv2
from core.preprocessing.image_processor import ImageProcessor

class TestContrastAdjustment:
    @pytest.fixture
    def processor(self):
        return ImageProcessor()
        
    @pytest.fixture
    def sample_image(self):
        # Create a simple grayscale gradient image 100x100
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            img[:, i] = i * 2.55
        return img

    def test_linear_contrast_increase(self, processor, sample_image):
        """Test linear contrast increase (factor > 1.0)"""
        contrast = 1.5
        adjusted = processor.adjust_contrast(sample_image, contrast=contrast, method='linear')
        
        # Check if values are spread out more
        # Original range approx 0-255
        # Adjusted range should be clipped but slope steeper
        
        # Midpoint (128) should stay roughly same
        mid_mask = (sample_image > 120) & (sample_image < 135)
        # assert np.mean(adjusted[mid_mask]) approx np.mean(sample_image[mid_mask])
        
        # Dark pixels should be darker, light pixels lighter
        # Pixel at 50 -> (50-128)*1.5 + 128 = -78*1.5 + 128 = -117 + 128 = 11 (darker than 50)
        pixel_50 = 50
        expected_50 = 11
        
        # Create a dummy single pixel image to test exact math
        dummy = np.full((1, 1, 3), 50, dtype=np.uint8)
        adj_dummy = processor.adjust_contrast(dummy, contrast=1.5, method='linear')
        assert abs(adj_dummy[0,0,0] - 11) <= 1

    def test_linear_no_change(self, processor, sample_image):
        """Test contrast=1.0 returns original image"""
        adjusted = processor.adjust_contrast(sample_image, contrast=1.0, method='linear')
        np.testing.assert_array_equal(adjusted, sample_image)
        
    def test_histogram_equalization(self, processor):
        """Test histogram equalization runs without error and changes distribution"""
        # Create low contrast image
        img = np.random.randint(100, 150, (100, 100, 3), dtype=np.uint8)
        adjusted = processor.adjust_contrast(img, contrast=1.0, method='histogram')
        
        assert adjusted.shape == img.shape
        assert adjusted.dtype == np.uint8
        # Standard deviation should likely increase
        assert np.std(adjusted) > np.std(img)

    def test_clahe(self, processor, sample_image):
        """Test CLAHE runs without error"""
        adjusted = processor.adjust_contrast(sample_image, contrast=1.0, method='clahe')
        assert adjusted.shape == sample_image.shape
        
    def test_gamma(self, processor):
        """Test gamma correction"""
        img = np.full((10, 10, 3), 100, dtype=np.uint8)
        # Contrast 2.0 -> Gamma 0.5 (brighten)
        # 100/255 = 0.39
        # 0.39^0.5 = 0.62
        # 0.62 * 255 = 159
        adjusted = processor.adjust_contrast(img, contrast=2.0, method='gamma')
        assert adjusted[0,0,0] > 100
