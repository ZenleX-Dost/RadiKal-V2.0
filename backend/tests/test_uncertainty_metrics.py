"""
Unit tests for uncertainty quantification and metrics modules.

Tests for MC-Dropout, calibration, and all metrics calculators.

Author: RadiKal Team
Date: 2025-10-14
"""

import pytest
import torch
import numpy as np
from sklearn.metrics import accuracy_score

from core.uncertainty.mc_dropout import MCDropoutEstimator, mc_dropout_predict
from core.uncertainty.calibration import (
    calculate_ece,
    TemperatureScaling,
    plot_reliability_diagram
)
from core.metrics.business_metrics import (
    calculate_confusion_matrix_metrics,
    get_business_metrics_report
)
from core.metrics.detection_metrics import (
    calculate_map,
    calculate_auroc,
    calculate_iou
)
from core.metrics.segmentation_metrics import (
    calculate_mean_iou,
    calculate_dice_score
)


class TestMCDropout:
    """Tests for MC-Dropout uncertainty estimation."""
    
    @pytest.fixture
    def simple_model(self):
        """Create a simple model with dropout."""
        class SimpleModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.conv = torch.nn.Conv2d(3, 16, 3, padding=1)
                self.dropout = torch.nn.Dropout2d(0.5)
                self.fc = torch.nn.Linear(16 * 512 * 512, 2)
            
            def forward(self, x):
                x = self.conv(x)
                x = self.dropout(x)
                x = x.flatten(1)
                x = self.fc(x)
                return x
        
        return SimpleModel()
    
    def test_mc_dropout_estimator_init(self, simple_model):
        """Test MCDropoutEstimator initialization."""
        estimator = MCDropoutEstimator(simple_model, n_samples=10, device='cpu')
        
        assert estimator.model is not None
        assert estimator.n_samples == 10
        assert estimator.device == 'cpu'
    
    def test_compute_predictive_entropy(self, simple_model):
        """Test predictive entropy computation."""
        estimator = MCDropoutEstimator(simple_model, n_samples=5, device='cpu')
        
        # Create sample input
        x = torch.randn(1, 3, 512, 512)
        
        # Compute entropy
        entropy = estimator.compute_predictive_entropy(x)
        
        assert isinstance(entropy, np.ndarray)
        assert entropy.shape == (512, 512)
        assert (entropy >= 0).all()


class TestCalibration:
    """Tests for model calibration."""
    
    def test_calculate_ece(self):
        """Test ECE calculation."""
        # Create synthetic predictions
        confidences = torch.tensor([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        predictions = torch.tensor([1, 1, 1, 1, 0, 0, 0, 0, 0])
        labels = torch.tensor([1, 1, 0, 1, 0, 1, 0, 0, 0])
        
        ece = calculate_ece(confidences, predictions, labels, n_bins=3)
        
        assert isinstance(ece, float)
        assert 0.0 <= ece <= 1.0
    
    def test_temperature_scaling_init(self):
        """Test TemperatureScaling initialization."""
        scaler = TemperatureScaling()
        
        assert scaler.temperature is not None
        assert scaler.temperature.requires_grad
    
    def test_temperature_scaling_forward(self):
        """Test temperature scaling forward pass."""
        scaler = TemperatureScaling()
        
        logits = torch.randn(10, 2)
        scaled_logits = scaler(logits)
        
        assert scaled_logits.shape == logits.shape
    
    def test_plot_reliability_diagram(self):
        """Test reliability diagram plotting."""
        confidences = torch.rand(100)
        predictions = (confidences > 0.5).long()
        labels = torch.randint(0, 2, (100,))
        
        fig = plot_reliability_diagram(confidences, predictions, labels, n_bins=10)
        
        assert fig is not None


class TestBusinessMetrics:
    """Tests for business metrics."""
    
    def test_calculate_confusion_matrix_metrics(self):
        """Test confusion matrix metrics calculation."""
        predictions = np.array([1, 1, 0, 1, 0, 0, 1, 0])
        labels = np.array([1, 0, 0, 1, 0, 1, 1, 0])
        
        metrics = calculate_confusion_matrix_metrics(predictions, labels)
        
        assert 'true_positives' in metrics
        assert 'false_positives' in metrics
        assert 'true_negatives' in metrics
        assert 'false_negatives' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        
        # Verify ranges
        assert 0.0 <= metrics['precision'] <= 1.0
        assert 0.0 <= metrics['recall'] <= 1.0
        assert 0.0 <= metrics['f1_score'] <= 1.0
    
    def test_get_business_metrics_report(self):
        """Test business metrics report generation."""
        predictions = np.array([1, 1, 0, 1, 0])
        labels = np.array([1, 0, 0, 1, 0])
        
        report = get_business_metrics_report(predictions, labels)
        
        assert isinstance(report, dict)
        assert len(report) > 0


class TestDetectionMetrics:
    """Tests for detection metrics."""
    
    def test_calculate_iou(self):
        """Test IoU calculation."""
        box1 = [10, 10, 50, 50]  # x1, y1, x2, y2
        box2 = [20, 20, 60, 60]
        
        iou = calculate_iou(box1, box2)
        
        assert isinstance(iou, float)
        assert 0.0 <= iou <= 1.0
    
    def test_calculate_iou_no_overlap(self):
        """Test IoU with no overlap."""
        box1 = [0, 0, 10, 10]
        box2 = [20, 20, 30, 30]
        
        iou = calculate_iou(box1, box2)
        
        assert iou == 0.0
    
    def test_calculate_iou_perfect_overlap(self):
        """Test IoU with perfect overlap."""
        box1 = [10, 10, 50, 50]
        box2 = [10, 10, 50, 50]
        
        iou = calculate_iou(box1, box2)
        
        assert iou == 1.0
    
    def test_calculate_map(self):
        """Test mAP calculation."""
        predictions = [
            {
                'boxes': [[10, 10, 50, 50], [60, 60, 100, 100]],
                'scores': [0.9, 0.8],
                'labels': [1, 1],
            }
        ]
        
        ground_truth = [
            {
                'boxes': [[12, 12, 48, 48], [65, 65, 95, 95]],
                'labels': [1, 1],
            }
        ]
        
        map_score = calculate_map(predictions, ground_truth, iou_threshold=0.5)
        
        assert isinstance(map_score, float)
        assert 0.0 <= map_score <= 1.0
    
    def test_calculate_auroc(self):
        """Test AUROC calculation."""
        scores = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
        labels = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0])
        
        auroc = calculate_auroc(scores, labels)
        
        assert isinstance(auroc, float)
        assert 0.0 <= auroc <= 1.0


