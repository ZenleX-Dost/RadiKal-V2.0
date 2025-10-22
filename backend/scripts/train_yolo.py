"""
YOLOv8 Fine-tuning Script for RadiKal Weld Defect Detection

This script fine-tunes a pre-trained YOLOv8 model on the RIAWELC dataset.
Much faster than training Faster R-CNN from scratch!

Expected training time: 2-4 hours (vs 4-6 hours for Faster R-CNN)
"""

import argparse
import os
from pathlib import Path
import yaml
from datetime import datetime

def create_yolo_config(data_dir: str, output_dir: str):
    """Create YOLOv8 data configuration file."""
    
    config = {
        'path': str(Path(data_dir).absolute()),
        'train': 'train',
        'val': 'val',
        'test': 'test',
        
        # Class names (adjust based on your RIAWELC dataset)
        'names': {
            0: 'crack',
            1: 'porosity',
            2: 'inclusion',
            3: 'lack_of_fusion'
        }
    }
    
    config_path = Path(output_dir) / 'riawelc.yaml'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Created YOLOv8 config: {config_path}")
    return str(config_path)


def train_yolov8(
    model_size: str = 'n',
    data_config: str = 'riawelc.yaml',
    epochs: int = 50,
    batch_size: int = 16,
    img_size: int = 640,
    device: str = '0',
    output_dir: str = 'runs/detect/train'
):
    """
    Fine-tune YOLOv8 on RIAWELC dataset.
    
    Args:
        model_size: 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge)
        data_config: Path to data YAML file
        epochs: Number of training epochs
        batch_size: Batch size (16 works well on RTX 4050)
        img_size: Input image size (640 standard, 1280 for high-res)
        device: GPU device ('0' for first GPU, 'cpu' for CPU)
        output_dir: Output directory for checkpoints and logs
    """
    
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ YOLOv8 not installed!")
        print("\n📦 Installing YOLOv8...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'ultralytics'])
        from ultralytics import YOLO
    
    # Check CUDA availability and adjust device
    import torch
    if device != 'cpu' and not torch.cuda.is_available():
        print(f"\n⚠️ CUDA not available (torch version: {torch.__version__})")
        print("   Switching to CPU training...")
        print("   💡 Install CUDA-enabled PyTorch for GPU acceleration:")
        print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121\n")
        device = 'cpu'
    
    print("=" * 60)
    print("🚀 YOLOv8 Fine-tuning for Weld Defect Detection")
    print("=" * 60)
    print(f"\n📊 Configuration:")
    print(f"   Model: YOLOv8{model_size}")
    print(f"   Dataset: {data_config}")
    print(f"   Epochs: {epochs}")
    print(f"   Batch Size: {batch_size}")
    print(f"   Image Size: {img_size}")
    print(f"   Device: {'GPU ' + device if device != 'cpu' else 'CPU'}")
    print(f"   Output: {output_dir}")
    print()
    
    # Load pre-trained model
    model_name = f'yolov8{model_size}.pt'
    # Check for pre-downloaded model in cache
    import os
    cache_path = os.path.expanduser(f'~/.cache/yolov8{model_size}.pt')
    if os.path.exists(cache_path):
        print(f"📥 Loading pre-downloaded model: {cache_path}")
        model = YOLO(cache_path)
    else:
        print(f"📥 Downloading pre-trained model: {model_name}")
        try:
            model = YOLO(model_name)
        except KeyboardInterrupt:
            print("\n⚠️ Download interrupted. Please run again or download manually.")
            return
        except Exception as e:
            print(f"\n❌ Error loading model: {e}")
            print(f"💡 Try downloading manually from: https://github.com/ultralytics/assets/releases/download/v8.3.0/{model_name}")
            return
    
    print(f"✅ Model loaded successfully!")
    print(f"   Parameters: {sum(p.numel() for p in model.model.parameters()):,}")
    print()
    
    # Start training
    print("=" * 60)
    print("🏋️ Starting Training...")
    print("=" * 60)
    print()
    
    start_time = datetime.now()
    
    # Train the model
    results = model.train(
        data=data_config,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project=output_dir,
        name='riawelc_yolov8',
        save=True,
        save_period=5,  # Save checkpoint every 5 epochs
        patience=10,  # Early stopping patience
        workers=4,
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        plots=True,
        verbose=True,
        resume=False,
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print()
    print("=" * 60)
    print("✅ Training Complete!")
    print("=" * 60)
    print(f"   Duration: {duration}")
    print(f"   Best mAP: {results.results_dict.get('metrics/mAP50(B)', 'N/A'):.4f}")
    print(f"   Model saved to: {output_dir}/riawelc_yolov8/weights/best.pt")
    print()
    
    # Validate the model
    print("📊 Running validation...")
    metrics = model.val()
    
    print()
    print("📈 Final Metrics:")
    print(f"   Precision: {metrics.results_dict.get('metrics/precision(B)', 0):.4f}")
    print(f"   Recall: {metrics.results_dict.get('metrics/recall(B)', 0):.4f}")
    print(f"   mAP@0.5: {metrics.results_dict.get('metrics/mAP50(B)', 0):.4f}")
    print(f"   mAP@0.5:0.95: {metrics.results_dict.get('metrics/mAP50-95(B)', 0):.4f}")
    print()
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Fine-tune YOLOv8 for weld defect detection')
    
    parser.add_argument('--model', type=str, default='s', choices=['n', 's', 'm', 'l', 'x'],
                        help='Model size: n(nano), s(small), m(medium), l(large), x(xlarge)')
    parser.add_argument('--data_dir', type=str, default='data/riawelc_coco',
                        help='Path to RIAWELC dataset directory')
    parser.add_argument('--epochs', type=int, default=50,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size (16 recommended for RTX 4050)')
    parser.add_argument('--img_size', type=int, default=640,
                        help='Input image size (640 or 1280)')
    parser.add_argument('--device', type=str, default='0',
                        help='GPU device (0, 1, etc.) or cpu')
    parser.add_argument('--output_dir', type=str, default='models/yolo',
                        help='Output directory for checkpoints')
    
    args = parser.parse_args()
    
    # Create YOLOv8 config file
    config_path = create_yolo_config(args.data_dir, args.output_dir)
    
    # Train model
    train_yolov8(
        model_size=args.model,
        data_config=config_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        img_size=args.img_size,
        device=args.device,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
