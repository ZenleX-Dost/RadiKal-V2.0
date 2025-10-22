"""
Model evaluation script for XAI Visual Quality Control.

This script evaluates a trained model on the test set and generates
comprehensive metrics reports.

Usage:
    python scripts/evaluate.py --model models/checkpoints/best_model.pth

Author: RadiKal Team
Date: 2025-01-20
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

import torch
import numpy as np
from tqdm import tqdm
import mlflow

from core.models.detector import DefectDetector
from core.preprocessing.image_processor import ImageProcessor
from core.metrics.business_metrics import (
    calculate_confusion_matrix_metrics,
    get_business_metrics_report
)
from core.metrics.detection_metrics import calculate_map, calculate_auroc
from core.metrics.segmentation_metrics import calculate_mean_iou
from core.uncertainty.calibration import calculate_ece

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_data(data_dir: Path):
    """
    Load test dataset.
    
    Args:
        data_dir: Path to test data directory
        
    Returns:
        List of (image_path, annotations) tuples
    """
    test_dir = data_dir / "test"
    images_dir = test_dir / "images"
    annotations_file = test_dir / "annotations.json"
    
    if not annotations_file.exists():
        raise FileNotFoundError(f"Annotations not found: {annotations_file}")
    
    with open(annotations_file, 'r') as f:
        annotations = json.load(f)
    
    # Create image_id to annotations mapping
    image_annotations = {}
    for ann in annotations.get('annotations', []):
        img_id = ann['image_id']
        if img_id not in image_annotations:
            image_annotations[img_id] = []
        image_annotations[img_id].append(ann)
    
    # Load images and their annotations
    test_data = []
    for image_info in annotations.get('images', []):
        img_id = image_info['id']
        img_path = images_dir / image_info['file_name']
        
        if img_path.exists():
            test_data.append({
                'image_path': str(img_path),
                'annotations': image_annotations.get(img_id, []),
                'image_id': img_id,
            })
    
    return test_data


def evaluate_model(
    model: DefectDetector,
    test_data: list,
    image_processor: ImageProcessor,
    device: str,
) -> dict:
    """
    Evaluate model on test dataset.
    
    Args:
        model: Trained defect detector
        test_data: List of test samples
        image_processor: Image preprocessor
        device: Device to run evaluation on
        
    Returns:
        Dictionary of evaluation metrics
    """
    model.model.eval()
    
    all_predictions = []
    all_ground_truth = []
    all_confidences = []
    all_pred_labels = []
    all_true_labels = []
    
    logger.info(f"Evaluating on {len(test_data)} test images...")
    
    with torch.no_grad():
        for sample in tqdm(test_data, desc="Evaluating"):
            # Load and preprocess image
            image = image_processor.load_image(sample['image_path'])
            preprocessed = image_processor.preprocess(image)
            image_tensor = torch.from_numpy(
                image_processor.to_tensor(preprocessed)
            ).float().unsqueeze(0).to(device)
            
            # Get predictions
            predictions = model.predict(image_tensor)
            
            # Extract ground truth
            gt_boxes = [ann['bbox'] for ann in sample['annotations']]
            gt_labels = [ann['category_id'] for ann in sample['annotations']]
            
            # Store for metrics calculation
            all_predictions.append({
                'boxes': [det['box'] for det in predictions],
                'scores': [det['score'] for det in predictions],
                'labels': [det['label'] for det in predictions],
            })
            
            all_ground_truth.append({
                'boxes': gt_boxes,
                'labels': gt_labels,
            })
            
            # Collect confidences and labels for calibration
            for det in predictions:
                all_confidences.append(det['score'])
                all_pred_labels.append(1 if det['label'] == 'defect' else 0)
            
            for gt_label in gt_labels:
                all_true_labels.append(1 if gt_label == 1 else 0)
    
    # Calculate metrics
    logger.info("Calculating metrics...")
    
    # Detection metrics
    from core.metrics.detection_metrics import calculate_map as compute_map
    map_scores = {}
    for iou_threshold in [0.5, 0.75]:
        map_score = compute_map(all_predictions, all_ground_truth, iou_threshold=iou_threshold)
        map_scores[f'mAP@{iou_threshold}'] = map_score
    
    # AUROC
    if len(all_confidences) > 0 and len(all_true_labels) > 0:
        auroc = calculate_auroc(
            np.array(all_confidences[:len(all_true_labels)]),
            np.array(all_true_labels)
        )
    else:
        auroc = 0.0
    
    # Business metrics (using simple threshold)
    pred_binary = np.array([1 if s > 0.5 else 0 for s in all_confidences[:len(all_true_labels)]])
    true_binary = np.array(all_true_labels)
    
    if len(pred_binary) > 0:
        business_metrics = calculate_confusion_matrix_metrics(pred_binary, true_binary)
    else:
        business_metrics = {}
    
    # Calibration
    if len(all_confidences) > 0:
        ece = calculate_ece(
            torch.tensor(all_confidences[:len(all_true_labels)]),
            torch.tensor(pred_binary),
            torch.tensor(true_binary),
            n_bins=10
        )
    else:
        ece = 0.0
    
    # Compile all metrics
    metrics = {
        **map_scores,
        'AUROC': float(auroc),
        **business_metrics,
        'ECE': float(ece),
        'num_test_samples': len(test_data),
        'total_predictions': len(all_predictions),
    }
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate XAI QC model")
    parser.add_argument('--model', type=str, required=True,
                       help='Path to model checkpoint')
    parser.add_argument('--data-dir', type=str, default='data',
                       help='Path to data directory')
    parser.add_argument('--device', type=str, default='cuda',
                       choices=['cuda', 'cpu'],
                       help='Device to use for evaluation')
    parser.add_argument('--output', type=str, default='evaluation_results.json',
                       help='Path to save evaluation results')
    
    args = parser.parse_args()
    
    # Setup device
    device = args.device if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    
    # Load model
    logger.info(f"Loading model from {args.model}...")
    model = DefectDetector(num_classes=2, device=device)
    model.load_weights(args.model)
    
    # Initialize image processor
    image_processor = ImageProcessor(target_size=(512, 512))
    
    # Load test data
    data_dir = Path(args.data_dir)
    test_data = load_test_data(data_dir)
    logger.info(f"Loaded {len(test_data)} test samples")
    
    # Evaluate
    metrics = evaluate_model(model, test_data, image_processor, device)
    
    # Log to MLflow
    with mlflow.start_run(run_name="evaluation"):
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                mlflow.log_metric(metric_name, metric_value)
    
    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Evaluation complete! Results saved to {output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    for metric_name, metric_value in metrics.items():
        if isinstance(metric_value, float):
            print(f"{metric_name:.<40} {metric_value:.4f}")
        else:
            print(f"{metric_name:.<40} {metric_value}")
    print("="*60)


if __name__ == "__main__":
    main()
