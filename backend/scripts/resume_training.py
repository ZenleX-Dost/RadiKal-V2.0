"""
Resume YOLOv8 Training from Last Checkpoint
"""

import os
from pathlib import Path

def resume_training():
    print("=" * 70)
    print("🔄 Resuming YOLOv8 Training - RadiKal Weld Detection")
    print("=" * 70)
    
    from ultralytics import YOLO
    import torch
    
    # Find last checkpoint
    weights_dir = Path('models/yolo/radikal_weld_detection/weights')
    last_checkpoint = weights_dir / 'last.pt'
    
    if not last_checkpoint.exists():
        print(f"\n❌ No checkpoint found at: {last_checkpoint}")
        print("   Start new training with: python scripts/start_training.py")
        return
    
    # Check GPU
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    
    print(f"\n🔧 Hardware:")
    print(f"   GPU: {gpu_name}")
    print(f"   PyTorch: {torch.__version__}")
    
    print(f"\n📊 Resuming from:")
    print(f"   Checkpoint: {last_checkpoint}")
    print(f"   Size: {last_checkpoint.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"   Modified: {last_checkpoint.stat().st_mtime}")
    
    # Load checkpoint
    print(f"\n📥 Loading checkpoint...")
    model = YOLO(str(last_checkpoint))
    
    print(f"✅ Checkpoint loaded!")
    
    # Resume training
    print(f"\n🏋️  Resuming training...")
    print("=" * 70)
    print()
    
    try:
        results = model.train(resume=True)
        
        print("\n" + "=" * 70)
        print("🎉 Training Complete!")
        print("=" * 70)
        print(f"\n📊 Final Model:")
        print(f"   Best: models/yolo/radikal_weld_detection/weights/best.pt")
        print(f"   Last: models/yolo/radikal_weld_detection/weights/last.pt")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted again!")
        print("   Run this script again to resume from the new checkpoint.")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    resume_training()
