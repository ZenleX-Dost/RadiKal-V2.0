"""
YOLOv8-based Defect Detector for RadiKal

This module implements defect detection using the trained YOLOv8 model.
Provides a compatible interface with the existing API.

Author: RadiKal Team  
Date: 2025-10-20
"""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import torch
from pathlib import Path
from PIL import Image
import logging

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("ultralytics not installed. Run: pip install ultralytics")

logger = logging.getLogger(__name__)


class YOLODefectDetector:
    """
    YOLOv8-based defect detection model for weld radiographic images.
    
    This detector uses the trained YOLOv8s model with 99.88% mAP@0.5
    to detect defects in welds:
    - LP: Lack of Penetration
    - PO: Porosity
    - CR: Cracks
    - ND: No Defect (clean weld)
    """
    
    # Class mapping - Weld Defect Types
    CLASS_NAMES = {
        0: "LP",  # Lack of Penetration
        1: "PO",  # Porosity
        2: "CR",  # Cracks
        3: "ND"   # No Defect
    }
    
    # Full defect names
    CLASS_FULL_NAMES = {
        0: "Lack of Penetration",
        1: "Porosity",
        2: "Cracks",
        3: "No Defect"
    }
    
    # Severity thresholds
    SEVERITY_THRESHOLDS = {
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.5,
        "low": 0.0
    }
    
    def __init__(
        self,
        model_path: str = "models/yolo/radikal_weld_detection/weights/best.pt",
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45
    ):
        """
        Initialize the YOLOv8 defect detector.
        
        Args:
            model_path: Path to trained YOLOv8 weights
            device: Device to run inference ('cpu', 'cuda', or None for auto)
            confidence_threshold: Minimum confidence for detections (0-1)
            iou_threshold: IoU threshold for NMS (0-1)
        """
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at: {self.model_path}\n"
                f"Please ensure training completed successfully."
            )
        
        # Set device
        if device is None:
            self.device = '0' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        
        # Load model
        logger.info(f"Loading YOLOv8 model from: {self.model_path}")
        self.model = YOLO(str(self.model_path))
        logger.info(f"Model loaded successfully on device: {self.device}")
        
        # Model info
        self.num_classes = 4
        self.input_size = 640
    
    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: Optional[float] = None,
        return_masks: bool = False
    ) -> Dict[str, Any]:
        """
        Detect defects in an image.
        
        Args:
            image: Input image as numpy array (H, W, C) or PIL Image
            confidence_threshold: Override default confidence threshold
            return_masks: Whether to return segmentation masks (if available)
            
        Returns:
            Dictionary containing:
                - boxes: List of bounding boxes [[x1, y1, x2, y2], ...]
                - scores: List of confidence scores [0-1]
                - labels: List of class IDs
                - class_names: List of class names
                - num_detections: Number of detections
                - image_shape: Original image shape (H, W)
        """
        conf_threshold = confidence_threshold or self.confidence_threshold
        
        # Run inference
        results = self.model.predict(
            image,
            conf=conf_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )
        
        # Parse results
        result = results[0]  # Get first image result
        
        boxes = []
        scores = []
        labels = []
        class_names = []
        
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                # Get bounding box coordinates
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                boxes.append(xyxy)
                
                # Get confidence score
                conf = float(box.conf[0].cpu().numpy())
                scores.append(conf)
                
                # Get class
                cls_id = int(box.cls[0].cpu().numpy())
                labels.append(cls_id)
                class_names.append(self.CLASS_NAMES[cls_id])
        
        detection_result = {
            "boxes": boxes,
            "scores": scores,
            "labels": labels,
            "class_names": class_names,
            "num_detections": len(boxes),
            "image_shape": result.orig_shape,  # (H, W)
        }
        
        # Add masks if requested and available
        if return_masks and hasattr(result, 'masks') and result.masks is not None:
            masks = []
            for mask in result.masks:
                mask_array = mask.data[0].cpu().numpy()
                masks.append(mask_array)
            detection_result["masks"] = masks
        
        return detection_result
    
    def predict(
        self,
        image_tensor: torch.Tensor,
        confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict defects from image tensor (API-compatible format).
        
        Args:
            image_tensor: Image tensor (1, C, H, W) or (C, H, W)
            confidence_threshold: Confidence threshold for detections
            
        Returns:
            List of detection dictionaries with keys:
                - box: [x1, y1, x2, y2]
                - score: confidence score
                - label: class name
                - class_id: class ID
                - severity: 'high', 'medium', or 'low'
        """
        # Convert tensor to numpy
        if isinstance(image_tensor, torch.Tensor):
            if image_tensor.dim() == 4:
                image_tensor = image_tensor.squeeze(0)
            image_np = image_tensor.permute(1, 2, 0).cpu().numpy()
            
            # Convert to uint8 if needed
            if image_np.max() <= 1.0:
                image_np = (image_np * 255).astype(np.uint8)
            else:
                image_np = image_np.astype(np.uint8)
        else:
            image_np = image_tensor
        
        # Run detection
        detection_result = self.detect(
            image_np,
            confidence_threshold=confidence_threshold,
            return_masks=True
        )
        
        # Convert to API format
        detections = []
        for i in range(detection_result["num_detections"]):
            box = detection_result["boxes"][i]
            score = detection_result["scores"][i]
            class_name = detection_result["class_names"][i]
            class_id = detection_result["labels"][i]
            
            # Determine severity
            if score >= self.SEVERITY_THRESHOLDS["high"]:
                severity = "high"
            elif score >= self.SEVERITY_THRESHOLDS["medium"]:
                severity = "medium"
            else:
                severity = "low"
            
            detection = {
                "box": box,
                "score": score,
                "label": class_name,
                "class_id": class_id,
                "severity": severity,
            }
            
            # Add mask if available
            if "masks" in detection_result and i < len(detection_result["masks"]):
                detection["mask"] = detection_result["masks"][i]
            
            detections.append(detection)
        
        return detections
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_type": "YOLOv8s",
            "model_path": str(self.model_path),
            "num_classes": self.num_classes,
            "class_names": self.CLASS_NAMES,
            "input_size": self.input_size,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "performance": {
                "mAP@0.5": 0.9988,
                "mAP@0.5:0.95": 0.9974,
                "precision": 0.995,
                "recall": 0.995,
                "inference_speed_fps": "60+"
            }
        }
    
    def batch_detect(
        self,
        images: List[np.ndarray],
        confidence_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Run batch detection on multiple images.
        
        Args:
            images: List of images as numpy arrays
            confidence_threshold: Confidence threshold for detections
            
        Returns:
            List of detection results, one per image
        """
        conf_threshold = confidence_threshold or self.confidence_threshold
        
        # Run batch inference
        results = self.model.predict(
            images,
            conf=conf_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False
        )
        
        # Parse all results
        batch_results = []
        for result in results:
            boxes = []
            scores = []
            labels = []
            class_names = []
            
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    boxes.append(xyxy)
                    
                    conf = float(box.conf[0].cpu().numpy())
                    scores.append(conf)
                    
                    cls_id = int(box.cls[0].cpu().numpy())
                    labels.append(cls_id)
                    class_names.append(self.CLASS_NAMES[cls_id])
            
            batch_results.append({
                "boxes": boxes,
                "scores": scores,
                "labels": labels,
                "class_names": class_names,
                "num_detections": len(boxes),
                "image_shape": result.orig_shape,
            })
        
        return batch_results
    
    def __repr__(self) -> str:
        """String representation of the detector."""
        return (
            f"YOLODefectDetector(\n"
            f"  model_path={self.model_path},\n"
            f"  device={self.device},\n"
            f"  num_classes={self.num_classes},\n"
            f"  confidence_threshold={self.confidence_threshold}\n"
            f")"
        )
