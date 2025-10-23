"""
Two-Stage Defect Detection Approach

Stage 1: Binary classifier - Defect vs No Defect (High Sensitivity)
Stage 2: Multi-class classifier - Type of defect (LP, PO, CR)

This approach ensures minor defects are caught in Stage 1 with high recall,
then Stage 2 determines the specific type of defect.

Benefits:
- Stage 1 can use very low confidence threshold (0.05) without confusion
- Stage 2 only runs on detected defects, can be more precise
- Dramatically reduces false negatives (missed defects)
"""

import os
import sys
from pathlib import Path
import yaml
import shutil
from datetime import datetime
import torch


def create_binary_dataset(source_data_yaml: str, output_dir: str = "DATA_binary"):
    """
    Create a binary classification dataset:
    - Class 0: Defect (combines LP, PO, CR)
    - Class 1: No Defect
    """
    
    print("=" * 80)
    print("🔨 Creating Binary Classification Dataset")
    print("=" * 80)
    print()
    
    # Load original data config
    with open(source_data_yaml, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # For each split (training, validation, testing)
    splits = ['training', 'validation', 'testing']
    
    for split in splits:
        print(f"📁 Processing {split} split...")
        
        source_dir = Path(config['path']) / split
        if not source_dir.exists():
            print(f"   ⚠️ Skipping {split} (not found)")
            continue
        
        # Create output directories
        defect_dir = output_path / split / 'Defect'
        no_defect_dir = output_path / split / 'NoDefect'
        defect_dir.mkdir(parents=True, exist_ok=True)
        no_defect_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        defect_count = 0
        no_defect_count = 0
        
        # Defect classes: Difetto1, Difetto2, Difetto4
        defect_classes = ['Difetto1', 'Difetto2', 'Difetto4']
        for defect_class in defect_classes:
            class_dir = source_dir / defect_class
            if class_dir.exists():
                for img_file in class_dir.glob('*'):
                    if img_file.is_file():
                        shutil.copy2(img_file, defect_dir / f"{defect_class}_{img_file.name}")
                        defect_count += 1
        
        # No Defect class: NoDifetto
        no_defect_class_dir = source_dir / 'NoDifetto'
        if no_defect_class_dir.exists():
            for img_file in no_defect_class_dir.glob('*'):
                if img_file.is_file():
                    shutil.copy2(img_file, no_defect_dir / img_file.name)
                    no_defect_count += 1
        
        print(f"   ✅ {split}: {defect_count} defects, {no_defect_count} no defects")
    
    # Create data.yaml for binary classification
    binary_config = {
        'path': str(output_path.absolute()),
        'train': 'training',
        'val': 'validation',
        'test': 'testing',
        'nc': 2,
        'names': {
            0: 'Defect',
            1: 'NoDefect'
        }
    }
    
    config_path = output_path / 'data.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(binary_config, f, default_flow_style=False)
    
    print(f"\n✅ Binary dataset created: {output_path}")
    print(f"📄 Config saved: {config_path}")
    print()
    
    return str(config_path)


def train_stage1_binary_detector(
    data_yaml: str,
    model_size: str = 's',
    epochs: int = 50,
    device: str = '0'
):
    """
    Train Stage 1: Binary classifier (Defect vs No Defect)
    
    Optimized for HIGH RECALL - we want to catch ALL defects, even unclear ones.
    """
    
    from ultralytics import YOLO
    
    print("=" * 80)
    print("🎯 Stage 1: Training Binary Defect Detector")
    print("=" * 80)
    print()
    print("📊 Goal: Catch ALL defects (even minor/unclear ones)")
    print("   Strategy: Very low confidence threshold + high recall focus")
    print()
    
    # Load model
    model = YOLO(f'yolov8{model_size}.pt')
    
    # Train with HIGH RECALL optimization
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=16,
        imgsz=640,
        device=device,
        project='models/yolo',
        name='stage1_binary_detector',
        exist_ok=True,
        
        # High recall optimization
        conf=0.05,  # VERY low confidence threshold
        iou=0.4,    # Lower IoU for more detections
        
        # Loss weights - favor recall over precision
        box=7.5,
        cls=2.0,  # Higher classification weight
        dfl=1.5,
        
        # Aggressive augmentation to learn subtle features
        hsv_h=0.03,
        hsv_s=0.7,
        hsv_v=0.5,
        degrees=10,
        translate=0.2,
        scale=0.7,
        shear=3.0,
        mixup=0.2,
        copy_paste=0.3,
        
        # Training params
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.0001,
        patience=15,
        
        # Validation
        val=True,
        plots=True,
        verbose=True,
    )
    
    print("\n✅ Stage 1 Training Complete!")
    print(f"📁 Model: models/yolo/stage1_binary_detector/weights/best.pt")
    print()
    
    return "models/yolo/stage1_binary_detector/weights/best.pt"


