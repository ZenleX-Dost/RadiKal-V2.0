"""
Simple YOLOv8 Training Script - Minimal Dependencies
Works offline, no update checks
"""

import os
import sys
import warnings

# Disable online checks and warnings
os.environ['YOLO_OFFLINE'] = '1'
os.environ['YOLO_VERBOSE'] = 'False'
warnings.filterwarnings('ignore')

def simple_train():
    """Train YOLOv8 with minimal overhead"""
    
    print("=" * 60)
    print("🚀 Simple YOLOv8 Training")
    print("=" * 60)
    
    # Import
    try:
        from ultralytics import YOLO
        import torch
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install ultralytics torch")
        return
    
    # Check CUDA
    has_cuda = torch.cuda.is_available()
    device = '0' if has_cuda else 'cpu'
    print(f"\n🔧 Device: {'GPU (CUDA)' if has_cuda else 'CPU'}")
    print(f"   PyTorch: {torch.__version__}")
    
    if not has_cuda:
        print("\n⚠️  WARNING: Training on CPU will be VERY SLOW!")
        print("   Expected time: 12-24 hours (vs 2-4 hours on GPU)")
        print("\n💡 To use GPU, install CUDA PyTorch:")
        print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        response = input("\n   Continue with CPU training? (y/n): ")
        if response.lower() != 'y':
            print("   Aborted.")
            return
    
    # Config
    data_yaml = 'models/yolo/riawelc.yaml'
    model_path = os.path.expanduser('~/.cache/yolov8s.pt')
    
    if not os.path.exists(model_path):
        print(f"\n❌ Model not found: {model_path}")
        print("   Downloading yolov8s.pt...")
        model_path = 'yolov8s.pt'  # Will auto-download
    
    if not os.path.exists(data_yaml):
        print(f"\n❌ Dataset config not found: {data_yaml}")
        print("   Please run the full train_yolo.py first to create it.")
        return
    
    print(f"\n📊 Configuration:")
    print(f"   Model: {model_path}")
    print(f"   Data: {data_yaml}")
    print(f"   Epochs: 50")
    print(f"   Batch: 16" if has_cuda else "   Batch: 4")
    print(f"   Device: {device}")
    
    # Load model
    print(f"\n📥 Loading model...")
    model = YOLO(model_path)
    
    # Train
    print("\n🏋️ Starting training...")
    print("=" * 60)
    
    try:
        results = model.train(
            data=data_yaml,
            epochs=50,
            batch=16 if has_cuda else 4,
            imgsz=640,
            device=device,
            project='models/yolo',
            name='train',
            patience=10,
            save=True,
            save_period=5,
            verbose=True,
            plots=True
        )
        
        print("\n" + "=" * 60)
        print("✅ Training Complete!")
        print("=" * 60)
        print(f"\n📊 Results:")
        print(f"   Best Model: models/yolo/train/weights/best.pt")
        print(f"   Metrics: {results}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user")
        print("   Checkpoints saved in: models/yolo/train/weights/")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    simple_train()
