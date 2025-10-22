"""Detection metrics for object detection tasks.

This module provides functions to calculate detection-specific metrics
such as Average Precision (AP), mean Average Precision (mAP), and AUROC.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve, auc


def calculate_iou(
    box1: np.ndarray,
    box2: np.ndarray
) -> float:
    """Calculate Intersection over Union (IoU) for two bounding boxes.
    
    Args:
        box1: Bounding box [x1, y1, x2, y2].
        box2: Bounding box [x1, y1, x2, y2].
        
    Returns:
        IoU score.
    """
    x1_inter = max(box1[0], box2[0])
    y1_inter = max(box1[1], box2[1])
    x2_inter = min(box1[2], box2[2])
    y2_inter = min(box1[3], box2[3])
    
    inter_width = max(0, x2_inter - x1_inter)
    inter_height = max(0, y2_inter - y1_inter)
    intersection = inter_width * inter_height
    
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = box1_area + box2_area - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def calculate_average_precision(
    recalls: np.ndarray,
    precisions: np.ndarray
) -> float:
    """Calculate Average Precision (AP) using 11-point interpolation.
    
    Args:
        recalls: Array of recall values.
        precisions: Array of precision values.
        
    Returns:
        Average Precision score.
    """
    recalls = np.concatenate(([0], recalls, [1]))
    precisions = np.concatenate(([0], precisions, [0]))
    
    for i in range(len(precisions) - 2, -1, -1):
        precisions[i] = max(precisions[i], precisions[i + 1])
    
    indices = np.where(recalls[1:] != recalls[:-1])[0] + 1
    ap = np.sum((recalls[indices] - recalls[indices - 1]) * precisions[indices])
    
    return float(ap)


def calculate_precision_recall_curve(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate precision-recall curve for detections.
    
    Args:
        predictions: List of prediction dictionaries with 'boxes', 'scores', 'labels'.
        ground_truths: List of ground truth dictionaries with 'boxes', 'labels'.
        iou_threshold: IoU threshold for considering a detection as correct.
        
    Returns:
        Tuple of (precisions, recalls) arrays.
    """
    all_detections = []
    
    for img_idx, (pred, gt) in enumerate(zip(predictions, ground_truths)):
        pred_boxes = np.array(pred['boxes'])
        pred_scores = np.array(pred['scores'])
        pred_labels = np.array(pred['labels'])
        
        gt_boxes = np.array(gt['boxes'])
        gt_labels = np.array(gt['labels'])
        
        for box, score, label in zip(pred_boxes, pred_scores, pred_labels):
            matched = False
            for gt_box, gt_label in zip(gt_boxes, gt_labels):
                if label == gt_label:
                    iou = calculate_iou(box, gt_box)
                    if iou >= iou_threshold:
                        matched = True
                        break
            
            all_detections.append({
                'score': score,
                'matched': matched
            })
    
    all_detections = sorted(all_detections, key=lambda x: x['score'], reverse=True)
    
    true_positives = np.cumsum([d['matched'] for d in all_detections])
    false_positives = np.cumsum([not d['matched'] for d in all_detections])
    
    total_ground_truths = sum(len(gt['boxes']) for gt in ground_truths)
    
    precisions = true_positives / (true_positives + false_positives + 1e-10)
    recalls = true_positives / (total_ground_truths + 1e-10)
    
    return precisions, recalls


def calculate_map(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5,
    num_classes: Optional[int] = None
) -> float:
    """Calculate mean Average Precision (mAP).
    
    Args:
        predictions: List of prediction dictionaries.
        ground_truths: List of ground truth dictionaries.
        iou_threshold: IoU threshold for matching.
        num_classes: Number of classes (if None, inferred from data).
        
    Returns:
        mAP score.
    """
    if num_classes is None:
        all_labels = set()
        for gt in ground_truths:
            all_labels.update(gt['labels'])
        num_classes = len(all_labels)
    
    aps = []
    
    for class_id in range(num_classes):
        class_preds = [
            {
                'boxes': [box for box, label in zip(pred['boxes'], pred['labels']) if label == class_id],
                'scores': [score for score, label in zip(pred['scores'], pred['labels']) if label == class_id],
                'labels': [class_id] * sum(1 for label in pred['labels'] if label == class_id)
            }
            for pred in predictions
        ]
        
        class_gts = [
            {
                'boxes': [box for box, label in zip(gt['boxes'], gt['labels']) if label == class_id],
                'labels': [class_id] * sum(1 for label in gt['labels'] if label == class_id)
            }
            for gt in ground_truths
        ]
        
        if not any(len(gt['boxes']) > 0 for gt in class_gts):
            continue
        
        precisions, recalls = calculate_precision_recall_curve(
            class_preds, class_gts, iou_threshold
        )
        
        ap = calculate_average_precision(recalls, precisions)
        aps.append(ap)
    
    if not aps:
        return 0.0
    
    return float(np.mean(aps))


def calculate_auroc(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    multi_class: str = 'ovr'
) -> float:
    """Calculate Area Under ROC Curve (AUROC).
    
    Args:
        y_true: Ground truth labels.
        y_scores: Predicted scores/probabilities.
        multi_class: Strategy for multi-class ('ovr' or 'ovo').
        
    Returns:
        AUROC score.
    """
    try:
        if len(y_scores.shape) > 1 and y_scores.shape[1] > 2:
            auroc = roc_auc_score(y_true, y_scores, multi_class=multi_class)
        else:
            if len(y_scores.shape) > 1:
                y_scores = y_scores[:, 1]
            auroc = roc_auc_score(y_true, y_scores)
        return float(auroc)
    except ValueError:
        return 0.0


def calculate_detection_metrics(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_thresholds: List[float] = [0.5, 0.75]
) -> Dict[str, float]:
    """Calculate comprehensive detection metrics.
    
    Args:
        predictions: List of prediction dictionaries.
        ground_truths: List of ground truth dictionaries.
        iou_thresholds: List of IoU thresholds to evaluate.
        
    Returns:
        Dictionary containing detection metrics.
    """
    metrics = {}
    
    for iou_thresh in iou_thresholds:
        map_score = calculate_map(predictions, ground_truths, iou_thresh)
        metrics[f'mAP@{iou_thresh}'] = float(map_score)
    
    if len(iou_thresholds) > 1:
        avg_map = np.mean([metrics[f'mAP@{t}'] for t in iou_thresholds])
        metrics['mAP'] = float(avg_map)
    
    return metrics