def train_stage2_defect_classifier(
    data_yaml: str,
    model_size: str = 's',
    epochs: int = 50,
    device: str = '0'
):
    """
    Train Stage 2: Defect Type Classifier (LP vs PO vs CR)
    
    Only runs on images already classified as defects by Stage 1.
    Can be more precise since it doesn't need to distinguish from No Defect.
    """
    
    from ultralytics import YOLO
    
    print("=" * 80)
    print("🎯 Stage 2: Training Defect Type Classifier")
    print("=" * 80)
    print()
    print("📊 Goal: Accurately classify defect types")
    print("   Strategy: Focus on distinguishing LP vs PO vs CR")
    print()
    
    # Create defect-only dataset
    print("🔨 Creating defect-only dataset...")
    defect_yaml = create_defect_only_dataset(data_yaml)
    
    # Load model
    model = YOLO(f'yolov8{model_size}.pt')
    
    # Train with precision focus
    results = model.train(
        data=defect_yaml,
        epochs=epochs,
        batch=16,
        imgsz=640,
        device=device,
        project='models/yolo',
        name='stage2_defect_classifier',
        exist_ok=True,
        
        # Balanced precision/recall
        conf=0.25,  # Standard threshold
        iou=0.5,
        
        # Loss weights
        box=7.5,
        cls=1.0,
        dfl=1.5,
        
        # Moderate augmentation
        hsv_h=0.02,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=5,
        translate=0.1,
        scale=0.5,
        mixup=0.1,
        copy_paste=0.2,
        
        # Training params
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.001,
        patience=15,
        
        val=True,
        plots=True,
        verbose=True,
    )
    
    print("\n✅ Stage 2 Training Complete!")
    print(f"📁 Model: models/yolo/stage2_defect_classifier/weights/best.pt")
    print()
    
    return "models/yolo/stage2_defect_classifier/weights/best.pt"


def create_defect_only_dataset(source_data_yaml: str, output_dir: str = "DATA_defects_only"):
    """
    Create dataset with only defect classes (for Stage 2 training).
    """
    
    print("📁 Creating defect-only dataset...")
    
    with open(source_data_yaml, 'r') as f:
        config = yaml.safe_load(f)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    splits = ['training', 'validation', 'testing']
    
    for split in splits:
        source_dir = Path(config['path']) / split
        if not source_dir.exists():
            continue
        
        # Copy only defect classes
        defect_classes = ['Difetto1', 'Difetto2', 'Difetto4']
        for defect_class in defect_classes:
            class_dir = source_dir / defect_class
            if class_dir.exists():
                dest_dir = output_path / split / defect_class
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                for img_file in class_dir.glob('*'):
                    if img_file.is_file():
                        shutil.copy2(img_file, dest_dir / img_file.name)
    
    # Create data.yaml
    defect_config = {
        'path': str(output_path.absolute()),
        'train': 'training',
        'val': 'validation',
        'test': 'testing',
        'nc': 3,
        'names': {
            0: 'LP',  # Difetto1
            1: 'PO',  # Difetto2
            2: 'CR',  # Difetto4
        }
    }
    
    config_path = output_path / 'data.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(defect_config, f, default_flow_style=False)
    
    print(f"✅ Defect-only dataset: {config_path}")
    
    return str(config_path)


def main():
    """Main two-stage training pipeline."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Train two-stage defect detector')
    parser.add_argument('--data', type=str, default='../DATA/data.yaml',
                        help='Path to original data.yaml')
    parser.add_argument('--model', type=str, default='s',
                        help='Model size')
    parser.add_argument('--epochs', type=int, default=50,
                        help='Epochs per stage')
    parser.add_argument('--device', type=str, default='0',
                        help='GPU device')
    parser.add_argument('--stage', type=str, choices=['1', '2', 'both'], default='both',
                        help='Which stage to train')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("🎯 TWO-STAGE DEFECT DETECTION TRAINING")
    print("=" * 80)
    print("\n💡 Approach:")
    print("   Stage 1: Binary (Defect vs No Defect) - HIGH SENSITIVITY")
    print("   Stage 2: Multi-class (LP vs PO vs CR) - HIGH PRECISION")
    print("\n✅ Benefits:")
    print("   • Catches minor/unclear defects in Stage 1")
    print("   • Accurate classification in Stage 2")
    print("   • Lower confidence threshold without false positives")
    print()
    
    if args.stage in ['1', 'both']:
        print("\n" + "▶" * 40)
        print("STARTING STAGE 1: Binary Detector")
        print("▶" * 40 + "\n")
        
        # Create binary dataset
        binary_yaml = create_binary_dataset(args.data)
        
        # Train Stage 1
        stage1_model = train_stage1_binary_detector(
            data_yaml=binary_yaml,
            model_size=args.model,
            epochs=args.epochs,
            device=args.device
        )
    
    if args.stage in ['2', 'both']:
        print("\n" + "▶" * 40)
        print("STARTING STAGE 2: Defect Classifier")
        print("▶" * 40 + "\n")
        
        # Train Stage 2
        stage2_model = train_stage2_defect_classifier(
            data_yaml=args.data,
            model_size=args.model,
            epochs=args.epochs,
            device=args.device
        )
    
    print("\n" + "=" * 80)
    print("✅ TWO-STAGE TRAINING COMPLETE!")
    print("=" * 80)
    print("\n📁 Models:")
    print("   Stage 1: models/yolo/stage1_binary_detector/weights/best.pt")
    print("   Stage 2: models/yolo/stage2_defect_classifier/weights/best.pt")
    print("\n💡 Usage:")
    print("   1. Run image through Stage 1 (conf=0.05)")
    print("   2. If defect detected, run through Stage 2")
    print("   3. Return final classification")
    print()


if __name__ == "__main__":
    main()
