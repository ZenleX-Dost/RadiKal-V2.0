"""
YOLOv8 Classification Wrapper for Weld Defect Classification

This module provides a wrapper for YOLOv8 classification models
to integrate with the RadiKal application.
"""

import numpy as np
import torch
from pathlib import Path
from typing import Dict, Any, Optional, List
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)


class YOLOClassifier:
    """
    YOLOv8 Classification wrapper for whole-image defect classification.
    
    Unlike detection models that find and localize defects, this classifier
    assigns a single class label to the entire radiographic image.
    """
    
    # Class mapping
    CLASS_NAMES = {
        0: "LP",  # Lack of Penetration (Difetto1)
        1: "PO",  # Porosity (Difetto2)
        2: "CR",  # Cracks (Difetto4)
        3: "ND"   # No Defect (NoDifetto)
    }
    
    CLASS_FULL_NAMES = {
        0: "Lack of Penetration",
        1: "Porosity",
        2: "Cracks",
        3: "No Defect"
    }
    
    def __init__(
        self,
        model_path: str = "models/yolo/classification_defect_focused/weights/best.pt",
        device: Optional[str] = None,
        nd_confidence_threshold: float = 0.7
    ):
        """
        Initialize the YOLOv8 classifier.
        
        Args:
            model_path: Path to trained YOLOv8-cls weights
            device: Device to run inference ('cpu', 'cuda', or None for auto)
            nd_confidence_threshold: Minimum confidence required to classify as "No Defect"
                                    If ND confidence < threshold, pick highest defect class
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
        
        self.nd_confidence_threshold = nd_confidence_threshold
        
        # Load model
        logger.info(f"Loading YOLOv8 Classification model from: {self.model_path}")
        self.model = YOLO(str(self.model_path))
        logger.info(f"Model loaded successfully on device: {self.device}")
        logger.info(f"Task: {self.model.task}")
        
        # Model info
        self.num_classes = 4
    
    def classify(
        self,
        image: np.ndarray,
        apply_nd_threshold: bool = True
    ) -> Dict[str, Any]:
        """
        Classify defect in radiographic image.
        
        Args:
            image: Input image as numpy array (H, W, C) or PIL Image
            apply_nd_threshold: Whether to apply ND confidence threshold
            
        Returns:
            Dictionary containing:
                - predicted_class: Class ID (0-3)
                - predicted_class_name: Short class name (LP, PO, CR, ND)
                - predicted_class_full_name: Full class name
                - confidence: Confidence score [0-1]
                - all_probabilities: Dict of all class probabilities
                - is_defect: Boolean indicating if a defect was detected
                - defect_type: Defect type if is_defect=True, else None
        """
        # Run inference
        results = self.model.predict(
            image,
            device=self.device,
            verbose=False
        )
        
        # Parse results
        result = results[0]
        
        if not hasattr(result, 'probs') or result.probs is None:
            raise ValueError("Model did not return classification probabilities")
        
        # Get all probabilities
        probs = result.probs.data.cpu().numpy()
        all_probabilities = {
            self.CLASS_NAMES[i]: float(probs[i])
            for i in range(len(probs))
        }
        
        # Get top prediction
        top_class_id = int(result.probs.top1)
        top_confidence = float(result.probs.top1conf)
        
        # Apply ND threshold logic if enabled
        if apply_nd_threshold and top_class_id == 3:  # ND class
            nd_confidence = probs[3]
            
            if nd_confidence < self.nd_confidence_threshold:
                # Not confident it's ND, pick highest defect class
                defect_probs = {
                    0: probs[0],  # LP
                    1: probs[1],  # PO
                    2: probs[2],  # CR
                }
                top_class_id = max(defect_probs, key=defect_probs.get)
                top_confidence = float(defect_probs[top_class_id])
                
                logger.info(
                    f"ND confidence ({nd_confidence:.4f}) below threshold "
                    f"({self.nd_confidence_threshold:.2f}), "
                    f"reclassified as {self.CLASS_NAMES[top_class_id]}"
                )
        
        # Build response
        predicted_class_name = self.CLASS_NAMES[top_class_id]
        predicted_class_full_name = self.CLASS_FULL_NAMES[top_class_id]
        is_defect = (top_class_id != 3)  # Not ND
        defect_type = predicted_class_name if is_defect else None
        
        return {
            "predicted_class": top_class_id,
            "predicted_class_name": predicted_class_name,
            "predicted_class_full_name": predicted_class_full_name,
            "confidence": top_confidence,
            "all_probabilities": all_probabilities,
            "is_defect": is_defect,
            "defect_type": defect_type,
            "nd_threshold_applied": apply_nd_threshold and top_class_id == 3
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_type": "YOLOv8-cls Classification",
            "task": "classify",
            "model_path": str(self.model_path),
            "num_classes": self.num_classes,
            "class_names": self.CLASS_NAMES,
            "device": self.device,
            "nd_confidence_threshold": self.nd_confidence_threshold
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"YOLOClassifier(\n"
            f"  model_path={self.model_path},\n"
            f"  device={self.device},\n"
            f"  num_classes={self.num_classes},\n"
            f"  nd_threshold={self.nd_confidence_threshold}\n"
            f")"
        )
