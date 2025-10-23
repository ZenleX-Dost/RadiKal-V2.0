"""
Evaluate Model Performance on Minor/Unclear Defects

This script specifically tests how well the model detects subtle defects
that might be misclassified as "No Defect".
"""

import os
import sys
from pathlib import Path
import torch
from ultralytics import YOLO
import pandas as pd
import numpy as np
from collections import defaultdict
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def evaluate_with_multiple_thresholds(
    model_path: str,
    data_yaml: str,
    confidence_thresholds: list = [0.1, 0.25, 0.5, 0.7, 0.9]
):
    """
    Evaluate model with different confidence thresholds to find optimal
    balance for detecting minor defects.
    """
    
    print("=" * 80)
    print("🔍 Minor Defect Detection Analysis")
    print("=" * 80)
    print(f"\n📍 Model: {model_path}")
    print(f"📍 Data: {data_yaml}")
    print()
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return
    
    # Load model
    print("📥 Loading model...")
    model = YOLO(model_path)
    
    # Check device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🔧 Device: {device.upper()}")
    print()
    
    # Store results for each threshold
    all_results = {}
    
    print("=" * 80)
    print("📊 Testing Multiple Confidence Thresholds")
    print("=" * 80)
    print()
    
    for conf_threshold in confidence_thresholds:
        print(f"\n{'─' * 80}")
        print(f"🎯 Testing with Confidence Threshold: {conf_threshold}")
        print(f"{'─' * 80}")
        
        # Run validation with specific confidence threshold
        metrics = model.val(
            data=data_yaml,
            conf=conf_threshold,
            iou=0.5,
            split='test',  # Use test set for true evaluation
            device=device,
            verbose=False,
            plots=False
        )
        
        # Extract metrics
        results_dict = metrics.results_dict
        
        # Get per-class metrics
        per_class_metrics = {}
        if hasattr(metrics, 'box'):
            # Class names
            names = model.names
            
            # Per-class precision, recall, mAP
            if hasattr(metrics.box, 'p'):
                for class_id, class_name in names.items():
                    per_class_metrics[class_name] = {
                        'precision': float(metrics.box.p[class_id]) if class_id < len(metrics.box.p) else 0.0,
                        'recall': float(metrics.box.r[class_id]) if class_id < len(metrics.box.r) else 0.0,
                        'mAP50': float(metrics.box.ap50[class_id]) if class_id < len(metrics.box.ap50) else 0.0,
                    }
        
        # Store results
        all_results[conf_threshold] = {
            'overall': {
                'precision': float(results_dict.get('metrics/precision(B)', 0)),
                'recall': float(results_dict.get('metrics/recall(B)', 0)),
                'mAP50': float(results_dict.get('metrics/mAP50(B)', 0)),
                'mAP50-95': float(results_dict.get('metrics/mAP50-95(B)', 0)),
            },
            'per_class': per_class_metrics
        }
        
        # Print summary
        print(f"\n📈 Overall Metrics (conf={conf_threshold}):")
        print(f"   Precision: {all_results[conf_threshold]['overall']['precision']:.4f}")
        print(f"   Recall:    {all_results[conf_threshold]['overall']['recall']:.4f}")
        print(f"   mAP@0.5:   {all_results[conf_threshold]['overall']['mAP50']:.4f}")
        
        if per_class_metrics:
            print(f"\n📊 Per-Class Metrics:")
            for class_name, metrics in per_class_metrics.items():
                print(f"\n   {class_name}:")
                print(f"      Precision: {metrics['precision']:.4f}")
                print(f"      Recall:    {metrics['recall']:.4f}  {'⚠️ LOW!' if metrics['recall'] < 0.8 else '✅'}")
                print(f"      mAP@0.5:   {metrics['mAP50']:.4f}")
    
    # Analysis: Find best threshold for defect detection
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS: Best Confidence Threshold for Minor Defects")
    print("=" * 80)
    
    # Calculate defect recall (excluding "No Defect" class)
    defect_recalls = {}
    for conf, results in all_results.items():
        if 'per_class' in results and results['per_class']:
            # Average recall for defect classes (LP, PO, CR)
            defect_classes = [k for k in results['per_class'].keys() if k != 'ND' and k != 'NoDifetto']
            if defect_classes:
                recalls = [results['per_class'][cls]['recall'] for cls in defect_classes]
                defect_recalls[conf] = np.mean(recalls)
    
    if defect_recalls:
        best_threshold = max(defect_recalls.keys(), key=lambda k: defect_recalls[k])
        print(f"\n✅ Best Threshold for Defect Detection: {best_threshold}")
        print(f"   Average Defect Recall: {defect_recalls[best_threshold]:.4f}")
        print(f"\n💡 Recommendation:")
        print(f"   - Current threshold might be too high ({0.25} default)")
        print(f"   - Lower to {best_threshold} to catch more minor defects")
        print(f"   - Trade-off: May increase false positives slightly")
    
    # Save results to JSON
    output_path = "models/threshold_analysis.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Results saved to: {output_path}")
    
    # Create comparison DataFrame
    print("\n" + "=" * 80)
    print("📊 THRESHOLD COMPARISON TABLE")
    print("=" * 80)
    
    comparison_data = []
    for conf, results in all_results.items():
        row = {
            'Confidence': conf,
            'Precision': results['overall']['precision'],
            'Recall': results['overall']['recall'],
            'mAP@0.5': results['overall']['mAP50'],
        }
        
        # Add per-class recalls
        if 'per_class' in results and results['per_class']:
            for class_name, metrics in results['per_class'].items():
                row[f'{class_name}_Recall'] = metrics['recall']
        
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    print("\n")
    print(df.to_string(index=False))
    
    # Save to CSV
    csv_path = "models/threshold_comparison.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n💾 Comparison saved to: {csv_path}")
    
    return all_results


def main():
    """Main evaluation function."""
    
    # Configuration
    MODEL_PATH = "runs/mlflow/809728953514087462/bc7a3eba72794ad29e1e524408b9d0b1/artifacts/weights/best.pt"
    DATA_YAML = "../DATA/data.yaml"  # Use the actual DATA directory
    
    # Alternative paths if first doesn't exist
    if not os.path.exists(MODEL_PATH):
        MODEL_PATH = "models/yolo/radikal_weld_detection/weights/best.pt"
    
    if not os.path.exists(DATA_YAML):
        DATA_YAML = "models/yolo/riawelc.yaml"
    
    # Test with multiple confidence thresholds
    # Lower thresholds will detect more subtle defects
    confidence_thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 0.7]
    
    print("\n🔍 This will test how confidence threshold affects minor defect detection")
    print("   Lower thresholds → More sensitive to subtle defects")
    print("   Higher thresholds → More confident, may miss minor defects")
    print()
    
    results = evaluate_with_multiple_thresholds(
        model_path=MODEL_PATH,
        data_yaml=DATA_YAML,
        confidence_thresholds=confidence_thresholds
    )
    
    print("\n" + "=" * 80)
    print("✅ EVALUATION COMPLETE!")
    print("=" * 80)
    print("\n📍 Next Steps:")
    print("   1. Check threshold_comparison.csv for detailed results")
    print("   2. Choose optimal confidence threshold for deployment")
    print("   3. If recall is still low, retrain with class weighting")
    print("   4. Consider focal loss for hard-to-detect defects")
    print()


if __name__ == "__main__":
    main()
