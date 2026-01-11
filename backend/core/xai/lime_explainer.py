"""LIME explainer implementation for visual explanations.

This module implements LIME (Local Interpretable Model-agnostic Explanations)
for image models using superpixel-based explanations.
"""

from typing import Optional, Callable, Union, Tuple
import numpy as np
import torch
import torch.nn as nn
from lime import lime_image
from skimage.segmentation import mark_boundaries


class LIMEExplainer:
    """LIME explainer for generating superpixel-based explanations.
    
    LIME explains predictions by approximating the model locally with an
    interpretable model using superpixels as interpretable components.
    """
    
    def __init__(
        self,
        model: Union[nn.Module, Callable],
        num_samples: int = 1000,
        num_features: int = 10,
        random_seed: int = 42
    ):
        """Initialize LIME explainer.
        
        Args:
            model: PyTorch model or prediction function.
            num_samples: Number of samples to generate for LIME.
            num_features: Number of features (superpixels) to highlight.
            random_seed: Random seed for reproducibility.
        """
        self.model = model
        self.num_samples = num_samples
        self.num_features = num_features
        self.random_seed = random_seed
        
        if isinstance(model, nn.Module):
            model.eval()
            self.predict_fn = self._create_predict_fn(model)
        else:
            self.predict_fn = model
        
        self.explainer = lime_image.LimeImageExplainer(random_state=random_seed)
    
    def _create_predict_fn(self, model: nn.Module) -> Callable:
        """Create a prediction function from PyTorch model.
        
        Args:
            model: PyTorch model.
            
        Returns:
            Prediction function that returns class probabilities.
        """
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        def predict(images):
            # LIME passes images as (N, H, W, C) in range [0, 1]
            batch = []
            for img in images:
                # Ensure proper shape (C, H, W)
                if len(img.shape) == 3:
                    if img.shape[2] == 3:  # (H, W, C) -> (C, H, W)
                        img = np.transpose(img, (2, 0, 1))
                # Ensure float and proper range
                if img.max() <= 1.0:
                    img = img * 255.0
                batch.append(img)
            
            batch = np.array(batch, dtype=np.float32)
            
            # Process one at a time to avoid batch dimension issues with YOLOv8
            all_probs = []
            with torch.no_grad():
                for i in range(len(batch)):
                    single = torch.from_numpy(batch[i:i+1]).float().to(device)
                    
                    # Resize if needed for YOLOv8 (expects 224x224)
                    if single.shape[-1] != 224 or single.shape[-2] != 224:
                        single = torch.nn.functional.interpolate(
                            single, size=(224, 224), mode='bilinear', align_corners=False
                        )
                    
                    output = model(single)
                    
                    # Handle different output types from YOLOv8
                    if isinstance(output, tuple):
                        # YOLOv8 may return tuple (logits, features)
                        logits = output[0]
                    elif isinstance(output, dict):
                        logits = output.get('scores', output.get('logits', output.get('pred', None)))
                    else:
                        logits = output
                    
                    if logits is None:
                        raise ValueError("Cannot extract logits from model output")
                    
                    # Ensure logits is a tensor
                    if not isinstance(logits, torch.Tensor):
                        logits = torch.tensor(logits)
                    
                    probs = torch.softmax(logits, dim=-1)
                    all_probs.append(probs.cpu().numpy())
            
            return np.vstack(all_probs)
        
        return predict
    
    def generate_heatmap(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None,
        normalize: bool = True,
        positive_only: bool = True
    ) -> np.ndarray:
        """Generate LIME heatmap for an image.
        
        Args:
            image: Input image as numpy array (H, W, C) in [0, 255] or [0, 1].
            target_class: Target class index. If None, uses predicted class.
            normalize: Whether to normalize heatmap to [0, 1].
            positive_only: Whether to show only positive contributions.
            
        Returns:
            LIME heatmap as numpy array (H, W) with values in [0, 1].
        """
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        if len(image.shape) == 3 and image.shape[0] == 3:
            image = np.transpose(image, (1, 2, 0))
        
        explanation = self.explainer.explain_instance(
            image,
            self.predict_fn,
            top_labels=5,
            hide_color=0,
            num_samples=self.num_samples,
            random_seed=self.random_seed
        )
        
        if target_class is None:
            target_class = explanation.top_labels[0]
        
        temp, mask = explanation.get_image_and_mask(
            target_class,
            positive_only=positive_only,
            num_features=self.num_features,
            hide_rest=False
        )
        
        heatmap = mask.astype(np.float32)
        
        if normalize and heatmap.max() > 0:
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        
        return heatmap
    
    def generate_superpixel_explanation(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None
    ) -> Tuple[np.ndarray, dict]:
        """Generate detailed superpixel explanation.
        
        Args:
            image: Input image as numpy array.
            target_class: Target class index.
            
        Returns:
            Tuple of (explanation_image, feature_weights).
            explanation_image: Image with superpixel boundaries.
            feature_weights: Dictionary mapping superpixel IDs to weights.
        """
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        if len(image.shape) == 3 and image.shape[0] == 3:
            image = np.transpose(image, (1, 2, 0))
        
        explanation = self.explainer.explain_instance(
            image,
            self.predict_fn,
            top_labels=5,
            hide_color=0,
            num_samples=self.num_samples,
            random_seed=self.random_seed
        )
        
        if target_class is None:
            target_class = explanation.top_labels[0]
        
        temp, mask = explanation.get_image_and_mask(
            target_class,
            positive_only=False,
            num_features=self.num_features,
            hide_rest=False
        )
        
        explanation_image = mark_boundaries(temp / 255.0, mask)
        
        feature_weights = dict(explanation.local_exp[target_class])
        
        return explanation_image, feature_weights
    
    def get_feature_importance(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None
    ) -> dict:
        """Get feature importance scores for superpixels.
        
        Args:
            image: Input image as numpy array.
            target_class: Target class index.
            
        Returns:
            Dictionary mapping superpixel IDs to importance scores.
        """
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        
        if len(image.shape) == 3 and image.shape[0] == 3:
            image = np.transpose(image, (1, 2, 0))
        
        explanation = self.explainer.explain_instance(
            image,
            self.predict_fn,
            top_labels=5,
            hide_color=0,
            num_samples=self.num_samples,
            random_seed=self.random_seed
        )
        
        if target_class is None:
            target_class = explanation.top_labels[0]
        
        return dict(explanation.local_exp[target_class])
    
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
            LIME heatmap.
        """
        return self.generate_heatmap(image, target_class)
    
    def explain(
        self,
        image: np.ndarray,
        target_class: Optional[int] = None,
        num_samples: Optional[int] = None,
        num_features: Optional[int] = None
    ) -> Tuple[np.ndarray, dict]:
        """Generate LIME explanation with overlay visualization.
        
        Args:
            image: Input image (H, W, C) in BGR format.
            target_class: Target class index.
            num_samples: Number of samples (overrides default).
            num_features: Number of features (overrides default).
            
        Returns:
            Tuple of (overlay_image, metadata).
        """
        # Save original settings
        orig_samples = self.num_samples
        orig_features = self.num_features
        
        if num_samples:
            self.num_samples = num_samples
        if num_features:
            self.num_features = num_features
        
        # Generate heatmap
        heatmap = self.generate_heatmap(image, target_class, normalize=True)
        
        # Create overlay
        import cv2
        heatmap_colored = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(image, 0.6, heatmap_colored, 0.4, 0)
        
        # Restore settings
        self.num_samples = orig_samples
        self.num_features = orig_features
        
        metadata = {
            'method': 'lime',
            'num_samples': num_samples or orig_samples,
            'num_features': num_features or orig_features,
            'explanation_score': float(heatmap.max())
        }
        
        return overlay, metadata
    
    def visualize(
        self,
        explanation_data: np.ndarray,
        original_image: np.ndarray
    ) -> np.ndarray:
        """Visualize LIME explanation.
        
        Args:
            explanation_data: Heatmap or attribution data.
            original_image: Original image.
            
        Returns:
            Visualization as BGR image.
        """
        import cv2
        if explanation_data.max() <= 1.0:
            explanation_data = (explanation_data * 255).astype(np.uint8)
        
        heatmap_colored = cv2.applyColorMap(explanation_data, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(original_image, 0.6, heatmap_colored, 0.4, 0)
        return overlay
