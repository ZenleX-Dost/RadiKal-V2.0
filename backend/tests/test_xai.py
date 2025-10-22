"""
Unit tests for XAI modules.

Tests for Grad-CAM, SHAP, LIME, Integrated Gradients, and Aggregator.

Author: RadiKal Team
Date: 2025-10-14
"""

import pytest
import torch
import numpy as np
from torchvision.models.detection import fasterrcnn_resnet50_fpn

from core.xai.gradcam import GradCAM
from core.xai.shap_explainer import SHAPExplainer
from core.xai.lime_explainer import LIMEExplainer
from core.xai.integrated_gradients import IntegratedGradientsExplainer
from core.xai.aggregator import XAIAggregator


@pytest.fixture
def sample_model():
    """Create a sample Faster R-CNN model."""
    model = fasterrcnn_resnet50_fpn(weights=None, num_classes=2)
    model.eval()
    return model


@pytest.fixture
def sample_image():
    """Create a sample image tensor."""
    return torch.randn(1, 3, 512, 512)


class TestGradCAM:
    """Tests for Grad-CAM explainer."""
    
    def test_initialization(self, sample_model):
        """Test GradCAM initialization."""
        gradcam = GradCAM(sample_model)
        assert gradcam.model is not None
        assert gradcam.target_layer is not None
    
    def test_generate_heatmap(self, sample_model, sample_image):
        """Test heatmap generation."""
        gradcam = GradCAM(sample_model)
        heatmap = gradcam.generate_heatmap(sample_image, target_class=1)
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
    
    def test_generate_overlay(self, sample_model, sample_image):
        """Test overlay generation."""
        gradcam = GradCAM(sample_model)
        
        original_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        overlay = gradcam.generate_overlay(sample_image, original_image, target_class=1)
        
        assert isinstance(overlay, np.ndarray)
        assert overlay.shape == (512, 512, 3)


class TestSHAPExplainer:
    """Tests for SHAP explainer."""
    
    def test_initialization(self, sample_model):
        """Test SHAP explainer initialization."""
        explainer = SHAPExplainer(sample_model)
        assert explainer.model is not None
    
    def test_generate_heatmap(self, sample_model, sample_image):
        """Test SHAP heatmap generation."""
        explainer = SHAPExplainer(sample_model)
        heatmap = explainer.generate_heatmap(sample_image, target_class=1)
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0


class TestLIMEExplainer:
    """Tests for LIME explainer."""
    
    def test_initialization(self, sample_model):
        """Test LIME explainer initialization."""
        explainer = LIMEExplainer(sample_model)
        assert explainer.model is not None
        assert explainer.random_seed == 42
    
    def test_generate_heatmap(self, sample_model, sample_image):
        """Test LIME heatmap generation."""
        explainer = LIMEExplainer(sample_model)
        heatmap = explainer.generate_heatmap(sample_image, target_class=1)
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
    
    def test_deterministic_results(self, sample_model, sample_image):
        """Test that LIME produces deterministic results with fixed seed."""
        explainer = LIMEExplainer(sample_model, random_seed=42)
        
        heatmap1 = explainer.generate_heatmap(sample_image, target_class=1)
        heatmap2 = explainer.generate_heatmap(sample_image, target_class=1)
        
        # Results should be very similar (not exactly same due to LIME's stochastic nature)
        correlation = np.corrcoef(heatmap1.flatten(), heatmap2.flatten())[0, 1]
        assert correlation > 0.8


class TestIntegratedGradientsExplainer:
    """Tests for Integrated Gradients explainer."""
    
    def test_initialization(self, sample_model):
        """Test IG explainer initialization."""
        explainer = IntegratedGradientsExplainer(sample_model)
        assert explainer.model is not None
    
    def test_generate_heatmap_black_baseline(self, sample_model, sample_image):
        """Test IG with black baseline."""
        explainer = IntegratedGradientsExplainer(sample_model)
        heatmap = explainer.generate_heatmap(sample_image, target_class=1, baseline='black')
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
    
    def test_generate_heatmap_white_baseline(self, sample_model, sample_image):
        """Test IG with white baseline."""
        explainer = IntegratedGradientsExplainer(sample_model)
        heatmap = explainer.generate_heatmap(sample_image, target_class=1, baseline='white')
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)
    
    def test_generate_heatmap_blur_baseline(self, sample_model, sample_image):
        """Test IG with blur baseline."""
        explainer = IntegratedGradientsExplainer(sample_model)
        heatmap = explainer.generate_heatmap(sample_image, target_class=1, baseline='blur')
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)
    
    def test_generate_heatmap_random_baseline(self, sample_model, sample_image):
        """Test IG with random baseline."""
        explainer = IntegratedGradientsExplainer(sample_model)
        heatmap = explainer.generate_heatmap(sample_image, target_class=1, baseline='random')
        
        assert isinstance(heatmap, np.ndarray)
        assert heatmap.shape == (512, 512)


