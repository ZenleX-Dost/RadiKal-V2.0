"""Model calibration utilities including ECE and temperature scaling.

This module provides functions for assessing and improving model calibration
through Expected Calibration Error (ECE) and temperature scaling.
"""

from typing import Tuple, Optional, List
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn import functional as F
import matplotlib.pyplot as plt


def calculate_ece(
    predictions: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Expected Calibration Error (ECE).
    
    ECE measures the difference between confidence and accuracy across bins.
    
    Args:
        predictions: Model predictions (probabilities) of shape (n_samples, n_classes).
        labels: Ground truth labels of shape (n_samples,).
        n_bins: Number of bins for calibration analysis.
        
    Returns:
        Tuple of (ece, bin_accuracies, bin_confidences, bin_counts).
        ece: Expected Calibration Error score.
        bin_accuracies: Accuracy for each bin.
        bin_confidences: Average confidence for each bin.
        bin_counts: Number of samples in each bin.
    """
    confidences = np.max(predictions, axis=1)
    predicted_labels = np.argmax(predictions, axis=1)
    accuracies = (predicted_labels == labels).astype(np.float32)
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    bin_accuracies = np.zeros(n_bins)
    bin_confidences = np.zeros(n_bins)
    bin_counts = np.zeros(n_bins)
    
    ece = 0.0
    
    for bin_idx, (bin_lower, bin_upper) in enumerate(zip(bin_lowers, bin_uppers)):
        in_bin = np.logical_and(confidences > bin_lower, confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            bin_accuracies[bin_idx] = np.mean(accuracies[in_bin])
            bin_confidences[bin_idx] = np.mean(confidences[in_bin])
            bin_counts[bin_idx] = np.sum(in_bin)
            
            ece += np.abs(bin_accuracies[bin_idx] - bin_confidences[bin_idx]) * prop_in_bin
    
    return ece, bin_accuracies, bin_confidences, bin_counts


def plot_reliability_diagram(
    predictions: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15,
    save_path: Optional[str] = None,
    title: str = "Reliability Diagram"
) -> plt.Figure:
    """Plot reliability diagram for model calibration assessment.
    
    Args:
        predictions: Model predictions (probabilities).
        labels: Ground truth labels.
        n_bins: Number of bins for calibration analysis.
        save_path: Optional path to save the figure.
        title: Title for the plot.
        
    Returns:
        Matplotlib figure object.
    """
    ece, bin_accuracies, bin_confidences, bin_counts = calculate_ece(
        predictions, labels, n_bins
    )
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    ax.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
    
    valid_bins = bin_counts > 0
    ax.bar(
        bin_confidences[valid_bins],
        bin_accuracies[valid_bins],
        width=1.0/n_bins,
        alpha=0.7,
        edgecolor='black',
        label='Model'
    )
    
    ax.set_xlabel('Confidence', fontsize=14)
    ax.set_ylabel('Accuracy', fontsize=14)
    ax.set_title(f'{title}\nECE: {ece:.4f}', fontsize=16)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


class TemperatureScaling(nn.Module):
    """Temperature scaling for model calibration.
    
    Temperature scaling is a simple post-processing technique that learns
    a single temperature parameter to calibrate model outputs.
    """
    
    def __init__(self, initial_temperature: float = 1.5):
        """Initialize temperature scaling.
        
        Args:
            initial_temperature: Initial temperature value.
        """
        super(TemperatureScaling, self).__init__()
        self.temperature = nn.Parameter(torch.ones(1) * initial_temperature)
    
    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply temperature scaling to logits.
        
        Args:
            logits: Model logits (before softmax).
            
        Returns:
            Temperature-scaled logits.
        """
        return logits / self.temperature
    
    def fit(
        self,
        logits: torch.Tensor,
        labels: torch.Tensor,
        lr: float = 0.01,
        max_iter: int = 50
    ) -> float:
        """Fit temperature parameter using validation set.
        
        Args:
            logits: Model logits on validation set.
            labels: Ground truth labels for validation set.
            lr: Learning rate for optimization.
            max_iter: Maximum number of optimization iterations.
            
        Returns:
            Optimal temperature value.
        """
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)
        
        def eval_loss():
            optimizer.zero_grad()
            loss = nll_criterion(self.forward(logits), labels)
            loss.backward()
            return loss
        
        optimizer.step(eval_loss)
        
        return self.temperature.item()
    
    def get_temperature(self) -> float:
        """Get current temperature value.
        
        Returns:
            Temperature value.
        """
        return self.temperature.item()


def temperature_scaling(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: str = 'cpu'
) -> Tuple[TemperatureScaling, float]:
    """Apply temperature scaling to a model using validation data.
    
    Args:
        model: PyTorch model to calibrate.
        val_loader: DataLoader with validation data.
        device: Device to run calibration on.
        
    Returns:
        Tuple of (temperature_scaling_module, optimal_temperature).
    """
    model.eval()
    
    logits_list = []
    labels_list = []
    
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            
            if isinstance(outputs, dict):
                logits = outputs.get('logits', outputs.get('scores', outputs.get('pred', None)))
            else:
                logits = outputs
            
            if logits is None:
                raise ValueError("Cannot extract logits from model output")
            
            logits_list.append(logits)
            labels_list.append(labels)
    
    all_logits = torch.cat(logits_list)
    all_labels = torch.cat(labels_list)
    
    temp_scaling = TemperatureScaling()
    temp_scaling.to(device)
    all_logits = all_logits.to(device)
    all_labels = all_labels.to(device)
    
    optimal_temp = temp_scaling.fit(all_logits, all_labels)
    
    return temp_scaling, optimal_temp


def evaluate_calibration(
    predictions: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 15
) -> dict:
    """Evaluate model calibration with multiple metrics.
    
    Args:
        predictions: Model predictions (probabilities).
        labels: Ground truth labels.
        n_bins: Number of bins for calibration analysis.
        
    Returns:
        Dictionary containing calibration metrics.
    """
    ece, bin_accuracies, bin_confidences, bin_counts = calculate_ece(
        predictions, labels, n_bins
    )
    
    confidences = np.max(predictions, axis=1)
    predicted_labels = np.argmax(predictions, axis=1)
    accuracies = (predicted_labels == labels).astype(np.float32)
    
    mce = np.max(np.abs(bin_accuracies - bin_confidences))
    
    avg_confidence = np.mean(confidences)
    avg_accuracy = np.mean(accuracies)
    
    return {
        'ece': float(ece),
        'mce': float(mce),
        'avg_confidence': float(avg_confidence),
        'avg_accuracy': float(avg_accuracy),
        'bin_accuracies': bin_accuracies.tolist(),
        'bin_confidences': bin_confidences.tolist(),
        'bin_counts': bin_counts.tolist()
    }
