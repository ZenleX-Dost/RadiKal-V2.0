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
        def predict(images):
            batch = []
            for img in images:
                if len(img.shape) == 3:
                    img = np.transpose(img, (2, 0, 1))
                batch.append(img)
            
            batch = np.array(batch)
            batch_tensor = torch.from_numpy(batch).float()
            
            with torch.no_grad():
                output = model(batch_tensor)
                
                if isinstance(output, dict):
                    logits = output.get('scores', output.get('logits', output.get('pred', None)))
                else:
                    logits = output
                
                if logits is None:
                    raise ValueError("Cannot extract logits from model output")
                
                probs = torch.softmax(logits, dim=-1)
                return probs.cpu().numpy()
        
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
