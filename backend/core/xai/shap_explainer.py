"""SHAP-like explainer implementation for visual explanations.

This module implements SHAP-like (SHapley Additive exPlanations) for image models
using gradient-based approximation for fast and compatible explanations.
"""

from typing import Optional, Callable, Union, Tuple
import numpy as np
import torch
import torch.nn as nn
import cv2
import logging

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAP-like explainer for generating pixel-level explanations.
    
    This class uses gradient * input (DeepLIFT-like) attribution to approximate
    SHAP values for image classification models. This approach is much faster
    than exact SHAP and avoids conflicts with Grad-CAM hooks.
    """
    
    def __init__(
        self,
        model: Union[nn.Module, Callable],
        background_samples: Optional[np.ndarray] = None,
        num_background: int = 50
    ):
        """Initialize SHAP explainer.
        
        Args:
            model: PyTorch model or prediction function.
            background_samples: Not used (for API compatibility).
            num_background: Not used (for API compatibility).
        """
        self.model = model
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if isinstance(model, nn.Module):
            model.eval()
            self.pytorch_model = model
            # Get device from model parameters
            try:
                self.device = next(model.parameters()).device
            except StopIteration:
                pass
        else:
            self.pytorch_model = None
        
        self.explainer = self  # For API compatibility
        logger.info("SHAP explainer initialized with gradient-based approximation")
    
    def _compute_gradient_attribution(
        self,
        image: torch.Tensor,
        target_class: int
    ) -> np.ndarray:
        """Compute gradient * input attribution.
        
        Args:
            image: Input image tensor (1, C, H, W).
            target_class: Target class index.
            
        Returns:
            Attribution as numpy array (C, H, W).
        """
        if self.pytorch_model is None:
            return np.zeros((3, image.shape[-2], image.shape[-1]))
        
        # Temporarily disable Grad-CAM hooks to avoid conflicts
        hooks_to_restore = []
        for name, module in self.pytorch_model.named_modules():
            if hasattr(module, '_forward_hooks'):
                for key, hook in list(module._forward_hooks.items()):
                    hooks_to_restore.append((module, '_forward_hooks', key, hook))
                module._forward_hooks.clear()
            if hasattr(module, '_backward_hooks'):
                for key, hook in list(module._backward_hooks.items()):
                    hooks_to_restore.append((module, '_backward_hooks', key, hook))
                module._backward_hooks.clear()
        
        try:
            # Clone image and enable gradients
            image = image.clone().detach().requires_grad_(True)
            image = image.to(self.device)
            
            # Forward pass
            output = self.pytorch_model(image)
            
            if isinstance(output, dict):
                scores = output.get('scores', output.get('logits', output.get('pred', None)))
            elif hasattr(output, 'probs'):
                # YOLO output
                scores = output.probs.data.unsqueeze(0)
            else:
                scores = output
            
            if scores is None:
                return np.zeros((3, image.shape[-2], image.shape[-1]))
            
            # Ensure scores have proper shape
            if len(scores.shape) == 1:
                scores = scores.unsqueeze(0)
            
            # Get score for target class
            target_score = scores[0, target_class]
            
            # Backward pass
            self.pytorch_model.zero_grad()
            target_score.backward()
            
            # Get gradients
            if image.grad is not None:
                gradients = image.grad.cpu().numpy()[0]  # (C, H, W)
                input_np = image.detach().cpu().numpy()[0]
                # Gradient * Input attribution
                attribution = gradients * input_np
            else:
                attribution = np.zeros((3, image.shape[-2], image.shape[-1]))
            
        except Exception as e:
            logger.warning(f"Gradient computation failed: {e}")
            attribution = np.zeros((3, image.shape[-2], image.shape[-1]))
        
        finally:
            # Restore hooks
            for module, hook_dict_name, key, hook in hooks_to_restore:
                getattr(module, hook_dict_name)[key] = hook
        
        return attribution
    
    def generate_heatmap(
        self,
        image: Union[np.ndarray, torch.Tensor],
        target_class: Optional[int] = None,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate gradient-based heatmap approximating SHAP values.
        
        Args:
            image: Input image as numpy array (C, H, W) or (1, C, H, W) or tensor.
            target_class: Target class index. If None, uses predicted class.
            normalize: Whether to normalize heatmap to [0, 1].
            
        Returns:
            Heatmap as numpy array (H, W) with values in [0, 1].
        """
        # Convert to tensor if needed
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3:
                image = np.expand_dims(image, axis=0)
            image_tensor = torch.from_numpy(image).float()
        else:
            if len(image.shape) == 3:
                image_tensor = image.unsqueeze(0)
            else:
                image_tensor = image.clone()
        
        image_tensor = image_tensor.to(self.device)
        h, w = image_tensor.shape[-2:]
        
        # Get predicted class if not specified
        if target_class is None and self.pytorch_model is not None:
            with torch.no_grad():
                output = self.pytorch_model(image_tensor)
                if isinstance(output, dict):
                    scores = output.get('scores', output.get('logits', output.get('pred', None)))
                elif hasattr(output, 'probs'):
                    scores = output.probs.data.unsqueeze(0)
                else:
                    scores = output
                if scores is not None:
                    target_class = torch.argmax(scores[0]).item()
                else:
                    target_class = 0
        
        # Compute gradient attribution
        attribution = self._compute_gradient_attribution(image_tensor, target_class)
        
        # Combine channels - use absolute values
        if len(attribution.shape) == 3:
            heatmap = np.mean(np.abs(attribution), axis=0)
        else:
            heatmap = np.abs(attribution)
        
        # Normalize
        if normalize and heatmap.max() > 0:
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        
        return heatmap.astype(np.float32)
    
    def generate_attribution_map(
        self,
        image: Union[np.ndarray, torch.Tensor],
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """Generate detailed attribution map preserving sign of attributions.
        
        Args:
            image: Input image as numpy array or tensor.
            target_class: Target class index.
            
        Returns:
            Attribution map with positive and negative attributions (H, W).
        """
        # Convert to tensor if needed
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3:
                image = np.expand_dims(image, axis=0)
            image_tensor = torch.from_numpy(image).float()
        else:
            if len(image.shape) == 3:
                image_tensor = image.unsqueeze(0)
            else:
                image_tensor = image.clone()
        
        image_tensor = image_tensor.to(self.device)
        
        # Get predicted class if not specified
        if target_class is None and self.pytorch_model is not None:
            with torch.no_grad():
                output = self.pytorch_model(image_tensor)
                if isinstance(output, dict):
                    scores = output.get('scores', output.get('logits', output.get('pred', None)))
                elif hasattr(output, 'probs'):
                    scores = output.probs.data.unsqueeze(0)
                else:
                    scores = output
                if scores is not None:
                    target_class = torch.argmax(scores[0]).item()
                else:
                    target_class = 0
        
        # Compute gradient attribution
        attribution = self._compute_gradient_attribution(image_tensor, target_class)
        
        # Average across channels but preserve sign
        if len(attribution.shape) == 3:
            attribution_map = np.mean(attribution, axis=0)
        else:
            attribution_map = attribution
        
        return attribution_map
    
    def __call__(
        self,
        image: Union[np.ndarray, torch.Tensor],
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """Callable interface for generating heatmaps.
        
        Args:
            image: Input image.
            target_class: Target class index.
            
        Returns:
            SHAP-like heatmap.
        """
        return self.generate_heatmap(image, target_class)
    
    def explain(
        self,
        image: Union[torch.Tensor, np.ndarray],
        target_class: Optional[int] = None
    ) -> Tuple[np.ndarray, dict]:
        """Generate SHAP-like explanation with overlay visualization.
        
        Args:
            image: Input image tensor or numpy array.
            target_class: Target class index.
            
        Returns:
            Tuple of (overlay_image, metadata).
        """
        # Generate heatmap
        heatmap = self.generate_heatmap(image, target_class, normalize=True)
        
        # Convert to visualization
        visualization = self.visualize(heatmap, None)
        
        metadata = {
            'method': 'shap',
            'approximation': 'gradient_input',
            'target_class': target_class,
            'attribution_range': (float(heatmap.min()), float(heatmap.max()))
        }
        
        return visualization, metadata
    
    def visualize(
        self,
        shap_values: np.ndarray,
        original_image: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Visualize SHAP values as heatmap overlay.
        
        Args:
            shap_values: SHAP attribution values (H, W).
            original_image: Original image (if available).
            
        Returns:
            Visualization as RGB image.
        """
        # Ensure heatmap is 2D
        if len(shap_values.shape) > 2:
            heatmap = np.mean(np.abs(shap_values), axis=0)
        else:
            heatmap = np.abs(shap_values)
        
        # Normalize
        if heatmap.max() > 0:
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        
        # Resize to standard size if needed
        if heatmap.shape[0] < 100 or heatmap.shape[1] < 100:
            heatmap = cv2.resize(heatmap, (224, 224))
        
        # Convert to color
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8), 
            cv2.COLORMAP_JET
        )
        
        # Overlay if original image provided
        if original_image is not None:
            if len(original_image.shape) == 2:
                original_image = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
            # Resize heatmap to match original
            if heatmap_colored.shape[:2] != original_image.shape[:2]:
                heatmap_colored = cv2.resize(
                    heatmap_colored, 
                    (original_image.shape[1], original_image.shape[0])
                )
            overlay = cv2.addWeighted(original_image, 0.6, heatmap_colored, 0.4, 0)
            return overlay
        
        # Convert BGR to RGB
        return cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
