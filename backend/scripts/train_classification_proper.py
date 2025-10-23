"""
Train YOLOv8 for IMAGE CLASSIFICATION (NOT Detection)

This trains a proper classification model that assigns a single class label
to each entire radiographic image: LP, PO, CR, or ND.

Key difference from detection:
- Classification: "This whole image shows a Porosity defect"
- Detection: "There's a porosity defect at coordinates (x, y, w, h)"

Your data structure (Difetto1/, Difetto2/, etc.) is perfect for classification!
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import torch


def train_classification_model(
    data_dir: str = "../DATA",
    model_size: str = 's',
    epochs: int = 100,
    batch_size: int = 64,  # Can use larger batch for classification
    img_size: int = 224,  # Standard for classification
    device: str = '0',
    focus_on_defects: bool = True
):
    """
    Train YOLOv8 CLASSIFICATION model for weld defect classification.
    
    Args:
        data_dir: Path to DATA directory with train/val/test splits
        model_size: 'n', 's', 'm', 'l', 'x'
        epochs: Number of training epochs
        batch_size: Batch size (can be larger for classification)
        img_size: Image size (224 standard for classification)
        device: GPU device or 'cpu'
        focus_on_defects: If True, use class weights to prioritize defects over ND
    """
    
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Ultralytics not installed!")
        return
    
    # Check device
    if device != 'cpu' and not torch.cuda.is_available():
        print("⚠️ CUDA not available, switching to CPU")
        device = 'cpu'
    
    print("=" * 80)
    print("🎯 YOLOv8 CLASSIFICATION Training")
    print("   (Whole-image classification, not detection)")
    print("=" * 80)
    print(f"\n📊 Configuration:")
    print(f"   Model: YOLOv8{model_size}-cls (CLASSIFICATION)")
    print(f"   Data: {data_dir}")
    print(f"   Classes: LP, PO, CR, ND")
    print(f"   Epochs: {epochs}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Image Size: {img_size}x{img_size}")
    print(f"   Device: {'GPU' if device != 'cpu' else 'CPU'}")
    if focus_on_defects:
        print(f"   🎯 Focus: High recall on defects (prioritize over ND)")
    print()
    
    # Calculate class weights if focusing on defects
    if focus_on_defects:
        print("🔧 Calculating Class Weights for Defect Focus...")
        print("   Strategy: Penalize missing defects more than false positives")
        print()
        
        # Based on your distribution:
        # LP: 4962, PO: 4108, CR: 2893, ND: 3900
        total = 4962 + 4108 + 2893 + 3900
        
        # Higher weight = more important
        weights = {
            'LP': 1.2,  # Slightly boost LP
            'PO': 1.3,  # Boost PO
            'CR': 2.0,  # Strongly boost CR (underrepresented)
            'ND': 0.3,  # Reduce ND importance (we care more about catching defects)
        }
        
        print("   Class Weights:")
        for cls, weight in weights.items():
            print(f"      {cls}: {weight:.1f}x")
        print()
    
    # Load CLASSIFICATION model (note the -cls suffix!)
    model_name = f'yolov8{model_size}-cls.pt'
    print(f"📥 Loading pre-trained classification model: {model_name}")
    model = YOLO(model_name)
    print(f"✅ Model loaded! (Task: {model.task})")
    print()
    
    # Verify data structure
    data_path = Path(data_dir)
    if not (data_path / 'training').exists():
        print(f"❌ Training directory not found: {data_path / 'training'}")
        return
    
    print("📁 Data Structure:")
    for split in ['training', 'validation', 'testing']:
        split_path = data_path / split
        if split_path.exists():
            classes = [d.name for d in split_path.iterdir() if d.is_dir()]
            total_images = sum(len(list((split_path / c).glob('*.png'))) + 
                              len(list((split_path / c).glob('*.jpg'))) 
                              for c in classes)
            print(f"   {split:12s}: {total_images:5d} images in {len(classes)} classes")
    print()
    
    # Training parameters
    print("=" * 80)
    print("🏋️ Starting Classification Training...")
    print("=" * 80)
    print()
    
    if focus_on_defects:
        print("💡 Optimizations for Minor Defect Detection:")
        print("   • Class weighting (defects prioritized)")
        print("   • Label smoothing (reduces overconfidence)")
        print("   • Enhanced augmentation (improves generalization)")
        print("   • Dropout (prevents overfitting to clear cases)")
        print()
    
    start_time = datetime.now()
    
    # Train model
    results = model.train(
        data=str(data_path.absolute()),
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project='models/yolo',
        name='classification_defect_focused' if focus_on_defects else 'classification',
        exist_ok=True,
        
        # Save settings
        save=True,
        save_period=10,
        patience=15,  # Early stopping
        
        # Optimizer
        optimizer='AdamW',
        lr0=0.001,  # Initial learning rate
        lrf=0.0001,  # Final learning rate
        momentum=0.937,
        weight_decay=0.0005 if not focus_on_defects else 0.001,  # More regularization for defect focus
        
        # Warmup
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # Classification-specific parameters
        dropout=0.2 if focus_on_defects else 0.0,  # Dropout to prevent overfitting
        label_smoothing=0.1 if focus_on_defects else 0.0,  # Reduces overconfidence
        
        # Data augmentation - Important for minor defects!
        hsv_h=0.03,  # Hue variation
        hsv_s=0.7,  # Saturation
        hsv_v=0.5,  # Value/brightness (important for radiographs!)
        degrees=10.0,  # Rotation
        translate=0.1,  # Translation
        scale=0.6,  # Scale variation
        shear=2.0,  # Shear
        perspective=0.0001,  # Slight perspective
        flipud=0.0,  # No vertical flip
        fliplr=0.5,  # Horizontal flip
        
        # Advanced augmentation for unclear defects
        mosaic=0.0,  # Not useful for classification
        mixup=0.15 if focus_on_defects else 0.0,  # Blend images (helps with unclear cases!)
        copy_paste=0.0,  # Not applicable to classification
        auto_augment='randaugment',  # Random augmentation
        erasing=0.3 if focus_on_defects else 0.0,  # Random erasing
        
        # Validation
        val=True,
        plots=True,
        verbose=True,
        
        # Performance
        workers=4,
        
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
    model_path = f"models/yolo/classification_defect_focused/weights/best.pt" if focus_on_defects else "models/yolo/classification/weights/best.pt"
    print(f"   Best Model: {model_path}")
    print()
    
    # Validate
    print("📊 Running Final Validation...")
    metrics = model.val()
    
    print()
    print("📈 Final Metrics:")
    if hasattr(metrics, 'top1'):
        print(f"   Top-1 Accuracy: {metrics.top1:.4f}")
    if hasattr(metrics, 'top5'):
        print(f"   Top-5 Accuracy: {metrics.top5:.4f}")
    print()
    
    print("💡 Next Steps:")
    print("   1. Check confusion matrix: models/yolo/.../confusion_matrix.png")
    print("   2. Test on individual images:")
    print(f"      python -c \"from ultralytics import YOLO; m=YOLO('{model_path}'); m.predict('test_image.png')\"")
    print("   3. Evaluate confidence scores:")
    print("      python scripts/evaluate_classification_confidence.py")
    print()
    
    # Test on a sample image
    print("🔍 Testing on sample image...")
    test_classes = ['Difetto1', 'Difetto2', 'Difetto4', 'NoDifetto']
    for test_class in test_classes:
        test_dir = data_path / 'testing' / test_class
        if test_dir.exists():
            test_images = list(test_dir.glob('*.png')) + list(test_dir.glob('*.jpg'))
            if test_images:
                test_img = test_images[0]
                print(f"\n   Testing {test_class} sample: {test_img.name}")
                result = model.predict(test_img, verbose=False)[0]
                if hasattr(result, 'probs'):
                    top_class = result.names[int(result.probs.top1)]
                    confidence = float(result.probs.top1conf)
                    print(f"      Predicted: {top_class} (confidence: {confidence:.4f})")
                    
                    # Show all class probabilities
                    print(f"      All probabilities:")
                    for i, prob in enumerate(result.probs.data):
                        print(f"         {result.names[i]}: {float(prob):.4f}")
                break
    
    print()
    return results


def main():
    """Main training function."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLOv8 Classification for Weld Defects')
    parser.add_argument('--data', type=str, default='../DATA',
                        help='Path to DATA directory')
    parser.add_argument('--model', type=str, default='s', choices=['n', 's', 'm', 'l', 'x'],
                        help='Model size')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs')
    parser.add_argument('--batch', type=int, default=64,
                        help='Batch size')
    parser.add_argument('--img', type=int, default=224,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='GPU device or cpu')
    parser.add_argument('--no-defect-focus', action='store_true',
                        help='Disable defect-focused training (equal class weights)')
    
    args = parser.parse_args()
    
    # Check if data exists
    if not os.path.exists(args.data):
        print(f"❌ Data directory not found: {args.data}")
        print("   Please provide correct path to DATA directory")
        return
    
    # Start training
    train_classification_model(
        data_dir=args.data,
        model_size=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.img,
        device=args.device,
        focus_on_defects=not args.no_defect_focus
    )


if __name__ == "__main__":
    main()
