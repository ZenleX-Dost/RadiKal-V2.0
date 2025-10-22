"""Grad-CAM implementation for visual explanations.

This module implements Gradient-weighted Class Activation Mapping (Grad-CAM)
for generating visual explanations of model predictions.
"""

from typing import Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2


class GradCAM:
    """Grad-CAM explainer for generating class-saliency heatmaps.
    
    Grad-CAM uses the gradients of the target concept flowing into the final
    convolutional layer to produce a coarse localization map highlighting
    important regions in the image for predicting the concept.
    """
    
    def __init__(
        self,
        model: nn.Module,
        target_layer: Optional[nn.Module] = None
    ):
        """Initialize GradCAM.
        
        Args:
            model: PyTorch model to explain.
            target_layer: Target convolutional layer for Grad-CAM.
                        If None, uses the last convolutional layer.
        """
        self.model = model
        self.model.eval()
        
        if target_layer is None:
            target_layer = self._find_last_conv_layer()
        
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        self._register_hooks()
    
    def _find_last_conv_layer(self) -> nn.Module:
        """Find the last convolutional layer in the model.
        
        Returns:
            Last convolutional layer module.
        """
        conv_layers = []
        for module in self.model.modules():
            if isinstance(module, nn.Conv2d):
                conv_layers.append(module)
        
        if not conv_layers:
            raise ValueError("No convolutional layers found in the model")
        
        return conv_layers[-1]
    
    def _register_hooks(self) -> None:
        """Register forward and backward hooks on the target layer."""
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
    
    def generate_heatmap(
        self,
        image: torch.Tensor,
        target_class: Optional[int] = None,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate Grad-CAM heatmap for an image.
        
        Args:
            image: Input image tensor of shape (1, C, H, W) or (C, H, W).
            target_class: Target class index. If None, uses the predicted class.
            normalize: Whether to normalize the heatmap to [0, 1].
            
        Returns:
            Heatmap as numpy array of shape (H, W) with values in [0, 1].
        """
        if len(image.shape) == 3:
            image = image.unsqueeze(0)
        
        image = image.requires_grad_(True)
        
        output = self.model(image)
        
        if target_class is None:
            if isinstance(output, dict):
                scores = output.get('scores', output.get('logits', None))
                if scores is None:
                    raise ValueError("Cannot determine output format")
                target_class = torch.argmax(scores[0]).item()
            else:
                target_class = torch.argmax(output[0]).item()
        
        self.model.zero_grad()
        
        if isinstance(output, dict):
            scores = output.get('scores', output.get('logits', output.get('pred', None)))
            if scores is None:
                raise ValueError("Cannot extract scores from model output")
            class_score = scores[0, target_class] if len(scores.shape) > 1 else scores[target_class]
        else:
            class_score = output[0, target_class] if len(output.shape) > 1 else output[target_class]
        
        class_score.backward()
        
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        
        cam = torch.sum(weights * self.activations, dim=1).squeeze()
        
        cam = F.relu(cam)
        
        cam_np = cam.cpu().numpy()
        
        if normalize:
            if cam_np.max() > 0:
                cam_np = (cam_np - cam_np.min()) / (cam_np.max() - cam_np.min())
            else:
                cam_np = np.zeros_like(cam_np)
        
        return cam_np
    
    def generate_overlay(
        self,
        image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """Generate an overlay of heatmap on the original image.
        
        Args:
            image: Original image as numpy array (H, W, 3) in [0, 255].
            heatmap: Heatmap as numpy array (H, W) in [0, 1].
            alpha: Blending factor for overlay.
            colormap: OpenCV colormap to apply to heatmap.
            
        Returns:
            Overlayed image as numpy array (H, W, 3) in [0, 255].
        """
        if image.dtype == np.float32 or image.dtype == np.float64:
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
        
        h, w = image.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (w, h))
        
        heatmap_uint8 = (heatmap_resized * 255).astype(np.uint8)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, colormap)
        
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        overlay = cv2.addWeighted(image, 1 - alpha, heatmap_colored, alpha, 0)
        
        return overlay
    
    def __call__(
        self,
        image: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """Callable interface for generating heatmaps.
        
        Args:
            image: Input image tensor.
            target_class: Target class index.
            
        Returns:
            Grad-CAM heatmap.
        """
        return self.generate_heatmap(image, target_class)
