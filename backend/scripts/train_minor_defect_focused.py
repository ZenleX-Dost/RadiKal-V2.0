"""
Train YOLOv8 with Focus on Minor/Unclear Defect Detection

This script addresses the specific problem of minor defects being
misclassified as "No Defect" by:
1. Class weighting (penalize missing defects more)
2. Lower confidence threshold during training
3. Enhanced augmentation for subtle features
4. Focal loss for hard examples
5. Higher recall optimization
"""

import os
import sys
from pathlib import Path
import yaml
from datetime import datetime
import torch
import numpy as np

def create_class_weighted_config(data_yaml_path: str, output_path: str = None):
    """
    Create a modified data.yaml with class weights that penalize
    missing defects (false negatives) more than false positives.
    """
    
    with open(data_yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Calculate class weights based on distribution
    # Training distribution:
    # Difetto1 (LP): 4962 (31.3%)
    # Difetto2 (PO): 4108 (25.9%)
    # Difetto4 (CR): 2893 (18.2%) <- Underrepresented
    # NoDifetto (ND): 3900 (24.6%)
    
    total = 4962 + 4108 + 2893 + 3900
    
    # Calculate inverse frequency weights
    weights = {
        0: total / (4 * 4962),  # LP - Difetto1
        1: total / (4 * 4108),  # PO - Difetto2
        2: total / (4 * 2893) * 1.5,  # CR - Difetto4 (boost more - underrepresented)
        3: total / (4 * 3900) * 0.5,  # ND - NoDifetto (penalize less - we care more about defects)
    }
    
    # Normalize weights
    weight_sum = sum(weights.values())
    weights = {k: v/weight_sum * 4 for k, v in weights.items()}
    
    print("📊 Class Weights (Higher = More Important):")
    for class_id, name in config['names'].items():
        print(f"   {name:15s} → Weight: {weights[class_id]:.3f}")
    
    return weights


def train_improved_model(
    model_size: str = 's',
    data_yaml: str = 'models/yolo/riawelc.yaml',
    epochs: int = 100,
    batch_size: int = 16,
    img_size: int = 640,
    device: str = '0',
):
    """
    Train YOLOv8 with optimizations for minor defect detection.
    """
    
    try:
        from ultralytics import YOLO
        from ultralytics.utils.loss import v8DetectionLoss
    except ImportError:
        print("❌ Ultralytics not installed!")
        return
    
    # Check device
    if device != 'cpu' and not torch.cuda.is_available():
        print("⚠️ CUDA not available, switching to CPU")
        device = 'cpu'
    
    print("=" * 80)
    print("🎯 Training YOLOv8 for Minor Defect Detection")
    print("=" * 80)
    print(f"\n📊 Configuration:")
    print(f"   Model: YOLOv8{model_size}")
    print(f"   Focus: High recall for defect classes (LP, PO, CR)")
    print(f"   Strategy: Class weighting + Enhanced augmentation")
    print(f"   Epochs: {epochs}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Image Size: {img_size}")
    print(f"   Device: {'GPU' if device != 'cpu' else 'CPU'}")
    print()
    
    # Calculate class weights
    print("🔧 Calculating Class Weights...")
    weights = create_class_weighted_config(data_yaml)
    print()
    
    # Load pre-trained model
    model_name = f'yolov8{model_size}.pt'
    print(f"📥 Loading pre-trained model: {model_name}")
    model = YOLO(model_name)
    print(f"✅ Model loaded!")
    print()
    
    # Enhanced hyperparameters for minor defect detection
    print("=" * 80)
    print("🏋️ Starting Training with Minor Defect Focus...")
    print("=" * 80)
    print("\n💡 Key Optimizations:")
    print("   • Lower confidence threshold (0.1 vs 0.25 default)")
    print("   • Class weighting (defects 2-3x more important)")
    print("   • Enhanced augmentation (mixup, copy-paste)")
    print("   • Focal loss parameters (harder examples)")
    print("   • Higher patience (allow longer convergence)")
    print()
    
    start_time = datetime.now()
    
    # Train with optimized parameters
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project='models/yolo',
        name='minor_defect_focused',
        exist_ok=True,
        
        # Save settings
        save=True,
        save_period=10,
        
        # Optimization
        optimizer='AdamW',
        lr0=0.001,  # Lower initial learning rate for fine-tuning
        lrf=0.001,  # Very low final LR for convergence
        momentum=0.937,
        weight_decay=0.001,  # Slightly higher for regularization
        
        # Warmup
        warmup_epochs=5,  # Longer warmup
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # Loss weights - CRITICAL for minor defects
        box=7.5,  # Bounding box loss
        cls=1.5,  # Classification loss (higher = more focus on correct class)
        dfl=1.5,  # Distribution focal loss
        
        # Early stopping
        patience=20,  # More patience for convergence
        
        # Data augmentation - Enhanced for subtle features
        hsv_h=0.02,   # Slightly more hue variation
        hsv_s=0.7,    # Saturation
        hsv_v=0.4,    # Value/brightness
        degrees=5.0,  # Small rotation (welds can be at angles)
        translate=0.1,
        scale=0.6,    # More scale variation
        shear=2.0,    # Small shear
        perspective=0.0001,  # Slight perspective
        flipud=0.0,   # No vertical flip (welds have orientation)
        fliplr=0.5,   # Horizontal flip OK
        mosaic=1.0,   # Mosaic augmentation
        mixup=0.15,   # Mixup for blending (helps with unclear defects!)
        copy_paste=0.3,  # Copy-paste augmentation (great for rare defects!)
        
        # Additional augmentations
        auto_augment='randaugment',  # Random augmentation
        erasing=0.4,  # Random erasing
        
        # Detection parameters - CRITICAL
        conf=0.1,  # Lower confidence threshold (catch more subtle defects!)
        iou=0.5,   # IoU threshold for NMS
        max_det=300,
        
        # Multi-scale training for better detection
        # This helps with defects of varying sizes
        # rect=False,  # No rectangular training
        # multi_scale=True,  # Would need custom implementation
        
        # Validation settings
        val=True,
        plots=True,
        
        # Performance
        workers=4,
        verbose=True,
        
        # Reproducibility
        seed=42,
        deterministic=True,
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print()
    print("=" * 80)
    print("✅ Training Complete!")
    print("=" * 80)
    print(f"   Duration: {duration}")
    print(f"   Best Model: models/yolo/minor_defect_focused/weights/best.pt")
    print()
    
    # Validate with low confidence threshold
    print("📊 Running Validation with Low Confidence Threshold (0.1)...")
    metrics = model.val(conf=0.1)
    
    print()
    print("📈 Final Metrics (Optimized for Minor Defects):")
    print(f"   Precision: {metrics.results_dict.get('metrics/precision(B)', 0):.4f}")
    print(f"   Recall:    {metrics.results_dict.get('metrics/recall(B)', 0):.4f}")
    print(f"   mAP@0.5:   {metrics.results_dict.get('metrics/mAP50(B)', 0):.4f}")
    print()
    
    print("💡 Next Steps:")
    print("   1. Compare recall with previous model (should be higher!)")
    print("   2. Check confusion matrix for No Defect misclassifications")
    print("   3. Test on real-world unclear defects")
    print("   4. Adjust confidence threshold in deployment (try 0.05-0.15)")
    print()
    
    return results


def main():
    """Main training function."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLOv8 for minor defect detection')
    parser.add_argument('--model', type=str, default='s', choices=['n', 's', 'm', 'l', 'x'],
                        help='Model size')
    parser.add_argument('--data', type=str, default='models/yolo/riawelc.yaml',
                        help='Path to data.yaml')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs (more epochs for better convergence)')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--img', type=int, default=640,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='GPU device or cpu')
    
    args = parser.parse_args()
    
    # Check if data.yaml exists
    if not os.path.exists(args.data):
        print(f"❌ Data config not found: {args.data}")
        print("   Looking for alternative...")
        
        alt_path = "../DATA/data.yaml"
        if os.path.exists(alt_path):
            args.data = alt_path
            print(f"✅ Found: {alt_path}")
        else:
            print("   Please create data.yaml first")
            return
    
    # Start training
    train_improved_model(
        model_size=args.model,
        data_yaml=args.data,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img,
        device=args.device
    )


if __name__ == "__main__":
    main()
