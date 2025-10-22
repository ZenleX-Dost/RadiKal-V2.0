"""Base detection model interface and simple detector implementation.

This module provides the base interface for detection models and a simple
implementation using a pre-trained model for defect detection.
"""

from typing import List, Dict, Tuple, Optional, Any
from abc import ABC, abstractmethod
import numpy as np
import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor


class BaseDetector(ABC):
    """Abstract base class for defect detection models.
    
    This class defines the interface that all detection models must implement.
    """
    
    @abstractmethod
    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Detect defects in an image.
        
        Args:
            image: Input image as numpy array.
            confidence_threshold: Minimum confidence score for detections.
            
        Returns:
            Dictionary containing bounding boxes, scores, and labels.
        """
        pass
    
    @abstractmethod
    def segment(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Segment defects in an image.
        
        Args:
            image: Input image as numpy array.
            confidence_threshold: Minimum confidence score for segmentation.
            
        Returns:
            Dictionary containing masks, bounding boxes, scores, and labels.
        """
        pass


class DefectDetector(BaseDetector):
    """Defect detection model using Faster R-CNN.
    
    This class implements defect detection using a Faster R-CNN model
    with ResNet-50 backbone, fine-tuned for radiographic image analysis.
    """
    
    def __init__(
        self,
        num_classes: int = 2,
        device: Optional[str] = None,
        model_path: Optional[str] = None
    ):
        """Initialize the DefectDetector.
        
        Args:
            num_classes: Number of classes (background + defect types).
            device: Device to run inference on ('cpu', 'cuda', or None for auto).
            model_path: Path to pre-trained model weights.
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.num_classes = num_classes
        self.model = self._build_model()
        
        if model_path:
            self.load_weights(model_path)
        
        self.model.to(self.device)
        self.model.eval()
    
    def _build_model(self) -> nn.Module:
        """Build the detection model.
        
        Returns:
            Faster R-CNN model with custom head.
        """
        model = fasterrcnn_resnet50_fpn(pretrained=True)
        
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, self.num_classes)
        
        return model
    
    def load_weights(self, model_path: str) -> None:
        """Load model weights from file.
        
        Args:
            model_path: Path to model weights file.
        """
        checkpoint = torch.load(model_path, map_location=self.device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)
    
    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for model input.
        
        Args:
            image: Input image as numpy array (H, W, C) in [0, 255].
            
        Returns:
            Preprocessed image tensor.
        """
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
        
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)
        
        image_tensor = torch.from_numpy(image).permute(2, 0, 1)
        
        return image_tensor
    
    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Detect defects in an image.
        
        Args:
            image: Input image as numpy array.
            confidence_threshold: Minimum confidence score for detections.
            
        Returns:
            Dictionary with keys:
                - boxes: List of bounding boxes [x1, y1, x2, y2]
                - scores: List of confidence scores
                - labels: List of class labels
        """
        image_tensor = self.preprocess_image(image)
        image_tensor = image_tensor.to(self.device)
        
        with torch.no_grad():
            predictions = self.model([image_tensor])[0]
        
        mask = predictions['scores'] >= confidence_threshold
        
        boxes = predictions['boxes'][mask].cpu().numpy()
        scores = predictions['scores'][mask].cpu().numpy()
        labels = predictions['labels'][mask].cpu().numpy()
        
        return {
            'boxes': boxes.tolist(),
            'scores': scores.tolist(),
            'labels': labels.tolist()
        }
    
    def segment(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Segment defects in an image.
        
        For Faster R-CNN, this method generates binary masks from bounding boxes.
        For true instance segmentation, use Mask R-CNN instead.
        
        Args:
            image: Input image as numpy array.
            confidence_threshold: Minimum confidence score for segmentation.
            
        Returns:
            Dictionary with keys:
                - masks: List of binary masks
                - boxes: List of bounding boxes [x1, y1, x2, y2]
                - scores: List of confidence scores
                - labels: List of class labels
        """
        detections = self.detect(image, confidence_threshold)
        
        h, w = image.shape[:2]
        masks = []
        
        for box in detections['boxes']:
            mask = np.zeros((h, w), dtype=np.uint8)
            x1, y1, x2, y2 = map(int, box)
            mask[y1:y2, x1:x2] = 1
            masks.append(mask)
        
        return {
            'masks': masks,
            'boxes': detections['boxes'],
            'scores': detections['scores'],
            'labels': detections['labels']
        }
    
    def get_feature_maps(
        self,
        image: np.ndarray,
        layer_name: Optional[str] = None
    ) -> torch.Tensor:
        """Extract feature maps for XAI methods.
        
        Args:
            image: Input image as numpy array.
            layer_name: Optional specific layer to extract features from.
            
        Returns:
            Feature maps tensor.
        """
        image_tensor = self.preprocess_image(image)
        image_tensor = image_tensor.to(self.device)
        
        features = self.model.backbone(image_tensor.unsqueeze(0))
        
        if isinstance(features, dict):
            return features[list(features.keys())[-1]]
        return features
