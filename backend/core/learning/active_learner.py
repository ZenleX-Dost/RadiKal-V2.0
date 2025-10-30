"""
Active Learning Pipeline for RadiKal XAI Quality Control.

This module implements active learning strategies to intelligently select
which images should be labeled next to maximize model improvement.

**Active Learning Strategies**:
1. Uncertainty Sampling - Select images with highest prediction uncertainty
2. Diversity Sampling - Select images covering diverse feature space
3. Disagreement Sampling - Select images where ensemble models disagree
4. Learning from Reviews - Incorporate inspector corrections

**Workflow**:
1. Model makes prediction on unlabeled image
2. Active learner calculates uncertainty/priority scores
3. High-priority images added to labeling queue
4. Human labels the image
5. Image added to training set
6. Model retrained periodically
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.stats import entropy
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class ActiveLearner:
    """
    Active Learning system for intelligent sample selection.
    """
    
    def __init__(
        self,
        uncertainty_threshold: float = 0.3,
        diversity_weight: float = 0.3,
        disagreement_weight: float = 0.4,
        min_samples_per_class: int = 50
    ):
        """
        Initialize active learner.
        
        Args:
            uncertainty_threshold: Minimum uncertainty to consider image
            diversity_weight: Weight for diversity score in final priority
            disagreement_weight: Weight for ensemble disagreement in priority
            min_samples_per_class: Minimum samples needed per class
        """
        self.uncertainty_threshold = uncertainty_threshold
        self.diversity_weight = diversity_weight
        self.disagreement_weight = disagreement_weight
        self.min_samples_per_class = min_samples_per_class
        
        # Track labeled samples for diversity calculation
        self.labeled_features = []
        self.labeled_classes = []
        
        logger.info("Initialized ActiveLearner")
    
    
    def calculate_uncertainty(
        self,
        probabilities: np.ndarray,
        method: str = "entropy"
    ) -> float:
        """
        Calculate prediction uncertainty from class probabilities.
        
        Args:
            probabilities: Array of class probabilities (sums to 1.0)
            method: Uncertainty calculation method
                - "entropy": Shannon entropy
                - "margin": Margin between top 2 classes
                - "least_confident": 1 - max probability
        
        Returns:
            Uncertainty score (0.0 = certain, 1.0 = maximally uncertain)
        """
        if method == "entropy":
            # Shannon entropy: high when probabilities are uniform
            ent = entropy(probabilities + 1e-10)  # Add epsilon to avoid log(0)
            max_entropy = np.log(len(probabilities))
            normalized_entropy = ent / max_entropy
            return float(normalized_entropy)
        
        elif method == "margin":
            # Margin sampling: difference between top 2 predictions
            sorted_probs = np.sort(probabilities)[::-1]
            if len(sorted_probs) < 2:
                return 0.0
            margin = sorted_probs[0] - sorted_probs[1]
            return float(1.0 - margin)  # Small margin = high uncertainty
        
        elif method == "least_confident":
            # Least confident: 1 - max probability
            max_prob = np.max(probabilities)
            return float(1.0 - max_prob)
        
        else:
            raise ValueError(f"Unknown uncertainty method: {method}")
    
    
    def calculate_ensemble_disagreement(
        self,
        ensemble_predictions: List[np.ndarray]
    ) -> float:
        """
        Calculate disagreement between ensemble model predictions.
        
        High disagreement indicates ambiguous samples that need labeling.
        
        Args:
            ensemble_predictions: List of probability arrays from different models
        
        Returns:
            Disagreement score (0.0 = agreement, 1.0 = maximum disagreement)
        """
        if len(ensemble_predictions) < 2:
            return 0.0
        
        # Calculate variance of predictions across ensemble
        stacked = np.stack(ensemble_predictions, axis=0)
        variance = np.var(stacked, axis=0)
        
        # Average variance across classes
        avg_variance = np.mean(variance)
        
        # Normalize to [0, 1]
        # Maximum variance occurs when half predict 0, half predict 1
        max_variance = 0.25  # Variance of [0, 1] with equal counts
        normalized_disagreement = min(avg_variance / max_variance, 1.0)
        
        return float(normalized_disagreement)
    
    
    def calculate_diversity_score(
        self,
        image_features: np.ndarray,
        labeled_features: Optional[List[np.ndarray]] = None
    ) -> float:
        """
        Calculate how diverse an image is compared to labeled samples.
        
        Diversity sampling ensures we explore different regions of feature space.
        
        Args:
            image_features: Feature vector for candidate image
            labeled_features: List of feature vectors from labeled samples
        
        Returns:
            Diversity score (0.0 = similar to labeled, 1.0 = very different)
        """
        if labeled_features is None:
            labeled_features = self.labeled_features
        
        if len(labeled_features) == 0:
            return 1.0  # No labeled samples yet, all are diverse
        
        # Calculate cosine similarity to all labeled samples
        similarities = cosine_similarity(
            image_features.reshape(1, -1),
            np.array(labeled_features)
        )[0]
        
        # Diversity = 1 - max similarity
        max_similarity = np.max(similarities)
        diversity = 1.0 - max_similarity
        
        return float(diversity)
    
    
    def calculate_class_imbalance_priority(
        self,
        predicted_class: int,
        class_counts: Dict[int, int]
    ) -> float:
        """
        Prioritize samples from underrepresented classes.
        
        Args:
            predicted_class: Predicted class index
            class_counts: Dictionary of current sample counts per class
        
        Returns:
            Priority score (0.0 = well-represented, 1.0 = underrepresented)
        """
        if predicted_class not in class_counts:
            return 1.0  # New class, high priority
        
        current_count = class_counts[predicted_class]
        
        if current_count >= self.min_samples_per_class:
            return 0.0  # Class has enough samples
        
        # Linear priority: closer to min_samples = lower priority
        priority = 1.0 - (current_count / self.min_samples_per_class)
        
        return float(priority)
    
    
    def calculate_priority_score(
        self,
        probabilities: np.ndarray,
        image_features: Optional[np.ndarray] = None,
        ensemble_predictions: Optional[List[np.ndarray]] = None,
        predicted_class: Optional[int] = None,
        class_counts: Optional[Dict[int, int]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall priority score for labeling an image.
        
        Combines multiple active learning strategies into single score.
        
        Args:
            probabilities: Class probability distribution
            image_features: Feature vector for diversity calculation
            ensemble_predictions: Predictions from ensemble models
            predicted_class: Predicted class index
            class_counts: Current sample counts per class
        
        Returns:
            Tuple of (priority_score, detailed_scores)
            - priority_score: Combined score (0.0-1.0, higher = more important)
            - detailed_scores: Dict with individual component scores
        """
        scores = {}
        
        # 1. Uncertainty score (always calculated)
        uncertainty = self.calculate_uncertainty(probabilities, method="entropy")
        scores["uncertainty"] = uncertainty
        
        # 2. Diversity score (if features provided)
        diversity = 0.0
        if image_features is not None:
            diversity = self.calculate_diversity_score(image_features)
            scores["diversity"] = diversity
        
        # 3. Ensemble disagreement (if ensemble predictions provided)
        disagreement = 0.0
        if ensemble_predictions is not None:
            disagreement = self.calculate_ensemble_disagreement(ensemble_predictions)
            scores["disagreement"] = disagreement
        
        # 4. Class imbalance priority (if class info provided)
        class_priority = 0.0
        if predicted_class is not None and class_counts is not None:
            class_priority = self.calculate_class_imbalance_priority(predicted_class, class_counts)
            scores["class_priority"] = class_priority
        
        # Combine scores with weights
        # Uncertainty is always the base (30% weight)
        priority = 0.3 * uncertainty
        
        # Add diversity if available (30% weight)
        if image_features is not None:
            priority += self.diversity_weight * diversity
        
        # Add disagreement if available (40% weight)
        if ensemble_predictions is not None:
            priority += self.disagreement_weight * disagreement
        
        # Boost priority for underrepresented classes (multiplier)
        if class_priority > 0:
            priority *= (1.0 + class_priority)
        
        # Normalize to [0, 1]
        priority = min(priority, 1.0)
        
        scores["final_priority"] = priority
        
        return priority, scores
    
    
    def should_suggest_for_labeling(
        self,
        probabilities: np.ndarray,
        image_features: Optional[np.ndarray] = None,
        ensemble_predictions: Optional[List[np.ndarray]] = None
    ) -> Tuple[bool, float, str]:
        """
        Decide if an image should be suggested for labeling.
        
        Args:
            probabilities: Class probability distribution
            image_features: Feature vector
            ensemble_predictions: Ensemble predictions
        
        Returns:
            Tuple of (should_suggest, priority_score, selection_method)
        """
        # Calculate uncertainty
        uncertainty = self.calculate_uncertainty(probabilities, method="entropy")
        
        # High uncertainty -> suggest for labeling
        if uncertainty >= self.uncertainty_threshold:
            priority, _ = self.calculate_priority_score(
                probabilities,
                image_features,
                ensemble_predictions
            )
            return True, priority, "uncertainty"
        
        # Check ensemble disagreement (if available)
        if ensemble_predictions is not None:
            disagreement = self.calculate_ensemble_disagreement(ensemble_predictions)
            if disagreement >= 0.4:  # High disagreement threshold
                priority, _ = self.calculate_priority_score(
                    probabilities,
                    image_features,
                    ensemble_predictions
                )
                return True, priority, "disagreement"
        
        # Check diversity (if features available)
        if image_features is not None:
            diversity = self.calculate_diversity_score(image_features)
            if diversity >= 0.7:  # High diversity threshold
                priority, _ = self.calculate_priority_score(
                    probabilities,
                    image_features,
                    ensemble_predictions
                )
                return True, priority, "diversity"
        
        # Low priority, don't suggest
        return False, 0.0, "none"
    
    
    def update_labeled_pool(
        self,
        image_features: np.ndarray,
        true_class: int
    ):
        """
        Add a newly labeled sample to the pool for diversity calculation.
        
        Args:
            image_features: Feature vector of labeled image
            true_class: Ground truth class label
        """
        self.labeled_features.append(image_features)
        self.labeled_classes.append(true_class)
        
        logger.debug(f"Updated labeled pool: {len(self.labeled_features)} samples")
    
    
    def analyze_review_correction(
        self,
        original_prediction: Dict,
        corrected_label: int,
        image_features: Optional[np.ndarray] = None
    ) -> Dict[str, any]:
        """
        Analyze a review correction to learn from inspector feedback.
        
        When an inspector corrects a prediction, this indicates:
        - Model is uncertain/wrong about this type of image
        - Similar images should be prioritized for labeling
        
        Args:
            original_prediction: Original model prediction dict
            corrected_label: Correct label provided by inspector
            image_features: Feature vector of corrected image
        
        Returns:
            Analysis dict with learning insights
        """
        analysis = {
            "is_correction": False,
            "confidence_before": 0.0,
            "correction_type": None,
            "suggests_retraining": False
        }
        
        predicted_class = original_prediction.get("predicted_class", -1)
        probabilities = original_prediction.get("probabilities", [])
        
        # Check if this was a correction (wrong prediction)
        if predicted_class != corrected_label:
            analysis["is_correction"] = True
            analysis["correction_type"] = "misclassification"
            
            # Get confidence of wrong prediction
            if len(probabilities) > predicted_class:
                analysis["confidence_before"] = float(probabilities[predicted_class])
            
            # High confidence wrong prediction -> model needs retraining
            if analysis["confidence_before"] > 0.7:
                analysis["suggests_retraining"] = True
                logger.warning(
                    f"High confidence misclassification detected! "
                    f"Predicted class {predicted_class} with {analysis['confidence_before']:.2f} confidence, "
                    f"correct class is {corrected_label}"
                )
        
        # Add to labeled pool if features provided
        if image_features is not None:
            self.update_labeled_pool(image_features, corrected_label)
        
        return analysis
    
    
    def get_labeling_recommendations(
        self,
        candidate_images: List[Dict],
        top_k: int = 20
    ) -> List[Dict]:
        """
        Get top-k images recommended for labeling.
        
        Args:
            candidate_images: List of dicts with keys:
                - image_id: str
                - probabilities: np.ndarray
                - features: Optional[np.ndarray]
                - ensemble_predictions: Optional[List[np.ndarray]]
            top_k: Number of recommendations to return
        
        Returns:
            List of recommended images sorted by priority
        """
        recommendations = []
        
        for img in candidate_images:
            should_suggest, priority, method = self.should_suggest_for_labeling(
                probabilities=img["probabilities"],
                image_features=img.get("features"),
                ensemble_predictions=img.get("ensemble_predictions")
            )
            
            if should_suggest:
                recommendations.append({
                    "image_id": img["image_id"],
                    "priority_score": priority,
                    "selection_method": method,
                    "uncertainty_score": self.calculate_uncertainty(img["probabilities"]),
                    "suggested_labels": self._get_top_k_classes(img["probabilities"], k=3)
                })
        
        # Sort by priority score (descending)
        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return recommendations[:top_k]
    
    
    def _get_top_k_classes(
        self,
        probabilities: np.ndarray,
        k: int = 3
    ) -> List[Dict[str, float]]:
        """
        Get top-k predicted classes with their probabilities.
        
        Args:
            probabilities: Class probability distribution
            k: Number of top classes to return
        
        Returns:
            List of dicts with {class_index, probability}
        """
        top_k_indices = np.argsort(probabilities)[::-1][:k]
        
        top_classes = []
        for idx in top_k_indices:
            top_classes.append({
                "class_index": int(idx),
                "probability": float(probabilities[idx])
            })
        
        return top_classes


# ===== Helper Functions =====

def create_active_learner(config: Optional[Dict] = None) -> ActiveLearner:
    """
    Factory function to create an ActiveLearner instance.
    
    Args:
        config: Optional configuration dict
    
    Returns:
        Configured ActiveLearner instance
    """
    if config is None:
        config = {}
    
    return ActiveLearner(
        uncertainty_threshold=config.get("uncertainty_threshold", 0.3),
        diversity_weight=config.get("diversity_weight", 0.3),
        disagreement_weight=config.get("disagreement_weight", 0.4),
        min_samples_per_class=config.get("min_samples_per_class", 50)
    )
