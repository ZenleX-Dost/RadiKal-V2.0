"""Aggregator for combining multiple XAI explanations.

This module provides functionality to combine and aggregate explanations
from multiple XAI methods (Grad-CAM, SHAP, LIME, Integrated Gradients).
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from enum import Enum


class AggregationMethod(Enum):
    """Enumeration of aggregation methods."""
    MEAN = "mean"
    MEDIAN = "median"
    MAX = "max"
    MIN = "min"
    WEIGHTED_MEAN = "weighted_mean"


class XAIAggregator:
    """Aggregator for combining multiple XAI explanations.
    
    This class combines heatmaps from different XAI methods to produce
    a consensus explanation and compute agreement scores.
    """
    
    def __init__(
        self,
        method: AggregationMethod = AggregationMethod.MEAN,
        weights: Optional[Dict[str, float]] = None
    ):
        """Initialize XAI aggregator.
        
        Args:
            method: Aggregation method to use.
            weights: Dictionary mapping method names to weights.
                    Required if method is WEIGHTED_MEAN.
        """
        self.method = method
        self.weights = weights or {}
        
        if method == AggregationMethod.WEIGHTED_MEAN and not weights:
            raise ValueError("Weights must be provided for weighted_mean aggregation")
    
    def aggregate(
        self,
        heatmaps: Dict[str, np.ndarray],
        normalize: bool = True
    ) -> np.ndarray:
        """Aggregate multiple heatmaps into a single consensus heatmap.
        
        Args:
            heatmaps: Dictionary mapping method names to heatmaps.
                     All heatmaps must have the same shape.
            normalize: Whether to normalize the aggregated heatmap to [0, 1].
            
        Returns:
            Aggregated heatmap as numpy array.
            
        Raises:
            ValueError: If heatmaps have inconsistent shapes or no heatmaps provided.
        """
        if not heatmaps:
            raise ValueError("No heatmaps provided for aggregation")
        
        shapes = [h.shape for h in heatmaps.values()]
        if len(set(shapes)) > 1:
            raise ValueError(f"Inconsistent heatmap shapes: {shapes}")
        
        heatmap_list = []
        for name, heatmap in heatmaps.items():
            h_normalized = self._normalize_heatmap(heatmap)
            heatmap_list.append(h_normalized)
        
        heatmap_array = np.stack(heatmap_list, axis=0)
        
        if self.method == AggregationMethod.MEAN:
            aggregated = np.mean(heatmap_array, axis=0)
        elif self.method == AggregationMethod.MEDIAN:
            aggregated = np.median(heatmap_array, axis=0)
        elif self.method == AggregationMethod.MAX:
            aggregated = np.max(heatmap_array, axis=0)
        elif self.method == AggregationMethod.MIN:
            aggregated = np.min(heatmap_array, axis=0)
        elif self.method == AggregationMethod.WEIGHTED_MEAN:
            weight_array = np.array([
                self.weights.get(name, 1.0) for name in heatmaps.keys()
            ])
            weight_array = weight_array / weight_array.sum()
            aggregated = np.average(
                heatmap_array,
                axis=0,
                weights=weight_array
            )
        else:
            raise ValueError(f"Unknown aggregation method: {self.method}")
        
        if normalize:
            aggregated = self._normalize_heatmap(aggregated)
        
        return aggregated
    
    def compute_consensus_score(
        self,
        heatmaps: Dict[str, np.ndarray],
        method: str = 'correlation'
    ) -> float:
        """Compute consensus score across multiple heatmaps.
        
        Args:
            heatmaps: Dictionary mapping method names to heatmaps.
            method: Consensus metric ('correlation', 'iou', 'dice').
            
        Returns:
            Consensus score in [0, 1] where higher is better agreement.
        """
        if len(heatmaps) < 2:
            return 1.0
        
        heatmap_list = [self._normalize_heatmap(h) for h in heatmaps.values()]
        
        if method == 'correlation':
            score = self._compute_pairwise_correlation(heatmap_list)
        elif method == 'iou':
            score = self._compute_pairwise_iou(heatmap_list)
        elif method == 'dice':
            score = self._compute_pairwise_dice(heatmap_list)
        else:
            raise ValueError(f"Unknown consensus method: {method}")
        
        return score
    
    def _normalize_heatmap(self, heatmap: np.ndarray) -> np.ndarray:
        """Normalize heatmap to [0, 1] range.
        
        Args:
            heatmap: Input heatmap.
            
        Returns:
            Normalized heatmap.
        """
        if heatmap.max() == heatmap.min():
            return np.zeros_like(heatmap)
        return (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
    
    def _compute_pairwise_correlation(
        self,
        heatmaps: List[np.ndarray]
    ) -> float:
        """Compute average pairwise correlation between heatmaps.
        
        Args:
            heatmaps: List of normalized heatmaps.
            
        Returns:
            Average correlation coefficient.
        """
        n = len(heatmaps)
        correlations = []
        
        for i in range(n):
            for j in range(i + 1, n):
                h1_flat = heatmaps[i].flatten()
                h2_flat = heatmaps[j].flatten()
                
                corr = np.corrcoef(h1_flat, h2_flat)[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
        
        if not correlations:
            return 0.0
        
        return float(np.mean(correlations))
    
    def _compute_pairwise_iou(
        self,
        heatmaps: List[np.ndarray],
        threshold: float = 0.5
    ) -> float:
        """Compute average pairwise IoU between binarized heatmaps.
        
        Args:
            heatmaps: List of normalized heatmaps.
            threshold: Threshold for binarization.
            
        Returns:
            Average IoU score.
        """
        n = len(heatmaps)
        ious = []
        
        binary_maps = [h > threshold for h in heatmaps]
        
        for i in range(n):
            for j in range(i + 1, n):
                intersection = np.logical_and(binary_maps[i], binary_maps[j]).sum()
                union = np.logical_or(binary_maps[i], binary_maps[j]).sum()
                
                if union > 0:
                    iou = intersection / union
                    ious.append(iou)
        
        if not ious:
            return 0.0
        
        return float(np.mean(ious))
    
    def _compute_pairwise_dice(
        self,
        heatmaps: List[np.ndarray],
        threshold: float = 0.5
    ) -> float:
        """Compute average pairwise Dice coefficient between binarized heatmaps.
        
        Args:
            heatmaps: List of normalized heatmaps.
            threshold: Threshold for binarization.
            
        Returns:
            Average Dice coefficient.
        """
        n = len(heatmaps)
        dice_scores = []
        
        binary_maps = [h > threshold for h in heatmaps]
        
        for i in range(n):
            for j in range(i + 1, n):
                intersection = np.logical_and(binary_maps[i], binary_maps[j]).sum()
                sum_areas = binary_maps[i].sum() + binary_maps[j].sum()
                
                if sum_areas > 0:
                    dice = (2.0 * intersection) / sum_areas
                    dice_scores.append(dice)
        
        if not dice_scores:
            return 0.0
        
        return float(np.mean(dice_scores))
    
    def get_explanation_rankings(
        self,
        heatmaps: Dict[str, np.ndarray],
        top_k: int = 10
    ) -> Dict[str, List[Tuple[int, int, float]]]:
        """Get top-k most important pixels for each explanation method.
        
        Args:
            heatmaps: Dictionary mapping method names to heatmaps.
            top_k: Number of top pixels to return.
            
        Returns:
            Dictionary mapping method names to lists of (row, col, value) tuples.
        """
        rankings = {}
        
        for name, heatmap in heatmaps.items():
            normalized = self._normalize_heatmap(heatmap)
            flat_indices = np.argsort(normalized.flatten())[-top_k:][::-1]
            
            rows, cols = np.unravel_index(flat_indices, normalized.shape)
            values = normalized[rows, cols]
            
            rankings[name] = [(int(r), int(c), float(v)) for r, c, v in zip(rows, cols, values)]
        
        return rankings
    
    def compare_methods(
        self,
        heatmaps: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, float]]:
        """Compare XAI methods pairwise.
        
        Args:
            heatmaps: Dictionary mapping method names to heatmaps.
            
        Returns:
            Dictionary containing pairwise comparison metrics.
        """
        methods = list(heatmaps.keys())
        n = len(methods)
        
        comparison = {
            'correlation': {},
            'iou': {},
            'dice': {}
        }
        
        for i in range(n):
            for j in range(i + 1, n):
                name_i, name_j = methods[i], methods[j]
                pair_key = f"{name_i}_vs_{name_j}"
                
                h1 = self._normalize_heatmap(heatmaps[name_i])
                h2 = self._normalize_heatmap(heatmaps[name_j])
                
                h1_flat = h1.flatten()
                h2_flat = h2.flatten()
                corr = np.corrcoef(h1_flat, h2_flat)[0, 1]
                comparison['correlation'][pair_key] = float(corr) if not np.isnan(corr) else 0.0
                
                binary_1 = h1 > 0.5
                binary_2 = h2 > 0.5
                
                intersection = np.logical_and(binary_1, binary_2).sum()
                union = np.logical_or(binary_1, binary_2).sum()
                iou = intersection / union if union > 0 else 0.0
                comparison['iou'][pair_key] = float(iou)
                
                sum_areas = binary_1.sum() + binary_2.sum()
                dice = (2.0 * intersection) / sum_areas if sum_areas > 0 else 0.0
                comparison['dice'][pair_key] = float(dice)
        
        return comparison
