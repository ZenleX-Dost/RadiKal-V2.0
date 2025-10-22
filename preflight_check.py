"""
RadiKal Training Pre-Flight Check
Verifies all requirements before starting training
"""

import os
import json
import torch
from pathlib import Path

def check_gpu():
    """Check GPU availability"""
    print("🖥️  GPU Check:")
    if torch.cuda.is_available():
        print(f"   ✅ CUDA Available: {torch.cuda.is_available()}")
        print(f"   ✅ GPU Device: {torch.cuda.get_device_name(0)}")
        print(f"   ✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print(f"   ✅ CUDA Version: {torch.version.cuda}")
        return True
    else:
        print("   ❌ CUDA not available!")
        return False

def check_dataset():
    """Check dataset files"""
    print("\n📊 Dataset Check:")
    
    base_dir = Path("backend/data")
    if not base_dir.exists():
        base_dir = Path("data")
    
    splits = ["train", "val", "test"]
    all_ok = True
    
    for split in splits:
        img_dir = base_dir / split / "images"
        ann_file = base_dir / split / "annotations" / "annotations.json"
        
        if not img_dir.exists():
            print(f"   ❌ {split} images directory not found: {img_dir}")
            all_ok = False
            continue
        
        if not ann_file.exists():
            print(f"   ❌ {split} annotations not found: {ann_file}")
            all_ok = False
            continue
        
        # Count images
        images = list(img_dir.glob("*.png"))
        
        # Load annotations
        with open(ann_file) as f:
            data = json.load(f)
        
        num_images = len(data.get("images", []))
        num_annotations = len(data.get("annotations", []))
        
        print(f"   ✅ {split.upper()}: {len(images)} image files, {num_images} COCO images, {num_annotations} annotations")
    
    return all_ok

def check_config():
    """Check training configuration"""
    print("\n⚙️  Configuration Check:")
    
    config_path = Path("backend/configs/train_config.json")
    if not config_path.exists():
        config_path = Path("configs/train_config.json")
    
    if not config_path.exists():
        print(f"   ❌ Config not found: {config_path}")
        return False
    
    with open(config_path) as f:
        config = json.load(f)
    
    print(f"   ✅ Num Classes: {config['num_classes']} (should be 4 for RIAWELC)")
    print(f"   ✅ Image Size: {config['image_size']} (should be [224, 224] for RIAWELC)")
    print(f"   ✅ Batch Size: {config['batch_size']}")
    print(f"   ✅ Num Epochs: {config['num_epochs']}")
    print(f"   ✅ Learning Rate: {config['learning_rate']}")
    
    if config['num_classes'] != 4:
        print("   ⚠️  WARNING: num_classes should be 4 for RIAWELC!")
    
    if config['image_size'] != [224, 224]:
        print("   ⚠️  WARNING: image_size should be [224, 224] for RIAWELC!")
    
    return True

def check_scripts():
    """Check training scripts"""
    print("\n📝 Script Check:")
    
    scripts = [
        "backend/scripts/train.py",
        "scripts/train.py"
    ]
    
    found = False
    for script in scripts:
        if Path(script).exists():
            print(f"   ✅ Training script found: {script}")
            found = True
            break
    
    if not found:
        print("   ❌ Training script not found!")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🚀 RadiKal Training Pre-Flight Check")
    print("=" * 60)
    
    gpu_ok = check_gpu()
    dataset_ok = check_dataset()
    config_ok = check_config()
    scripts_ok = check_scripts()
    
    print("\n" + "=" * 60)
    if gpu_ok and dataset_ok and config_ok and scripts_ok:
        print("✅ All checks passed! Ready to start training!")
        print("\nTo start training, run:")
        print("  cd backend")
        print("  python scripts/train.py --config configs/train_config.json --gpu 0")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
