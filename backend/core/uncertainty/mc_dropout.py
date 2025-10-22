"""MC-Dropout implementation for uncertainty quantification.

This module implements Monte Carlo Dropout for estimating model uncertainty
through multiple stochastic forward passes.
"""

from typing import Tuple, Optional, List
import numpy as np
import torch
import torch.nn as nn


def enable_dropout(model: nn.Module) -> None:
    """Enable dropout layers in a model for inference.
    
    Args:
        model: PyTorch model to modify.
    """
    for module in model.modules():
        if isinstance(module, nn.Dropout) or isinstance(module, nn.Dropout2d):
            module.train()


def disable_dropout(model: nn.Module) -> None:
    """Disable dropout layers in a model for inference.
    
    Args:
        model: PyTorch model to modify.
    """
    for module in model.modules():
        if isinstance(module, nn.Dropout) or isinstance(module, nn.Dropout2d):
            module.eval()


def mc_dropout_predict(
    model: nn.Module,
    image: torch.Tensor,
    n_samples: int = 30,
    return_all: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """Perform MC-Dropout prediction for uncertainty estimation.
    
    Args:
        model: PyTorch model with dropout layers.
        image: Input image tensor of shape (1, C, H, W) or (C, H, W).
        n_samples: Number of stochastic forward passes.
        return_all: If True, returns all predictions; otherwise returns mean and variance.
        
    Returns:
        Tuple of (mean_prediction, variance) or (all_predictions, None) if return_all=True.
        mean_prediction: Mean prediction across samples.
        variance: Variance of predictions (uncertainty estimate).
    """
    if len(image.shape) == 3:
        image = image.unsqueeze(0)
    
    model.eval()
    enable_dropout(model)
    
    predictions = []
    
    with torch.no_grad():
        for _ in range(n_samples):
            output = model(image)
            
            if isinstance(output, dict):
                pred = output.get('scores', output.get('logits', output.get('pred', None)))
            else:
                pred = output
            
            if pred is None:
                raise ValueError("Cannot extract predictions from model output")
            
            predictions.append(pred.cpu().numpy())
    
    disable_dropout(model)
    
    predictions = np.array(predictions)
    
    if return_all:
        return predictions, None
    
    mean_prediction = np.mean(predictions, axis=0)
    variance = np.var(predictions, axis=0)
    
    return mean_prediction, variance


def compute_predictive_entropy(
    predictions: np.ndarray,
    epsilon: float = 1e-10
) -> np.ndarray:
    """Compute predictive entropy from MC-Dropout samples.
    
    Predictive entropy measures the total uncertainty in predictions.
    
    Args:
        predictions: Array of shape (n_samples, batch_size, n_classes).
        epsilon: Small constant for numerical stability.
        
    Returns:
        Predictive entropy array of shape (batch_size,).
    """
    mean_probs = np.mean(predictions, axis=0)
    
    mean_probs = np.clip(mean_probs, epsilon, 1.0 - epsilon)
    
    entropy = -np.sum(mean_probs * np.log(mean_probs), axis=-1)
    
    return entropy


def compute_mutual_information(
    predictions: np.ndarray,
    epsilon: float = 1e-10
) -> np.ndarray:
    """Compute mutual information from MC-Dropout samples.
    
    Mutual information measures the model uncertainty (epistemic uncertainty).
    
    Args:
        predictions: Array of shape (n_samples, batch_size, n_classes).
        epsilon: Small constant for numerical stability.
        
    Returns:
        Mutual information array of shape (batch_size,).
    """
    predictive_entropy = compute_predictive_entropy(predictions, epsilon)
    
    predictions = np.clip(predictions, epsilon, 1.0 - epsilon)
    sample_entropies = -np.sum(predictions * np.log(predictions), axis=-1)
    expected_entropy = np.mean(sample_entropies, axis=0)
    
    mutual_info = predictive_entropy - expected_entropy
    
    return mutual_info


class MCDropoutEstimator:
    """MC-Dropout estimator for uncertainty quantification.
    
    This class provides a high-level interface for uncertainty estimation
    using Monte Carlo Dropout.
    """
    
    def __init__(
        self,
        model: nn.Module,
        n_samples: int = 30,
        device: Optional[str] = None
    ):
        """Initialize MC-Dropout estimator.
        
        Args:
            model: PyTorch model with dropout layers.
            n_samples: Number of stochastic forward passes.
            device: Device to run inference on.
        """
        self.model = model
        self.n_samples = n_samples
        
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.model.to(self.device)
    
    def predict_with_uncertainty(
        self,
        image: torch.Tensor
    ) -> dict:
        """Predict with uncertainty estimates.
        
        Args:
            image: Input image tensor.
            
        Returns:
            Dictionary containing:
                - mean_prediction: Mean prediction
                - variance: Prediction variance
                - std: Standard deviation
                - predictive_entropy: Total uncertainty
                - mutual_information: Model uncertainty
        """
        image = image.to(self.device)
        
        mean_pred, variance = mc_dropout_predict(
            self.model,
            image,
            n_samples=self.n_samples,
            return_all=False
        )
        
        all_predictions, _ = mc_dropout_predict(
            self.model,
            image,
            n_samples=self.n_samples,
            return_all=True
        )
        
        pred_entropy = compute_predictive_entropy(all_predictions)
        mutual_info = compute_mutual_information(all_predictions)
        
        return {
            'mean_prediction': mean_pred,
            'variance': variance,
            'std': np.sqrt(variance),
            'predictive_entropy': pred_entropy,
            'mutual_information': mutual_info
        }
    
    def get_confidence_interval(
        self,
        image: torch.Tensor,
        confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute confidence interval for predictions.
        
        Args:
            image: Input image tensor.
            confidence: Confidence level (default 0.95 for 95% CI).
            
        Returns:
            Tuple of (lower_bound, upper_bound) arrays.
        """
        image = image.to(self.device)
        
        all_predictions, _ = mc_dropout_predict(
            self.model,
            image,
            n_samples=self.n_samples,
            return_all=True
        )
        
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        lower_bound = np.percentile(all_predictions, lower_percentile, axis=0)
        upper_bound = np.percentile(all_predictions, upper_percentile, axis=0)
        
        return lower_bound, upper_bound
