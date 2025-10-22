"""SHAP explainer implementation for visual explanations.

This module implements SHAP (SHapley Additive exPlanations) for image models
using the shap library.
"""

from typing import Optional, Callable, Union
import numpy as np
import torch
import torch.nn as nn
import shap


class SHAPExplainer:
    """SHAP explainer for generating pixel-level explanations.
    
    This class uses the SHAP library to generate explanations for image
    classification and detection models.
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
            background_samples: Background dataset for SHAP. If None, uses zeros.
            num_background: Number of background samples to use.
        """
        self.model = model
        self.num_background = num_background
        
        if isinstance(model, nn.Module):
            model.eval()
            self.predict_fn = self._create_predict_fn(model)
        else:
            self.predict_fn = model
        
        if background_samples is None:
            background_samples = np.zeros((num_background, 3, 224, 224))
        
        self.explainer = shap.DeepExplainer(self.predict_fn, torch.tensor(background_samples))
    
    def _create_predict_fn(self, model: nn.Module) -> Callable:
        """Create a prediction function from PyTorch model.
        
        Args:
            model: PyTorch model.
            
        Returns:
            Prediction function.
        """
        def predict(x):
            with torch.no_grad():
                if isinstance(x, np.ndarray):
                    x = torch.from_numpy(x)
                output = model(x.float())
                if isinstance(output, dict):
                    return output.get('scores', output.get('logits', output.get('pred', None)))
                return output
        return predict
    
    def generate_heatmap(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None,
        normalize: bool = True
    ) -> np.ndarray:
        """Generate SHAP heatmap for an image.
        
        Args:
            image: Input image as numpy array.
                  Shape: (C, H, W) or (1, C, H, W).
            target_class: Target class index. If None, uses predicted class.
            normalize: Whether to normalize heatmap to [0, 1].
            
        Returns:
            SHAP heatmap as numpy array (H, W) with values in [0, 1].
        """
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        if isinstance(image, np.ndarray):
            image_tensor = torch.from_numpy(image).float()
        else:
            image_tensor = image
        
        shap_values = self.explainer.shap_values(image_tensor)
        
        if isinstance(shap_values, list):
            if target_class is not None:
                shap_values = shap_values[target_class]
            else:
                predictions = self.predict_fn(image_tensor)
                if isinstance(predictions, torch.Tensor):
                    predictions = predictions.numpy()
                target_class = np.argmax(predictions[0])
                shap_values = shap_values[target_class]
        
        if isinstance(shap_values, torch.Tensor):
            shap_values = shap_values.cpu().numpy()
        
        shap_values = shap_values[0]
        
        if len(shap_values.shape) == 3:
            heatmap = np.mean(np.abs(shap_values), axis=0)
        else:
            heatmap = np.abs(shap_values)
        
        if normalize and heatmap.max() > 0:
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        
        return heatmap
    
    def generate_attribution_map(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """Generate detailed attribution map preserving sign of attributions.
        
        Args:
            image: Input image as numpy array.
            target_class: Target class index.
            
        Returns:
            Attribution map with positive and negative attributions.
        """
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        image_tensor = torch.from_numpy(image).float()
        shap_values = self.explainer.shap_values(image_tensor)
        
        if isinstance(shap_values, list):
            if target_class is not None:
                shap_values = shap_values[target_class]
            else:
                predictions = self.predict_fn(image_tensor)
                if isinstance(predictions, torch.Tensor):
                    predictions = predictions.numpy()
                target_class = np.argmax(predictions[0])
                shap_values = shap_values[target_class]
        
        if isinstance(shap_values, torch.Tensor):
            shap_values = shap_values.cpu().numpy()
        
        attribution_map = shap_values[0]
        
        if len(attribution_map.shape) == 3:
            attribution_map = np.mean(attribution_map, axis=0)
        
        return attribution_map
    
    def __call__(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """Callable interface for generating heatmaps.
        
        Args:
            image: Input image.
            target_class: Target class index.
            
        Returns:
            SHAP heatmap.
        """
        return self.generate_heatmap(image, target_class)