class TestXAIAggregator:
    """Tests for XAI aggregator."""
    
    def test_initialization(self):
        """Test aggregator initialization."""
        aggregator = XAIAggregator()
        assert aggregator is not None
    
    def test_aggregate_mean(self):
        """Test mean aggregation."""
        aggregator = XAIAggregator()
        
        heatmaps = [
            np.random.rand(512, 512),
            np.random.rand(512, 512),
            np.random.rand(512, 512),
        ]
        
        aggregated = aggregator.aggregate(heatmaps, method='mean')
        
        assert isinstance(aggregated, np.ndarray)
        assert aggregated.shape == (512, 512)
        assert aggregated.min() >= 0.0
        assert aggregated.max() <= 1.0
    
    def test_aggregate_median(self):
        """Test median aggregation."""
        aggregator = XAIAggregator()
        
        heatmaps = [
            np.random.rand(512, 512),
            np.random.rand(512, 512),
            np.random.rand(512, 512),
        ]
        
        aggregated = aggregator.aggregate(heatmaps, method='median')
        
        assert isinstance(aggregated, np.ndarray)
        assert aggregated.shape == (512, 512)
    
    def test_aggregate_weighted(self):
        """Test weighted aggregation."""
        aggregator = XAIAggregator()
        
        heatmaps = [
            np.random.rand(512, 512),
            np.random.rand(512, 512),
            np.random.rand(512, 512),
        ]
        weights = [0.5, 0.3, 0.2]
        
        aggregated = aggregator.aggregate(heatmaps, method='weighted', weights=weights)
        
        assert isinstance(aggregated, np.ndarray)
        assert aggregated.shape == (512, 512)
    
    def test_compute_consensus_correlation(self):
        """Test consensus score with correlation metric."""
        aggregator = XAIAggregator()
        
        heatmaps = [
            np.random.rand(512, 512),
            np.random.rand(512, 512),
        ]
        
        score = aggregator.compute_consensus_score(heatmaps, metric='correlation')
        
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0
    
    def test_compute_consensus_iou(self):
        """Test consensus score with IoU metric."""
        aggregator = XAIAggregator()
        
        # Create binary heatmaps for IoU
        heatmaps = [
            (np.random.rand(512, 512) > 0.5).astype(float),
            (np.random.rand(512, 512) > 0.5).astype(float),
        ]
        
        score = aggregator.compute_consensus_score(heatmaps, metric='iou')
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_compute_consensus_dice(self):
        """Test consensus score with Dice metric."""
        aggregator = XAIAggregator()
        
        # Create binary heatmaps for Dice
        heatmaps = [
            (np.random.rand(512, 512) > 0.5).astype(float),
            (np.random.rand(512, 512) > 0.5).astype(float),
        ]
        
        score = aggregator.compute_consensus_score(heatmaps, metric='dice')
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_mismatched_shapes_raises_error(self):
        """Test that mismatched shapes raise an error."""
        aggregator = XAIAggregator()
        
        heatmaps = [
            np.random.rand(512, 512),
            np.random.rand(256, 256),  # Different shape
        ]
        
        with pytest.raises(ValueError):
            aggregator.aggregate(heatmaps, method='mean')
    
    def test_invalid_weights_raises_error(self):
        """Test that invalid weights raise an error."""
        aggregator = XAIAggregator()
        
        heatmaps = [
            np.random.rand(512, 512),
            np.random.rand(512, 512),
        ]
        weights = [0.5]  # Wrong number of weights
        
        with pytest.raises(ValueError):
            aggregator.aggregate(heatmaps, method='weighted', weights=weights)


class TestXAIIntegration:
    """Integration tests for XAI workflow."""
    
    def test_all_explainers_produce_valid_output(self, sample_model, sample_image):
        """Test that all explainers produce valid heatmaps."""
        explainers = {
            'gradcam': GradCAM(sample_model),
            'shap': SHAPExplainer(sample_model),
            'lime': LIMEExplainer(sample_model),
            'ig': IntegratedGradientsExplainer(sample_model),
        }
        
        for name, explainer in explainers.items():
            heatmap = explainer.generate_heatmap(sample_image, target_class=1)
            
            assert isinstance(heatmap, np.ndarray), f"{name} failed"
            assert heatmap.shape == (512, 512), f"{name} failed"
            assert heatmap.min() >= 0.0, f"{name} failed"
            assert heatmap.max() <= 1.0, f"{name} failed"
    
    def test_full_xai_pipeline(self, sample_model, sample_image):
        """Test the complete XAI pipeline."""
        # Generate explanations from all methods
        explainers = {
            'gradcam': GradCAM(sample_model),
            'shap': SHAPExplainer(sample_model),
            'lime': LIMEExplainer(sample_model),
            'ig': IntegratedGradientsExplainer(sample_model),
        }
        
        heatmaps = []
        for explainer in explainers.values():
            heatmap = explainer.generate_heatmap(sample_image, target_class=1)
            heatmaps.append(heatmap)
        
        # Aggregate explanations
        aggregator = XAIAggregator()
        aggregated = aggregator.aggregate(heatmaps, method='mean')
        
        # Compute consensus
        consensus = aggregator.compute_consensus_score(heatmaps, metric='correlation')
        
        # Verify results
        assert isinstance(aggregated, np.ndarray)
        assert isinstance(consensus, float)
        assert aggregated.shape == (512, 512)
        assert -1.0 <= consensus <= 1.0
