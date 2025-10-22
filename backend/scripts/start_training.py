"""
Start YOLOv8 Training with Network Bypass
This script patches Ultralytics to work without network access
"""

import os
import sys

# Step 1: Patch the check_font function before importing ultralytics
def patch_ultralytics():
    """Patch ultralytics to skip font downloads"""
    import ultralytics.utils.checks as checks
    
    # Replace check_font with no-op
    original_check_font = checks.check_font
    def patched_check_font(font='Arial.ttf', progress=True):
        """Skip font check - fonts not needed for training"""
        return None
    
    checks.check_font = patched_check_font
    print("✅ Patched check_font to skip downloads")

def main():
    print("=" * 70)
    print("🚀 YOLOv8 GPU Training - RadiKal Weld Defect Detection")
    print("=" * 70)
    
    # Patch before importing
    patch_ultralytics()
    
    # Now import
    import torch
    from ultralytics import YOLO
    
    # Check GPU
    if not torch.cuda.is_available():
        print("\n❌ CUDA not available!")
        print("   Install: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return
    
    gpu_name = torch.cuda.get_device_name(0)
    print(f"\n🔧 Hardware:")
    print(f"   GPU: {gpu_name}")
    print(f"   PyTorch: {torch.__version__}")
    print(f"   CUDA: {torch.version.cuda}")
    
    # Configuration
    model_path = os.path.expanduser('~/.cache/yolov8s.pt')
    data_yaml = 'models/yolo/riawelc.yaml'
    
    print(f"\n📊 Training Configuration:")
    print(f"   Model: YOLOv8s (11.2M parameters)")
    print(f"   Dataset: RIAWELC (24,407 images)")
    print(f"   Epochs: 50")
    print(f"   Batch Size: 16")
    print(f"   Image Size: 640x640")
    print(f"   Device: GPU 0")
    print(f"   Expected Time: 2-4 hours")
    
    # Load model
    print(f"\n📥 Loading pre-trained model...")
    model = YOLO(model_path)
    print(f"✅ Model loaded successfully!")
    
    # Start training
    print(f"\n🏋️  Starting Training...")
    print("=" * 70)
    print()
    
    try:
        results = model.train(
            data=data_yaml,
            epochs=50,
            batch=16,
            imgsz=640,
            device=0,
            project='models/yolo',
            name='radikal_weld_detection',
            patience=10,              # Early stopping
            save=True,                # Save checkpoints
            save_period=5,            # Save every 5 epochs
            exist_ok=True,            # Overwrite existing
            verbose=True,             # Detailed output
            plots=True,               # Generate plots
            cache=False,              # Don't cache (saves memory)
            workers=8,                # Data loading workers
            optimizer='AdamW',        # Optimizer
            lr0=0.01,                 # Initial learning rate
            lrf=0.01,                 # Final learning rate
            momentum=0.937,           # SGD momentum
            weight_decay=0.0005,      # Weight decay
            warmup_epochs=3.0,        # Warmup epochs
            close_mosaic=10,          # Close mosaic augmentation
        )
        
        print("\n" + "=" * 70)
        print("🎉 Training Complete!")
        print("=" * 70)
        
        print(f"\n📊 Results:")
        print(f"   Best Model: models/yolo/radikal_weld_detection/weights/best.pt")
        print(f"   Last Model: models/yolo/radikal_weld_detection/weights/last.pt")
        print(f"   Metrics: models/yolo/radikal_weld_detection/results.csv")
        print(f"   Plots: models/yolo/radikal_weld_detection/*.png")
        
        # Show final metrics if available
        if hasattr(results, 'results_dict'):
            metrics = results.results_dict
            print(f"\n📈 Final Metrics:")
            if 'metrics/mAP50(B)' in metrics:
                print(f"   mAP@0.5: {metrics['metrics/mAP50(B)']:.4f}")
            if 'metrics/mAP50-95(B)' in metrics:
                print(f"   mAP@0.5:0.95: {metrics['metrics/mAP50-95(B)']:.4f}")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user!")
        print("   Partial checkpoints saved in: models/yolo/radikal_weld_detection/weights/")
        print("\n💡 To resume training:")
        print("   model = YOLO('models/yolo/radikal_weld_detection/weights/last.pt')")
        print("   model.train(resume=True)")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Troubleshooting:")
        print("   1. Check GPU memory: nvidia-smi")
        print("   2. Reduce batch size if OOM: batch=8")
        print("   3. Check dataset: ls data/train/images")

if __name__ == '__main__':
    main()
