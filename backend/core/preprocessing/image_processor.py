"""Image preprocessing utilities for XAI Visual Quality Control.

This module provides image preprocessing functions including loading,
normalization, resizing, and data type validation.
"""

from typing import Optional, Tuple, Union
import numpy as np
import cv2
from PIL import Image


class ImageProcessor:
    """Image processor for preparing images for model inference.
    
    This class handles image loading, preprocessing, normalization,
    and validation to ensure consistent input format for detection models.
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (512, 512),
        normalize: bool = True,
        mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
    ):
        """Initialize the ImageProcessor.
        
        Args:
            target_size: Target image size as (height, width).
            normalize: Whether to normalize pixel values.
            mean: Mean values for normalization (RGB).
            std: Standard deviation values for normalization (RGB).
        """
        self.target_size = target_size
        self.normalize = normalize
        self.mean = np.array(mean, dtype=np.float32)
        self.std = np.array(std, dtype=np.float32)
    
    def load_image(
        self,
        image_path: str
    ) -> np.ndarray:
        """Load an image from file path.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Loaded image as numpy array in RGB format.
            
        Raises:
            FileNotFoundError: If image file does not exist.
            ValueError: If image cannot be loaded.
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image from {image_path}")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}")
    
    def load_image_from_bytes(
        self,
        image_bytes: bytes
    ) -> np.ndarray:
        """Load an image from bytes.
        
        Args:
            image_bytes: Image data as bytes.
            
        Returns:
            Loaded image as numpy array in RGB format.
            
        Raises:
            ValueError: If image cannot be loaded.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = np.array(image.convert('RGB'))
            return image
        except Exception as e:
            raise ValueError(f"Error loading image from bytes: {str(e)}")
    
    def resize_image(
        self,
        image: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """Resize image to target size.
        
        Args:
            image: Input image as numpy array.
            target_size: Optional target size, uses self.target_size if None.
            
        Returns:
            Resized image.
        """
        if target_size is None:
            target_size = self.target_size
        
        resized = cv2.resize(
            image,
            (target_size[1], target_size[0]),
            interpolation=cv2.INTER_LINEAR
        )
        return resized
    
    def normalize_image(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """Normalize image pixel values.
        
        Args:
            image: Input image as numpy array with values in [0, 255].
            
        Returns:
            Normalized image with values scaled by mean and std.
            
        Raises:
            ValueError: If image dtype is invalid.
        """
        if not np.issubdtype(image.dtype, np.integer) and not np.issubdtype(image.dtype, np.floating):
            raise ValueError(f"Invalid image dtype: {image.dtype}")
        
        image = image.astype(np.float32)
        if image.max() > 1.0:
            image = image / 255.0
        
        if self.normalize:
            image = (image - self.mean) / self.std
        
        return image
    
    def preprocess(
        self,
        image: Union[str, np.ndarray, bytes],
        resize: bool = True
    ) -> np.ndarray:
        """Complete preprocessing pipeline.
        
        Args:
            image: Input image as file path, numpy array, or bytes.
            resize: Whether to resize the image.
            
        Returns:
            Preprocessed image ready for model inference.
        """
        if isinstance(image, str):
            image = self.load_image(image)
        elif isinstance(image, bytes):
            image = self.load_image_from_bytes(image)
        elif not isinstance(image, np.ndarray):
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        if resize:
            image = self.resize_image(image)
        
        image = self.normalize_image(image)
        
        return image
    
    def to_tensor(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """Convert image to tensor format (C, H, W).
        
        Args:
            image: Input image as numpy array (H, W, C).
            
        Returns:
            Image in tensor format (C, H, W).
        """
        if len(image.shape) == 3:
            image = np.transpose(image, (2, 0, 1))
        return image
    
    def add_batch_dimension(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """Add batch dimension to image tensor.
        
        Args:
            image: Input image tensor.
            
        Returns:
            Image with batch dimension added.
        """
        return np.expand_dims(image, axis=0)


def validate_image_format(
    image: np.ndarray
) -> bool:
    """Validate image format and shape.
    
    Args:
        image: Input image to validate.
        
    Returns:
        True if image format is valid.
        
    Raises:
        ValueError: If image format is invalid.
    """
    if not isinstance(image, np.ndarray):
        raise ValueError("Image must be a numpy array")
    
    if len(image.shape) not in [2, 3]:
        raise ValueError(f"Image must be 2D or 3D, got shape {image.shape}")
    
    if len(image.shape) == 3 and image.shape[2] not in [1, 3, 4]:
        raise ValueError(f"Image must have 1, 3, or 4 channels, got {image.shape[2]}")
    
    return True


import io
