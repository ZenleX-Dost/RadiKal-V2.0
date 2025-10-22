"""
Download and prepare GDXray dataset for RadiKal XAI training.

GDXray is a publicly available X-ray image dataset with industrial defects.
Perfect for defect detection and XAI visualization.

Usage:
    python scripts/download_gdxray.py --output data/gdxray --category castings
"""

import os
import urllib.request
import zipfile
import argparse
from pathlib import Path
import json
from typing import Dict, List
import shutil


# GDXray dataset information
GDXRAY_URLS = {
    "castings": {
        "url": "http://dmery.sitios.ing.uc.cl/images/GDXray/Castings.zip",
        "description": "Casting defects (cracks, gas pores, shrinkage) - 6,076 images",
        "size": "~2.5 GB"
    },
    "welds": {
        "url": "http://dmery.sitios.ing.uc.cl/images/GDXray/Welds.zip",
        "description": "Weld defects - 1,832 images",
        "size": "~800 MB"
    }
}


def download_file(url: str, output_path: Path, description: str = ""):
    """Download file with progress bar."""
    print(f"📥 Downloading {description}...")
    print(f"   URL: {url}")
    print(f"   Output: {output_path}")
    
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        print(f"\r   Progress: {percent}%", end='')
    
    urllib.request.urlretrieve(url, output_path, reporthook=progress_hook)
    print(f"\n✅ Download complete!")


def extract_zip(zip_path: Path, extract_to: Path):
    """Extract ZIP file."""
    print(f"📦 Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"✅ Extraction complete!")


def organize_dataset(gdxray_path: Path, output_path: Path, category: str):
    """
    Organize GDXray dataset into train/val/test splits.
    
    GDXray structure:
        Castings/
            C0001/
                C0001_0000.png
                C0001_0000.txt  (annotations)
                ...
    
    Output structure:
        train/
            images/
            annotations/
        val/
            images/
            annotations/
        test/
            images/
            annotations/
    """
    print(f"📂 Organizing {category} dataset...")
    
    # Create output directories
    for split in ['train', 'val', 'test']:
        (output_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split / 'annotations').mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    category_path = gdxray_path / category.capitalize()
    if not category_path.exists():
        print(f"⚠️  Warning: {category_path} not found. Checking alternative paths...")
        # Try finding the extracted folder
        possible_paths = list(gdxray_path.glob(f"*{category.capitalize()}*"))
        if possible_paths:
            category_path = possible_paths[0]
            print(f"✅ Found: {category_path}")
        else:
            print(f"❌ Error: Could not find {category} data")
            return
    
    # Collect all series (subdirectories)
    series_dirs = [d for d in category_path.iterdir() if d.is_dir()]
    print(f"   Found {len(series_dirs)} series in dataset")
    
    # Split: 70% train, 15% val, 15% test
    import random
    random.seed(42)
    random.shuffle(series_dirs)
    
    n_train = int(len(series_dirs) * 0.7)
    n_val = int(len(series_dirs) * 0.15)
    
    train_series = series_dirs[:n_train]
    val_series = series_dirs[n_train:n_train + n_val]
    test_series = series_dirs[n_train + n_val:]
    
    print(f"   Split: {len(train_series)} train, {len(val_series)} val, {len(test_series)} test series")
    
    # Copy files to appropriate splits
    total_images = 0
    for split_name, split_series in [('train', train_series), ('val', val_series), ('test', test_series)]:
        split_images = 0
        for series_dir in split_series:
            # Copy all PNG images from this series
            for img_file in series_dir.glob('*.png'):
                # Copy image
                dest_img = output_path / split_name / 'images' / img_file.name
                shutil.copy2(img_file, dest_img)
                
                # Copy annotation if exists
                ann_file = img_file.with_suffix('.txt')
                if ann_file.exists():
                    dest_ann = output_path / split_name / 'annotations' / ann_file.name
                    shutil.copy2(ann_file, dest_ann)
                
                split_images += 1
                total_images += 1
        
        print(f"   ✅ {split_name}: {split_images} images")
    
    print(f"✅ Dataset organized: {total_images} total images")
    
    # Create dataset metadata
    metadata = {
        "dataset": "GDXray",
        "category": category,
        "total_images": total_images,
        "splits": {
            "train": len(list((output_path / 'train' / 'images').glob('*.png'))),
            "val": len(list((output_path / 'val' / 'images').glob('*.png'))),
            "test": len(list((output_path / 'test' / 'images').glob('*.png')))
        },
        "source": GDXRAY_URLS[category]["url"],
        "description": GDXRAY_URLS[category]["description"]
    }
    
    with open(output_path / 'dataset_info.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to {output_path / 'dataset_info.json'}")


def main():
    parser = argparse.ArgumentParser(description='Download and prepare GDXray dataset')
    parser.add_argument('--output', type=str, default='data/gdxray',
                        help='Output directory for dataset')
    parser.add_argument('--category', type=str, default='castings',
                        choices=['castings', 'welds'],
                        help='Dataset category to download')
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip download if already exists')
    
    args = parser.parse_args()
    
    # Setup paths
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = output_dir / 'temp'
    temp_dir.mkdir(exist_ok=True)
    
    category_info = GDXRAY_URLS[args.category]
    zip_path = temp_dir / f"{args.category}.zip"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           GDXray Dataset Downloader for RadiKal              ║
╚══════════════════════════════════════════════════════════════╝

📦 Category: {args.category}
📝 Description: {category_info['description']}
💾 Size: {category_info['size']}
📁 Output: {output_dir.absolute()}
""")
    
    # Download
    if not args.skip_download or not zip_path.exists():
        try:
            download_file(category_info['url'], zip_path, args.category)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print(f"\n💡 Manual download instructions:")
            print(f"   1. Visit: {category_info['url']}")
            print(f"   2. Download the ZIP file")
            print(f"   3. Place it at: {zip_path}")
            print(f"   4. Run this script again with --skip-download")
            return
    else:
        print(f"✅ Using existing download: {zip_path}")
    
    # Extract
    extract_zip(zip_path, temp_dir)
    
    # Organize
    organize_dataset(temp_dir, output_dir, args.category)
    
    # Cleanup
    print(f"🧹 Cleaning up temporary files...")
    # shutil.rmtree(temp_dir)  # Commented out for safety - user can delete manually
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                      ✅ SUCCESS!                              ║
╚══════════════════════════════════════════════════════════════╝

Dataset ready at: {output_dir.absolute()}

Next steps:
1. Update backend/configs/train_config.json with:
   "data_dir": "{output_dir.absolute()}"

2. Start training:
   python scripts/train.py --config configs/train_config.json --gpu 0

3. Monitor with MLflow:
   mlflow ui
   
Happy training! 🚀
""")


if __name__ == '__main__':
    main()
