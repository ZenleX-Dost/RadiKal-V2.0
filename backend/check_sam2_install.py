import os
import sys

print("=" * 60)
print("SAM2 Installation Diagnostic")
print("=" * 60)

# Check SAM2 import
try:
    import sam2
    print("✓ SAM2 imported successfully")
    sam2_dir = os.path.dirname(sam2.__file__)
    print(f"  Location: {sam2_dir}")
except ImportError as e:
    print(f"✗ SAM2 import failed: {e}")
    sys.exit(1)

# Check config directory
config_dir = os.path.join(sam2_dir, "configs")
print(f"\n✓ Config directory: {config_dir}")
print(f"  Exists: {os.path.exists(config_dir)}")

if os.path.exists(config_dir):
    configs = [f for f in os.listdir(config_dir) if f.endswith('.yaml')]
    print(f"  Config files found: {len(configs)}")
    for cfg in configs[:5]:
        print(f"    - {cfg}")
else:
    print("  ⚠ Config directory not found!")

# Check SAM2 build function
try:
    from sam2.build_sam import build_sam2
    print("\n✓ build_sam2 imported")
except ImportError as e:
    print(f"\n✗ build_sam2 import failed: {e}")

# Check predictor
try:
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    print("✓ SAM2ImagePredictor imported")
except ImportError as e:
    print(f"✗ SAM2ImagePredictor import failed: {e}")

# Check automatic mask generator
try:
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    print("✓ SAM2AutomaticMaskGenerator imported")
except ImportError as e:
    print(f"✗ SAM2AutomaticMaskGenerator import failed: {e}")

# Check checkpoints
checkpoint_dir = "backend/models/sam2"
print(f"\n✓ Checkpoint directory: {checkpoint_dir}")
print(f"  Exists: {os.path.exists(checkpoint_dir)}")

if os.path.exists(checkpoint_dir):
    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith('.pt')]
    print(f"  Checkpoint files found: {len(checkpoints)}")
    for ckpt in checkpoints:
        size = os.path.getsize(os.path.join(checkpoint_dir, ckpt)) / (1024*1024)
        print(f"    - {ckpt} ({size:.1f} MB)")
else:
    print("  ⚠ Checkpoint directory not found!")

# Check PyTorch
import torch
print(f"\n✓ PyTorch: {torch.__version__}")
print(f"  CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"  CUDA version: {torch.version.cuda}")
    print(f"  GPU: {torch.cuda.get_device_name(0)}")

print("\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
