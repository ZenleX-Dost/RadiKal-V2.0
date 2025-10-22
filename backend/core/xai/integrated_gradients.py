"""Integrated Gradients implementation for visual explanations.

This module implements Integrated Gradients (IG) using the Captum library
for generating attribution-based explanations.
"""

from typing import Optional, Union, Tuple
import numpy as np
import torch
import torch.nn as nn
from captum.attr import IntegratedGradients as CaptumIG
from captum.attr import visualization as viz


class IntegratedGradientsExplainer:
    """Integrated Gradients explainer for attribution-based explanations.
    
    Integrated Gradients computes attributions by integrating gradients
    along a path from a baseline to the input image.
    """
    
    def __init__(
        self,
        model: nn.Module,
        n_steps: int = 50,
        internal_batch_size: Optional[int] = None
    ):
        """Initialize Integrated Gradients explainer.
        
        Args:
            model: PyTorch model to explain.
            n_steps: Number of steps in the integration path.
            internal_batch_size: Batch size for internal computations.
        """
        self.model = model
        self.model.eval()
        self.n_steps = n_steps
        self.internal_batch_size = internal_batch_size
        
        self.ig = CaptumIG(self.model, multiply_by_inputs=True)
    
    def _prepare_baseline(
        self,
        image: torch.Tensor,
        baseline_type: str = 'black'
    ) -> torch.Tensor:
        """Prepare baseline image for IG computation.
        
        Args:
            image: Input image tensor.
            baseline_type: Type of baseline ('black', 'white', 'blur', 'random').
            
        Returns:
            Baseline tensor with same shape as image.
        """
        if baseline_type == 'black':
            baseline = torch.zeros_like(image)
        elif baseline_type == 'white':
            baseline = torch.ones_like(image)
        elif baseline_type == 'blur':
            import torch.nn.functional as F
            kernel_size = 15
            sigma = 5.0
            baseline = image.clone()
            if len(baseline.shape) == 4:
                for i in range(baseline.shape[0]):
                    for c in range(baseline.shape[1]):
                        baseline[i, c] = self._gaussian_blur(baseline[i, c], kernel_size, sigma)
            else:
                for c in range(baseline.shape[0]):
                    baseline[c] = self._gaussian_blur(baseline[c], kernel_size, sigma)
        elif baseline_type == 'random':
            baseline = torch.rand_like(image)
        else:
            raise ValueError(f"Unknown baseline type: {baseline_type}")
        
        return baseline
    
    def _gaussian_blur(
        self,
        tensor: torch.Tensor,
        kernel_size: int,
        sigma: float
    ) -> torch.Tensor:
        """Apply Gaussian blur to a tensor.
        
        Args:
            tensor: Input tensor (H, W).
            kernel_size: Size of Gaussian kernel.
            sigma: Standard deviation of Gaussian.
            
        Returns:
            Blurred tensor.
        """
        import scipy.ndimage as ndimage
        numpy_array = tensor.cpu().numpy()
        blurred = ndimage.gaussian_filter(numpy_array, sigma=sigma)
        return torch.from_numpy(blurred).to(tensor.device)
    
    def generate_heatmap(
        self,
        image: Union[torch.Tensor, np.ndarray],
        target_class: Optional[int] = None,
        baseline_type: str = 'black',
        normalize: bool = True
    ) -> np.ndarray:
        """Generate Integrated Gradients heatmap.
        
        Args:
            image: Input image as tensor (1, C, H, W) or (C, H, W) or numpy array.
            target_class: Target class index. If None, uses predicted class.
            baseline_type: Type of baseline to use.
            normalize: Whether to normalize heatmap to [0, 1].
            
        Returns:
            IG heatmap as numpy array (H, W) with values in [0, 1].
        """
        if isinstance(image, np.ndarray):
            image = torch.from_numpy(image).float()
        
        if len(image.shape) == 3:
            image = image.unsqueeze(0)
        
        image = image.requires_grad_(True)
        
        baseline = self._prepare_baseline(image, baseline_type)
        
        if target_class is None:
            with torch.no_grad():
                output = self.model(image)
                if isinstance(output, dict):
                    scores = output.get('scores', output.get('logits', output.get('pred', None)))
                else:
                    scores = output
                
                if scores is None:
                    raise ValueError("Cannot extract scores from model output")
                
                target_class = torch.argmax(scores[0]).item()
        
        attributions = self.ig.attribute(
            image,
            baselines=baseline,
            target=target_class,
            n_steps=self.n_steps,
            internal_batch_size=self.internal_batch_size
        )
        
        attributions = attributions.squeeze().cpu().detach().numpy()
        
        if len(attributions.shape) == 3:
            heatmap = np.mean(np.abs(attributions), axis=0)
        else:
            heatmap = np.abs(attributions)
        
        if normalize and heatmap.max() > 0:
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        
        return heatmap
    
    def generate_attribution_map(
        self,
        image: Union[torch.Tensor, np.ndarray],
        target_class: Optional[int] = None,
        baseline_type: str = 'black'
    ) -> np.ndarray:
        """Generate detailed attribution map with signed attributions.
        
        Args:
            image: Input image.
            target_class: Target class index.
            baseline_type: Type of baseline to use.
            
        Returns:
            Attribution map with positive and negative attributions.
        """
        if isinstance(image, np.ndarray):
            image = torch.from_numpy(image).float()
        
        if len(image.shape) == 3:
            image = image.unsqueeze(0)
        
        image = image.requires_grad_(True)
        baseline = self._prepare_baseline(image, baseline_type)
        
        if target_class is None:
            with torch.no_grad():
                output = self.model(image)
                if isinstance(output, dict):
                    scores = output.get('scores', output.get('logits', output.get('pred', None)))
                else:
                    scores = output
                target_class = torch.argmax(scores[0]).item()
        
        attributions = self.ig.attribute(
            image,
            baselines=baseline,
            target=target_class,
            n_steps=self.n_steps,
            internal_batch_size=self.internal_batch_size
        )
        
        attribution_map = attributions.squeeze().cpu().detach().numpy()
        
        if len(attribution_map.shape) == 3:
            attribution_map = np.mean(attribution_map, axis=0)
        
        return attribution_map
    
    def visualize_attribution(
        self,
        image: Union[torch.Tensor, np.ndarray],
        target_class: Optional[int] = None,
        baseline_type: str = 'black',
        method: str = 'heat_map'
    ) -> np.ndarray:
        """Generate visualization of attributions.
        
        Args:
            image: Input image.
            target_class: Target class index.
            baseline_type: Type of baseline to use.
            method: Visualization method ('heat_map', 'blended_heat_map', 'masked_image').
            
        Returns:
            Visualization as numpy array.
        """
        if isinstance(image, np.ndarray):
            original_image = image.copy()
            image = torch.from_numpy(image).float()
        else:
            original_image = image.cpu().numpy()
        
        if len(image.shape) == 3:
            image = image.unsqueeze(0)
        
        image = image.requires_grad_(True)
        baseline = self._prepare_baseline(image, baseline_type)
        
        if target_class is None:
            with torch.no_grad():
                output = self.model(image)
                if isinstance(output, dict):
                    scores = output.get('scores', output.get('logits', output.get('pred', None)))
                else:
                    scores = output
                target_class = torch.argmax(scores[0]).item()
        
        attributions = self.ig.attribute(
            image,
            baselines=baseline,
            target=target_class,
            n_steps=self.n_steps,
            internal_batch_size=self.internal_batch_size
        )
        
        return attributions.squeeze().cpu().detach().numpy()
    
    def __call__(
        self,
        image: Union[torch.Tensor, np.ndarray],
        target_class: Optional[int] = None,
        baseline_type: str = 'black'
    ) -> np.ndarray:
        """Callable interface for generating heatmaps.
        
        Args:
            image: Input image.
            target_class: Target class index.
            baseline_type: Type of baseline to use.
            
        Returns:
            Integrated Gradients heatmap.
        """
        return self.generate_heatmap(image, target_class, baseline_type)