class TestSegmentationMetrics:
    """Tests for segmentation metrics."""
    
    def test_calculate_mean_iou(self):
        """Test mean IoU calculation."""
        predictions = np.random.randint(0, 2, (5, 512, 512))
        ground_truth = np.random.randint(0, 2, (5, 512, 512))
        
        mean_iou = calculate_mean_iou(predictions, ground_truth, num_classes=2)
        
        assert isinstance(mean_iou, float)
        assert 0.0 <= mean_iou <= 1.0
    
    def test_calculate_dice_score(self):
        """Test Dice score calculation."""
        pred_mask = np.random.randint(0, 2, (512, 512))
        gt_mask = np.random.randint(0, 2, (512, 512))
        
        dice = calculate_dice_score(pred_mask, gt_mask)
        
        assert isinstance(dice, float)
        assert 0.0 <= dice <= 1.0
    
    def test_dice_score_perfect_match(self):
        """Test Dice score with perfect match."""
        mask = np.random.randint(0, 2, (512, 512))
        
        dice = calculate_dice_score(mask, mask)
        
        assert dice == 1.0
    
    def test_dice_score_no_overlap(self):
        """Test Dice score with no overlap."""
        pred_mask = np.zeros((512, 512))
        gt_mask = np.ones((512, 512))
        
        dice = calculate_dice_score(pred_mask, gt_mask)
        
        assert dice == 0.0


class TestMetricsIntegration:
    """Integration tests for metrics workflow."""
    
    def test_full_metrics_pipeline(self):
        """Test complete metrics calculation pipeline."""
        # Generate synthetic detection results
        predictions = np.array([1, 1, 0, 1, 0, 0, 1, 0, 1, 0])
        labels = np.array([1, 0, 0, 1, 0, 1, 1, 0, 0, 0])
        
        # Business metrics
        business_metrics = calculate_confusion_matrix_metrics(predictions, labels)
        
        # Detection metrics
        confidences = np.random.rand(len(predictions))
        auroc = calculate_auroc(confidences, labels)
        
        # Segmentation metrics
        pred_masks = np.random.randint(0, 2, (10, 64, 64))
        gt_masks = np.random.randint(0, 2, (10, 64, 64))
        mean_iou = calculate_mean_iou(pred_masks, gt_masks, num_classes=2)
        
        # Verify all metrics are calculated
        assert business_metrics is not None
        assert auroc is not None
        assert mean_iou is not None
        
        # Create comprehensive metrics report
        full_report = {
            **business_metrics,
            'auroc': auroc,
            'mean_iou': mean_iou,
        }
        
        assert len(full_report) >= 8  # At least 8 metrics
        assert all(isinstance(v, (int, float)) for v in full_report.values())
    
    def test_edge_cases(self):
        """Test metrics with edge cases."""
        # Empty predictions
        empty_pred = np.array([])
        empty_gt = np.array([])
        
        # All zeros
        zeros_pred = np.zeros(10)
        zeros_gt = np.zeros(10)
        
        # All ones
        ones_pred = np.ones(10)
        ones_gt = np.ones(10)
        
        # Test that functions handle edge cases gracefully
        # (may raise errors or return special values)
        
        # Perfect predictions
        perfect = calculate_confusion_matrix_metrics(ones_gt, ones_gt)
        assert perfect['accuracy'] == 1.0
