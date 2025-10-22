"""
Convert COCO format to YOLO format for training
"""

import json
import os
from pathlib import Path
from tqdm import tqdm

def coco_to_yolo(data_dir="data"):
    """Convert COCO annotations to YOLO format"""
    
    data_path = Path(data_dir)
    
    for split in ['train', 'val', 'test']:
        print(f"\n📋 Converting {split} annotations...")
        
        # Paths
        images_dir = data_path / split / 'images'
        annotations_file = data_path / split / 'annotations' / 'annotations.json'
        labels_dir = data_path / split / 'labels'
        
        # Create labels directory
        labels_dir.mkdir(exist_ok=True)
        
        # Load COCO annotations
        with open(annotations_file, 'r') as f:
            coco_data = json.load(f)
        
        # Create image_id to filename mapping
        images = {img['id']: img for img in coco_data['images']}
        
        # Create category_id mapping (COCO categories might not start at 0)
        categories = {cat['id']: idx for idx, cat in enumerate(coco_data['categories'])}
        
        # Group annotations by image_id
        annotations_by_image = {}
        for ann in coco_data['annotations']:
            image_id = ann['image_id']
            if image_id not in annotations_by_image:
                annotations_by_image[image_id] = []
            annotations_by_image[image_id].append(ann)
        
        # Convert each image's annotations
        converted = 0
        for image_id, img_info in tqdm(images.items(), desc=f"Converting {split}"):
            img_width = img_info['width']
            img_height = img_info['height']
            img_filename = Path(img_info['file_name']).stem
            
            # Create label file
            label_file = labels_dir / f"{img_filename}.txt"
            
            # Get annotations for this image
            anns = annotations_by_image.get(image_id, [])
            
            with open(label_file, 'w') as f:
                for ann in anns:
                    # Convert COCO bbox [x, y, width, height] to YOLO [x_center, y_center, width, height] normalized
                    x, y, w, h = ann['bbox']
                    
                    # Calculate center and normalize
                    x_center = (x + w / 2) / img_width
                    y_center = (y + h / 2) / img_height
                    w_norm = w / img_width
                    h_norm = h / img_height
                    
                    # Get class ID (map to 0-indexed)
                    class_id = categories[ann['category_id']]
                    
                    # Write YOLO format line
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")
            
            converted += 1
        
        print(f"✅ Converted {converted} images in {split} set")
    
    print("\n🎉 Conversion complete!")
    print(f"\n📁 Dataset structure:")
    print(f"   data/")
    print(f"   ├── train/")
    print(f"   │   ├── images/")
    print(f"   │   └── labels/  ← Created")
    print(f"   ├── val/")
    print(f"   │   ├── images/")
    print(f"   │   └── labels/  ← Created")
    print(f"   └── test/")
    print(f"       ├── images/")
    print(f"       └── labels/  ← Created")

if __name__ == '__main__':
    print("=" * 60)
    print("🔄 COCO to YOLO Format Converter")
    print("=" * 60)
    
    coco_to_yolo()
