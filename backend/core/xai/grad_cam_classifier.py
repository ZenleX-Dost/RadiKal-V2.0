"""
Grad-CAM Implementation for YOLOv8 Classification Models

This module provides Gradient-weighted Class Activation Mapping (Grad-CAM)
specifically designed for YOLOv8-cls models to visualize defect localization
in radiographic weld images.
"""

from typing import Optional, Tuple, Dict, Any
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class YOLOv8ClassifierGradCAM:
    """
    Grad-CAM explainer for YOLOv8 classification models.
    
    Generates heatmaps showing which regions of the radiographic image
    the model focuses on when making defect classification decisions.
    """
    
    def __init__(
        self,
        model: Any,  # YOLO model from ultralytics
        target_layer_name: Optional[str] = None
    ):
        """
        Initialize Grad-CAM for YOLOv8 classifier.
        
        Args:
            model: Loaded YOLOv8 classification model (ultralytics.YOLO)
            target_layer_name: Name of target layer (auto-detects last conv if None)
        """
        self.model = model
        self.target_layer = None
        self.gradients = None
        self.activations = None
        
        # Get the PyTorch model from YOLO wrapper
        try:
            self.pytorch_model = self.model.model
            logger.info(f"Extracted PyTorch model: {type(self.pytorch_model)}")
        except Exception as e:
            logger.error(f"Failed to extract PyTorch model: {e}")
            raise
        
        # Find target layer
        if target_layer_name:
            self.target_layer = self._find_layer_by_name(target_layer_name)
        else:
            self.target_layer = self._find_last_conv_layer()
        
        logger.info(f"Using target layer: {self.target_layer}")
        
        # Register hooks
        self._register_hooks()
    
    def _find_layer_by_name(self, name: str) -> nn.Module:
        """Find layer by name in the model."""
        for layer_name, module in self.pytorch_model.named_modules():
            if name in layer_name:
                return module
        raise ValueError(f"Layer '{name}' not found in model")
    
    def _find_last_conv_layer(self) -> nn.Module:
        """
        Find the last convolutional layer in YOLOv8 backbone.
        
        For YOLOv8-cls, this is typically in the backbone before the classifier head.
        """
        conv_layers = []
        
        # YOLOv8 structure: model.model contains the backbone
        for name, module in self.pytorch_model.named_modules():
            if isinstance(module, nn.Conv2d):
                conv_layers.append((name, module))
        
        if not conv_layers:
            raise ValueError("No convolutional layers found in model")
        
        # Use the last conv layer in backbone (before classifier head)
        # Typically this is in model[9] for YOLOv8s-cls
        last_name, last_layer = conv_layers[-1]
        logger.info(f"Found {len(conv_layers)} conv layers, using: {last_name}")
        
        return last_layer
    
    def _register_hooks(self) -> None:
        """Register forward and backward hooks."""
        def forward_hook(module, input, output):
            # Clone to avoid in-place modification issues
            self.activations = output.detach().clone()
            logger.debug(f"Forward hook: activations shape {output.shape}")
        
        def backward_hook(module, grad_input, grad_output):
            # Clone to avoid in-place modification issues
            self.gradients = grad_output[0].detach().clone()
            logger.debug(f"Backward hook: gradients shape {grad_output[0].shape}")
        
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
    
    def generate_heatmap(
        self,
        image_path: str,
        target_class: Optional[int] = None,
        image_size: int = 224,
        normalize: bool = True
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Generate Grad-CAM heatmap for an image.
        
        Args:
            image_path: Path to radiographic image
            target_class: Class index to explain (None = predicted class)
            image_size: Input size for model (YOLOv8-cls default: 224)
            normalize: Whether to normalize heatmap to [0, 1]
        
        Returns:
            Tuple of:
                - heatmap: numpy array (H, W) with values [0, 1]
                - info: Dict with prediction details
        """
        # Load and preprocess image
        original_image = cv2.imread(str(image_path))
        if original_image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        original_size = original_image.shape[:2]  # (H, W)
        
        # Get model predictions first (this warms up the model)
        results = self.model.predict(
            image_path,
            imgsz=image_size,
            verbose=False
        )
        
        # Extract prediction info
        result = results[0]
        probs = result.probs.data.cpu().numpy()  # Class probabilities
        predicted_class = int(result.probs.top1)
        confidence = float(result.probs.top1conf)
        
        # Use predicted class if not specified
        if target_class is None:
            target_class = predicted_class
        
        logger.info(f"Generating Grad-CAM for class {target_class} (predicted: {predicted_class}, conf: {confidence:.3f})")
        
        # Now do a forward pass with gradients enabled
        self.pytorch_model.eval()
        
        # Set requires_grad for model parameters
        for param in self.pytorch_model.parameters():
            param.requires_grad = True
        
        # Preprocess image for PyTorch
        image_tensor = self._preprocess_image(original_image, image_size)
        image_tensor = image_tensor.requires_grad_(True)
        
        try:
            # Forward pass
            with torch.enable_grad():
                output = self.pytorch_model(image_tensor)
            
            # Get target class score
            if isinstance(output, torch.Tensor):
                target_score = output[0, target_class]
            else:
                # Handle dict output
                target_score = output['logits'][0, target_class] if 'logits' in output else output['scores'][0, target_class]
            
            # Backward pass
            self.pytorch_model.zero_grad()
            target_score.backward(retain_graph=False)
            
        except RuntimeError as e:
            logger.warning(f"Backward pass failed: {e}")
            logger.warning("Using fallback heatmap based on prediction confidence")
            # Generate a simple center-focused heatmap as fallback
            h, w = original_size
            y_coords, x_coords = np.ogrid[:h, :w]
            center_y, center_x = h // 2, w // 2
            heatmap = np.exp(-((x_coords - center_x)**2 + (y_coords - center_y)**2) / (2 * (min(h, w) / 4)**2))
            heatmap = heatmap * confidence  # Scale by confidence
            
            info = {
                'predicted_class': predicted_class,
                'target_class': target_class,
                'confidence': confidence,
                'all_probabilities': probs.tolist(),
                'original_size': original_size,
                'heatmap_range': (float(heatmap.min()), float(heatmap.max())),
                'fallback_mode': True
            }
            
            return heatmap, info
        
        # Generate CAM from gradients and activations
        if self.gradients is None or self.activations is None:
            logger.warning("Gradients or activations not captured, using fallback heatmap")
            heatmap = np.ones(original_size) * 0.5
        else:
            # Compute weights as global average pooling of gradients
            weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # [1, C, 1, 1]
            
            # Weighted combination of activation maps
            cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # [1, 1, H', W']
            
            # Apply ReLU to focus on positive contributions
            cam = F.relu(cam)
            
            # Convert to numpy
            cam_np = cam.squeeze().cpu().numpy()
            
            # Normalize
            if normalize and cam_np.max() > 0:
                cam_np = (cam_np - cam_np.min()) / (cam_np.max() - cam_np.min())
            else:
                cam_np = np.zeros_like(cam_np)
            
            # Resize to original image size
            heatmap = cv2.resize(cam_np, (original_size[1], original_size[0]))
        
        # Prepare info dict
        info = {
            'predicted_class': predicted_class,
            'target_class': target_class,
            'confidence': confidence,
            'all_probabilities': probs.tolist(),
            'original_size': original_size,
            'heatmap_range': (float(heatmap.min()), float(heatmap.max()))
        }
        
        return heatmap, info
    
    def _preprocess_image(self, image: np.ndarray, size: int = 224) -> torch.Tensor:
        """
        Preprocess image for YOLOv8 model input.
        
        Args:
            image: BGR image from cv2
            size: Target size (square)
        
        Returns:
            Preprocessed tensor [1, 3, size, size]
        """
        # Resize
        image_resized = cv2.resize(image, (size, size))
        
        # BGR to RGB
        image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        image_float = image_rgb.astype(np.float32) / 255.0
        
        # HWC to CHW
        image_chw = np.transpose(image_float, (2, 0, 1))
        
        # Add batch dimension
        image_tensor = torch.from_numpy(image_chw).unsqueeze(0)
        
        # Move to same device as model
        device = next(self.pytorch_model.parameters()).device
        image_tensor = image_tensor.to(device)
        
        return image_tensor
    
    def generate_overlay(
        self,
        original_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Create heatmap overlay on original image.
        
        Args:
            original_image: Original BGR image
            heatmap: Grad-CAM heatmap [0, 1]
            alpha: Blending factor (0=original, 1=heatmap)
            colormap: OpenCV colormap
        
        Returns:
            Overlay image
        """
        # Ensure heatmap is uint8 [0, 255]
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, colormap)
        
        # Resize heatmap to match original image if needed
        if heatmap_colored.shape[:2] != original_image.shape[:2]:
            heatmap_colored = cv2.resize(
                heatmap_colored,
                (original_image.shape[1], original_image.shape[0])
            )
        
        # Blend
        overlay = cv2.addWeighted(original_image, 1 - alpha, heatmap_colored, alpha, 0)
        
        return overlay
    
    def find_defect_regions(
        self,
        heatmap: np.ndarray,
        threshold: float = 0.5,
        min_area: int = 100
    ) -> list:
        """
        Identify defect regions from heatmap.
        
        Args:
            heatmap: Grad-CAM heatmap [0, 1]
            threshold: Activation threshold
            min_area: Minimum region area in pixels
        
        Returns:
            List of dicts with region info: {'bbox': [x, y, w, h], 'area': int, 'score': float}
        """
        # Threshold heatmap
        binary = (heatmap > threshold).astype(np.uint8)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate average activation in region
            mask = np.zeros_like(heatmap, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 1, -1)
            score = float(np.mean(heatmap[mask == 1]))
            
            regions.append({
                'bbox': [int(x), int(y), int(w), int(h)],
                'area': int(area),
                'score': score,
                'center': [int(x + w//2), int(y + h//2)]
            })
        
        # Sort by score (highest first)
        regions.sort(key=lambda r: r['score'], reverse=True)
        
        return regions
    
    def describe_defect_location(
        self,
        regions: list,
        image_shape: Tuple[int, int]
    ) -> str:
        """
        Generate natural language description of defect location.
        
        Args:
            regions: List of detected regions
            image_shape: (height, width) of image
        
        Returns:
            Human-readable description
        """
        if not regions:
            return "No significant defect regions detected"
        
        h, w = image_shape
        top_region = regions[0]
        cx, cy = top_region['center']
        
        # Determine position
        if cy < h / 3:
            vert = "upper"
        elif cy < 2 * h / 3:
            vert = "central"
        else:
            vert = "lower"
        
        if cx < w / 3:
            horiz = "left"
        elif cx < 2 * w / 3:
            horiz = "middle"
        else:
            horiz = "right"
        
        # Combine
        if horiz == "middle":
            location = f"{vert} region"
        else:
            location = f"{vert}-{horiz} region"
        
        # Add size info
        area_pct = (top_region['area'] / (h * w)) * 100
        
        if len(regions) == 1:
            return f"Defect indication in {location} (coverage: {area_pct:.1f}%)"
        else:
            return f"Primary defect in {location} ({len(regions)} regions total, coverage: {area_pct:.1f}%)"


def test_gradcam():
    """Quick test function."""
    from core.models.yolo_classifier import YOLOClassifier
    
    # Load classifier
    classifier = YOLOClassifier()
    
    # Create Grad-CAM
    gradcam = YOLOv8ClassifierGradCAM(classifier.model)
    
    # Test on sample image
    test_image = Path("DATA/testing/Difetto1/00006.jpg")
    if test_image.exists():
        heatmap, info = gradcam.generate_heatmap(str(test_image))
        print(f"Generated heatmap: {heatmap.shape}")
        print(f"Info: {info}")
        
        # Find regions
        regions = gradcam.find_defect_regions(heatmap)
        print(f"Found {len(regions)} defect regions")
        
        if regions:
            description = gradcam.describe_defect_location(regions, heatmap.shape)
            print(f"Location: {description}")


if __name__ == "__main__":
    test_gradcam()
