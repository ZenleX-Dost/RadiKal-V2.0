"""
Evaluate YOLO Classification Model - Confidence Analysis

This script analyzes how the classification model assigns confidence scores
to minor/unclear defects, helping identify if they're being misclassified
as "No Defect" due to low confidence.
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
from tqdm import tqdm

def analyze_classification_confidence(
    model_path: str,
    data_dir: str,
    splits: list = ['testing', 'validation']
):
    """
    Analyze confidence scores for each class prediction.
    Find images where model is uncertain (low confidence on correct class).
    """
    
    print("=" * 80)
    print("🔍 Classification Confidence Analysis")
    print("=" * 80)
    print(f"\n📍 Model: {model_path}")
    print(f"📍 Data: {data_dir}")
    print()
    
    # Load model
    print("📥 Loading classification model...")
    model = YOLO(model_path)
    
    # Check device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🔧 Device: {device.upper()}")
    print()
    
    # Class mapping
    class_names = {
        'Difetto1': 'LP',
        'Difetto2': 'PO',
        'Difetto4': 'CR',
        'NoDifetto': 'ND'
    }
    
    # Store results
    all_results = []
    misclassified_as_nd = []  # Images with defects classified as ND
    low_confidence_correct = []  # Correct but low confidence
    
    for split in splits:
        split_dir = Path(data_dir) / split
        
        if not split_dir.exists():
            print(f"⚠️ Skipping {split} (not found)")
            continue
        
        print(f"\n{'='*80}")
        print(f"📊 Analyzing {split.upper()} split")
        print(f"{'='*80}\n")
        
        # Process each class
        for class_folder in split_dir.iterdir():
            if not class_folder.is_dir():
                continue
            
            true_class = class_names.get(class_folder.name, class_folder.name)
            
            # Get all images
            image_files = list(class_folder.glob('*.png')) + \
                         list(class_folder.glob('*.jpg')) + \
                         list(class_folder.glob('*.jpeg'))
            
            if not image_files:
                continue
            
            print(f"🔍 Processing {true_class} ({len(image_files)} images)...")
            
            class_confidences = []
            predictions = []
            
            # Predict each image
            for img_path in tqdm(image_files, desc=f"  {true_class}", leave=False):
                try:
                    # Run prediction
                    results = model.predict(img_path, verbose=False)
                    
                    if len(results) > 0:
                        result = results[0]
                        
                        # Get probabilities for all classes
                        probs = result.probs
                        
                        if probs is not None:
                            # Get top prediction
                            top_class_id = int(probs.top1)
                            top_confidence = float(probs.top1conf)
                            pred_class = result.names[top_class_id]
                            
                            # Get confidence for all classes
                            all_confs = {result.names[i]: float(probs.data[i]) 
                                        for i in range(len(probs.data))}
                            
                            # Store result
                            result_data = {
                                'image': img_path.name,
                                'true_class': true_class,
                                'predicted_class': pred_class,
                                'confidence': top_confidence,
                                'split': split,
                                'correct': pred_class == true_class,
                                **{f'conf_{k}': v for k, v in all_confs.items()}
                            }
                            
                            all_results.append(result_data)
                            class_confidences.append(top_confidence)
                            predictions.append(pred_class)
                            
                            # Flag issues
                            if true_class != 'ND' and pred_class == 'ND':
                                # Defect misclassified as No Defect!
                                misclassified_as_nd.append(result_data)
                            
                            if pred_class == true_class and top_confidence < 0.7:
                                # Correct but low confidence
                                low_confidence_correct.append(result_data)
                
                except Exception as e:
                    print(f"    ⚠️ Error processing {img_path.name}: {e}")
                    continue
            
            # Statistics for this class
            if class_confidences:
                accuracy = sum(1 for p in predictions if p == true_class) / len(predictions)
                avg_conf = np.mean(class_confidences)
                min_conf = np.min(class_confidences)
                
                print(f"  ✅ Accuracy: {accuracy:.2%}")
                print(f"  📊 Avg Confidence: {avg_conf:.4f}")
                print(f"  📉 Min Confidence: {min_conf:.4f}")
                
                # Count misclassifications
                misclass_to_nd = sum(1 for p in predictions if p == 'ND' and true_class != 'ND')
                if misclass_to_nd > 0 and true_class != 'ND':
                    print(f"  ⚠️  Misclassified as ND: {misclass_to_nd} ({misclass_to_nd/len(predictions):.1%})")
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    print("\n" + "=" * 80)
    print("📊 OVERALL ANALYSIS")
    print("=" * 80)
    
    # Overall accuracy
    overall_acc = df['correct'].mean()
    print(f"\n✅ Overall Accuracy: {overall_acc:.2%}")
    
    # Per-class accuracy
    print("\n📈 Per-Class Accuracy:")
    for true_class in df['true_class'].unique():
        class_df = df[df['true_class'] == true_class]
        acc = class_df['correct'].mean()
        avg_conf = class_df['confidence'].mean()
        print(f"   {true_class:5s} → Accuracy: {acc:.2%}, Avg Confidence: {avg_conf:.4f}")
    
    # Confusion analysis
    print("\n🔀 Confusion Matrix:")
    confusion = pd.crosstab(df['true_class'], df['predicted_class'], 
                           rownames=['True'], colnames=['Predicted'])
    print(confusion)
    
    # Critical issue: Defects misclassified as ND
    print("\n" + "=" * 80)
    print("🚨 CRITICAL: Defects Misclassified as 'No Defect'")
    print("=" * 80)
    
    if misclassified_as_nd:
        print(f"\n⚠️  Found {len(misclassified_as_nd)} defects misclassified as ND!")
        
        # Group by true class
        misclass_df = pd.DataFrame(misclassified_as_nd)
        print("\n📊 Breakdown by defect type:")
        for true_class in misclass_df['true_class'].unique():
            class_errors = misclass_df[misclass_df['true_class'] == true_class]
            avg_conf = class_errors['confidence'].mean()
            print(f"   {true_class} → {len(class_errors)} images, Avg ND Confidence: {avg_conf:.4f}")
            
            # Show confidence distribution
            print(f"      Min: {class_errors['confidence'].min():.4f}, "
                  f"Max: {class_errors['confidence'].max():.4f}")
        
        # Save misclassified images list
        misclass_csv = "models/defects_misclassified_as_nd.csv"
        misclass_df.to_csv(misclass_csv, index=False)
        print(f"\n💾 Misclassified images saved to: {misclass_csv}")
        
        # Analyze confidence scores
        print("\n🔍 Confidence Score Analysis for Misclassified Defects:")
        print(f"   When model says 'ND' for actual defects:")
        print(f"      ND Confidence: {misclass_df['confidence'].mean():.4f} (avg)")
        
        # Check if true class had decent confidence
        for idx, row in misclass_df.head(10).iterrows():
            true_class = row['true_class']
            true_class_conf = row.get(f'conf_{true_class}', 0)
            nd_conf = row['confidence']
            print(f"\n   Example: {row['image'][:40]}")
            print(f"      True: {true_class} (conf: {true_class_conf:.4f})")
            print(f"      Pred: ND (conf: {nd_conf:.4f})")
            print(f"      → Difference: {abs(nd_conf - true_class_conf):.4f}")
    else:
        print("\n✅ No defects were misclassified as 'No Defect'!")
    
    # Low confidence correct predictions
    print("\n" + "=" * 80)
    print("📉 Low Confidence Correct Predictions (< 0.7)")
    print("=" * 80)
    
    if low_confidence_correct:
        print(f"\n⚠️  Found {len(low_confidence_correct)} correct predictions with low confidence")
        
        low_conf_df = pd.DataFrame(low_confidence_correct)
        print("\n📊 Breakdown by class:")
        for true_class in low_conf_df['true_class'].unique():
            class_low = low_conf_df[low_conf_df['true_class'] == true_class]
            print(f"   {true_class} → {len(class_low)} images, "
                  f"Avg Conf: {class_low['confidence'].mean():.4f}")
        
        # These are candidates for improvement
        print("\n💡 These images might have minor/unclear defects!")
    
    # Save all results
    output_csv = "models/classification_confidence_analysis.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n💾 Full analysis saved to: {output_csv}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if misclassified_as_nd:
        nd_conf_threshold = misclass_df['confidence'].quantile(0.75)
        print(f"\n1. 🎯 Confidence Threshold Adjustment:")
        print(f"   Current: Model picks class with highest confidence")
        print(f"   Problem: 'ND' wins with confidence as low as {misclass_df['confidence'].min():.4f}")
        print(f"   Recommendation: Require ND confidence > {nd_conf_threshold:.2f} to classify as ND")
        print(f"   Otherwise, pick the highest defect class (LP, PO, or CR)")
        
        print(f"\n2. 🔄 Retraining with Class Weights:")
        print(f"   Increase penalty for misclassifying defects as ND")
        print(f"   Use class weights: Defects=2.0-3.0, ND=0.5")
        
        print(f"\n3. 🎨 Data Augmentation:")
        print(f"   Add more variations of minor/unclear defects")
        print(f"   Use mixup, cutout, and contrast adjustments")
        
        print(f"\n4. 🏗️ Two-Stage Approach:")
        print(f"   Stage 1: Binary (Defect vs ND) with high sensitivity")
        print(f"   Stage 2: Classify defect type (LP/PO/CR)")
    else:
        print("\n✅ Model is performing well!")
        print("   No systematic misclassification of defects as ND")
        print("   Consider fine-tuning if you want higher confidence scores")
    
    print()
    
    return df, misclassified_as_nd, low_confidence_correct


def main():
    """Main evaluation function."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze classification confidence')
    parser.add_argument('--model', type=str, 
                       default='runs/mlflow/809728953514087462/bc7a3eba72794ad29e1e524408b9d0b1/artifacts/weights/best.pt',
                       help='Path to model')
    parser.add_argument('--data', type=str, default='../DATA',
                       help='Path to data directory')
    parser.add_argument('--splits', nargs='+', default=['testing', 'validation'],
                       help='Splits to evaluate')
    
    args = parser.parse_args()
    
    # Check paths
    if not os.path.exists(args.model):
        print(f"❌ Model not found: {args.model}")
        return
    
    if not os.path.exists(args.data):
        print(f"❌ Data directory not found: {args.data}")
        return
    
    # Run analysis
    df, misclass, low_conf = analyze_classification_confidence(
        model_path=args.model,
        data_dir=args.data,
        splits=args.splits
    )
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\n📁 Output Files:")
    print("   • models/classification_confidence_analysis.csv")
    if misclass:
        print("   • models/defects_misclassified_as_nd.csv")
    print()


if __name__ == "__main__":
    main()
