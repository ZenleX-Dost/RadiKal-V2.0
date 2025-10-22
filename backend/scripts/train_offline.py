"""
Offline YOLOv8 Training - No Network Dependencies
"""

import os
import sys
import warnings

# Critical: Disable ALL online operations
os.environ['YOLO_OFFLINE'] = '1'
os.environ['YOLO_VERBOSE'] = 'False'
warnings.filterwarnings('ignore')

def train_offline():
    """Train YOLOv8 completely offline"""
    
    print("=" * 60)
    print("🚀 Offline YOLOv8 Training")
    print("=" * 60)
    
    # Import with network operations disabled
    import torch
    from ultralytics import YOLO
    from ultralytics.utils import SETTINGS
    
    # Disable all online checks
    SETTINGS['sync'] = False
    
    # Check CUDA
    has_cuda = torch.cuda.is_available()
    device = '0' if has_cuda else 'cpu'
    
    print(f"\n🔧 Device: {'GPU (CUDA)' if has_cuda else 'CPU'}")
    print(f"   PyTorch: {torch.__version__}")
    print(f"   GPU: {torch.cuda.get_device_name(0) if has_cuda else 'N/A'}")
    
    # Config
    data_yaml = 'models/yolo/riawelc.yaml'
    model_path = os.path.expanduser('~/.cache/yolov8s.pt')
    
    print(f"\n📊 Configuration:")
    print(f"   Model: {model_path}")
    print(f"   Data: {data_yaml}")
    print(f"   Epochs: 50")
    print(f"   Batch: 16" if has_cuda else "   Batch: 4")
    print(f"   Device: {device}")
    
    # Load model
    print(f"\n📥 Loading model...")
    model = YOLO(model_path)
    params = sum(p.numel() for p in model.model.parameters())
    print(f"✅ Model loaded ({params:,} parameters)")
    
    # Train with minimal online operations
    print("\n🏋️ Starting training (offline mode)...")
    print("=" * 60)
    print()
    
    try:
        # Monkey-patch check_font to disable font downloads
        from ultralytics.utils import checks
        def no_font_check(font):
            pass  # Skip font check
        checks.check_font = no_font_check
        
        results = model.train(
            data=data_yaml,
            epochs=50,
            batch=16 if has_cuda else 4,
            imgsz=640,
            device=device,
            project='models/yolo',
            name='radikal_train',
            patience=10,
            save=True,
            save_period=5,
            verbose=True,
            plots=True,
            # Disable online operations
            cache=False,
            exist_ok=True,
        )
        
        print("\n" + "=" * 60)
        print("✅ Training Complete!")
        print("=" * 60)
        print(f"\n📊 Best Results:")
        print(f"   Model: models/yolo/radikal_train/weights/best.pt")
        print(f"   Last: models/yolo/radikal_train/weights/last.pt")
        print(f"\n📈 Metrics:")
        print(f"   Check: models/yolo/radikal_train/results.csv")
        print(f"   Plots: models/yolo/radikal_train/*.png")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted!")
        print("   Checkpoints saved in: models/yolo/radikal_train/weights/")
        print("   Resume with: model.train(resume=True)")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    train_offline()
