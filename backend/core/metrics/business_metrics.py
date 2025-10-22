"""Business metrics for quality control.

This module provides functions to calculate business-relevant metrics
such as False Negatives, False Positives, Precision, Recall, and F1-score.
"""

from typing import Tuple, Optional, Dict
import numpy as np
from sklearn.metrics import confusion_matrix, classification_report


def calculate_confusion_matrix_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """Calculate metrics from confusion matrix.
    
    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        
    Returns:
        Dictionary containing TP, TN, FP, FN, Precision, Recall, F1-score.
    """
    cm = confusion_matrix(y_true, y_pred)
    
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tp = np.diag(cm).sum()
        fp = cm.sum(axis=0) - np.diag(cm)
        fp = fp.sum()
        fn = cm.sum(axis=1) - np.diag(cm)
        fn = fn.sum()
        tn = cm.sum() - (tp + fp + fn)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'true_positives': int(tp),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1)
    }


def calculate_precision(
    true_positives: int,
    false_positives: int
) -> float:
    """Calculate precision score.
    
    Precision = TP / (TP + FP)
    
    Args:
        true_positives: Number of true positives.
        false_positives: Number of false positives.
        
    Returns:
        Precision score.
    """
    if (true_positives + false_positives) == 0:
        return 0.0
    return true_positives / (true_positives + false_positives)


def calculate_recall(
    true_positives: int,
    false_negatives: int
) -> float:
    """Calculate recall score (sensitivity, true positive rate).
    
    Recall = TP / (TP + FN)
    
    Args:
        true_positives: Number of true positives.
        false_negatives: Number of false negatives.
        
    Returns:
        Recall score.
    """
    if (true_positives + false_negatives) == 0:
        return 0.0
    return true_positives / (true_positives + false_negatives)


def calculate_f1_score(
    precision: float,
    recall: float
) -> float:
    """Calculate F1-score (harmonic mean of precision and recall).
    
    F1 = 2 * (Precision * Recall) / (Precision + Recall)
    
    Args:
        precision: Precision score.
        recall: Recall score.
        
    Returns:
        F1-score.
    """
    if (precision + recall) == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def calculate_specificity(
    true_negatives: int,
    false_positives: int
) -> float:
    """Calculate specificity (true negative rate).
    
    Specificity = TN / (TN + FP)
    
    Args:
        true_negatives: Number of true negatives.
        false_positives: Number of false positives.
        
    Returns:
        Specificity score.
    """
    if (true_negatives + false_positives) == 0:
        return 0.0
    return true_negatives / (true_negatives + false_positives)


def calculate_accuracy(
    true_positives: int,
    true_negatives: int,
    false_positives: int,
    false_negatives: int
) -> float:
    """Calculate accuracy score.
    
    Accuracy = (TP + TN) / (TP + TN + FP + FN)
    
    Args:
        true_positives: Number of true positives.
        true_negatives: Number of true negatives.
        false_positives: Number of false positives.
        false_negatives: Number of false negatives.
        
    Returns:
        Accuracy score.
    """
    total = true_positives + true_negatives + false_positives + false_negatives
    if total == 0:
        return 0.0
    return (true_positives + true_negatives) / total


def calculate_balanced_accuracy(
    recall: float,
    specificity: float
) -> float:
    """Calculate balanced accuracy.
    
    Balanced Accuracy = (Recall + Specificity) / 2
    
    Args:
        recall: Recall score.
        specificity: Specificity score.
        
    Returns:
        Balanced accuracy score.
    """
    return (recall + specificity) / 2.0


def calculate_defect_rate(
    total_inspections: int,
    defects_found: int
) -> float:
    """Calculate defect rate (business metric).
    
    Args:
        total_inspections: Total number of inspections.
        defects_found: Number of defects found.
        
    Returns:
        Defect rate as a percentage.
    """
    if total_inspections == 0:
        return 0.0
    return (defects_found / total_inspections) * 100.0


def calculate_false_alarm_rate(
    false_positives: int,
    total_negatives: int
) -> float:
    """Calculate false alarm rate (business metric).
    
    False Alarm Rate = FP / (FP + TN)
    
    Args:
        false_positives: Number of false positives.
        total_negatives: Total number of negative samples (FP + TN).
        
    Returns:
        False alarm rate as a percentage.
    """
    if total_negatives == 0:
        return 0.0
    return (false_positives / total_negatives) * 100.0


def calculate_miss_rate(
    false_negatives: int,
    total_positives: int
) -> float:
    """Calculate miss rate (business metric).
    
    Miss Rate = FN / (FN + TP)
    
    Args:
        false_negatives: Number of false negatives.
        total_positives: Total number of positive samples (FN + TP).
        
    Returns:
        Miss rate as a percentage.
    """
    if total_positives == 0:
        return 0.0
    return (false_negatives / total_positives) * 100.0


def get_business_metrics_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    total_inspections: Optional[int] = None
) -> Dict[str, float]:
    """Generate comprehensive business metrics report.
    
    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        total_inspections: Optional total number of inspections.
        
    Returns:
        Dictionary containing all business metrics.
    """
    metrics = calculate_confusion_matrix_metrics(y_true, y_pred)
    
    tp = metrics['true_positives']
    tn = metrics['true_negatives']
    fp = metrics['false_positives']
    fn = metrics['false_negatives']
    
    specificity = calculate_specificity(tn, fp)
    accuracy = calculate_accuracy(tp, tn, fp, fn)
    balanced_acc = calculate_balanced_accuracy(metrics['recall'], specificity)
    
    if total_inspections is None:
        total_inspections = len(y_true)
    
    defects_found = tp + fp
    defect_rate = calculate_defect_rate(total_inspections, defects_found)
    false_alarm_rate = calculate_false_alarm_rate(fp, tn + fp)
    miss_rate = calculate_miss_rate(fn, tp + fn)
    
    return {
        **metrics,
        'specificity': float(specificity),
        'accuracy': float(accuracy),
        'balanced_accuracy': float(balanced_acc),
        'defect_rate_percent': float(defect_rate),
        'false_alarm_rate_percent': float(false_alarm_rate),
        'miss_rate_percent': float(miss_rate),
        'total_inspections': int(total_inspections)
    }


def generate_classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target_names: Optional[list] = None
) -> str:
    """Generate detailed classification report.
    
    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        target_names: Optional list of class names.
        
    Returns:
        Classification report as formatted string.
    """
    return classification_report(y_true, y_pred, target_names=target_names)
