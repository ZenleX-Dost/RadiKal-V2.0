"""Segmentation metrics for image segmentation tasks.

This module provides functions to calculate segmentation-specific metrics
such as IoU (Jaccard Index) and Dice Score.
"""

from typing import Union, Optional
import numpy as np


def calculate_iou(
    mask1: np.ndarray,
    mask2: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """Calculate Intersection over Union (IoU) for segmentation masks.
    
    Also known as Jaccard Index.
    
    Args:
        mask1: Binary mask (ground truth).
        mask2: Binary mask (prediction).
        epsilon: Small constant for numerical stability.
        
    Returns:
        IoU score in [0, 1].
    """
    mask1 = mask1.astype(bool)
    mask2 = mask2.astype(bool)
    
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    
    iou = (intersection + epsilon) / (union + epsilon)
    
    return float(iou)


def calculate_dice_score(
    mask1: np.ndarray,
    mask2: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """Calculate Dice Score (F1-score for segmentation).
    
    Also known as Sorensen-Dice coefficient.
    
    Args:
        mask1: Binary mask (ground truth).
        mask2: Binary mask (prediction).
        epsilon: Small constant for numerical stability.
        
    Returns:
        Dice score in [0, 1].
    """
    mask1 = mask1.astype(bool)
    mask2 = mask2.astype(bool)
    
    intersection = np.logical_and(mask1, mask2).sum()
    sum_masks = mask1.sum() + mask2.sum()
    
    if sum_masks == 0:
        return 1.0 if intersection == 0 else 0.0
    
    dice = (2.0 * intersection + epsilon) / (sum_masks + epsilon)
    
    return float(dice)


def calculate_pixel_accuracy(
    mask1: np.ndarray,
    mask2: np.ndarray
) -> float:
    """Calculate pixel-wise accuracy.
    
    Args:
        mask1: Binary mask (ground truth).
        mask2: Binary mask (prediction).
        
    Returns:
        Pixel accuracy in [0, 1].
    """
    mask1 = mask1.astype(bool)
    mask2 = mask2.astype(bool)
    
    correct_pixels = (mask1 == mask2).sum()
    total_pixels = mask1.size
    
    return float(correct_pixels / total_pixels)


def calculate_precision_segmentation(
    mask_true: np.ndarray,
    mask_pred: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """Calculate precision for segmentation.
    
    Precision = TP / (TP + FP)
    
    Args:
        mask_true: Ground truth mask.
        mask_pred: Predicted mask.
        epsilon: Small constant for numerical stability.
        
    Returns:
        Precision score.
    """
    mask_true = mask_true.astype(bool)
    mask_pred = mask_pred.astype(bool)
    
    true_positive = np.logical_and(mask_true, mask_pred).sum()
    predicted_positive = mask_pred.sum()
    
    if predicted_positive == 0:
        return 0.0
    
    return float((true_positive + epsilon) / (predicted_positive + epsilon))


def calculate_recall_segmentation(
    mask_true: np.ndarray,
    mask_pred: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """Calculate recall for segmentation.
    
    Recall = TP / (TP + FN)
    
    Args:
        mask_true: Ground truth mask.
        mask_pred: Predicted mask.
        epsilon: Small constant for numerical stability.
        
    Returns:
        Recall score.
    """
    mask_true = mask_true.astype(bool)
    mask_pred = mask_pred.astype(bool)
    
    true_positive = np.logical_and(mask_true, mask_pred).sum()
    actual_positive = mask_true.sum()
    
    if actual_positive == 0:
        return 0.0
    
    return float((true_positive + epsilon) / (actual_positive + epsilon))


def calculate_mean_iou(
    masks_true: np.ndarray,
    masks_pred: np.ndarray,
    num_classes: Optional[int] = None
) -> float:
    """Calculate mean IoU across multiple classes or instances.
    
    Args:
        masks_true: Ground truth masks of shape (N, H, W) or (N, C, H, W).
        masks_pred: Predicted masks of shape (N, H, W) or (N, C, H, W).
        num_classes: Number of classes (if None, assumes binary).
        
    Returns:
        Mean IoU score.
    """
    if masks_true.shape != masks_pred.shape:
        raise ValueError("Mask shapes must match")
    
    ious = []
    
    if len(masks_true.shape) == 3:
        for mask_true, mask_pred in zip(masks_true, masks_pred):
            iou = calculate_iou(mask_true, mask_pred)
            ious.append(iou)
    elif len(masks_true.shape) == 4:
        for i in range(masks_true.shape[0]):
            for c in range(masks_true.shape[1]):
                iou = calculate_iou(masks_true[i, c], masks_pred[i, c])
                ious.append(iou)
    else:
        raise ValueError("Unsupported mask shape")
    
    return float(np.mean(ious))


def calculate_mean_dice(
    masks_true: np.ndarray,
    masks_pred: np.ndarray
) -> float:
    """Calculate mean Dice score across multiple instances.
    
    Args:
        masks_true: Ground truth masks of shape (N, H, W).
        masks_pred: Predicted masks of shape (N, H, W).
        
    Returns:
        Mean Dice score.
    """
    if masks_true.shape != masks_pred.shape:
        raise ValueError("Mask shapes must match")
    
    dice_scores = []
    
    if len(masks_true.shape) == 3:
        for mask_true, mask_pred in zip(masks_true, masks_pred):
            dice = calculate_dice_score(mask_true, mask_pred)
            dice_scores.append(dice)
    elif len(masks_true.shape) == 4:
        for i in range(masks_true.shape[0]):
            for c in range(masks_true.shape[1]):
                dice = calculate_dice_score(masks_true[i, c], masks_pred[i, c])
                dice_scores.append(dice)
    else:
        dice = calculate_dice_score(masks_true, masks_pred)
        return dice
    
    return float(np.mean(dice_scores))


def calculate_segmentation_metrics(
    mask_true: np.ndarray,
    mask_pred: np.ndarray
) -> dict:
    """Calculate comprehensive segmentation metrics.
    
    Args:
        mask_true: Ground truth mask.
        mask_pred: Predicted mask.
        
    Returns:
        Dictionary containing all segmentation metrics.
    """
    iou = calculate_iou(mask_true, mask_pred)
    dice = calculate_dice_score(mask_true, mask_pred)
    pixel_acc = calculate_pixel_accuracy(mask_true, mask_pred)
    precision = calculate_precision_segmentation(mask_true, mask_pred)
    recall = calculate_recall_segmentation(mask_true, mask_pred)
    
    return {
        'iou': float(iou),
        'dice_score': float(dice),
        'pixel_accuracy': float(pixel_acc),
        'precision': float(precision),
        'recall': float(recall)
    }
