"""
Convert RIAWELC weld defects dataset to detection format for RadiKal XAI.

RIAWELC Dataset: Radiographic Images for Automatic Weld Defects Classification
- 24,407 images (224x224, 8-bit PNG)
- 4 classes of weld defects

Your DATA folder structure:
  DATA/
    training/
      Difetto1/  (Lack of Penetration - LP)
      Difetto2/  (Porosity - PO)
      Difetto4/  (Cracks - CR)
      NoDifetto/ (No Defect - ND)
    validation/...
    testing/...

Target structure for backend:
  backend/data/
    train/
      images/
      annotations/annotations.json (COCO format)
    val/...
    test/...

Usage:
    python scripts/convert_radikal_dataset.py --input DATA --output backend/data
"""

import os
import json
import shutil
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import argparse
from datetime import datetime


# Class mapping for RIAWELC dataset
CLASS_MAPPING = {
    'NoDifetto': 0,      # No Defect (ND)
    'Difetto1': 1,       # Lack of Penetration (LP)
    'Difetto2': 2,       # Porosity (PO)
    'Difetto4': 3,       # Cracks (CR)
}

CLASS_NAMES = {
    0: 'no_defect',
    1: 'lack_of_penetration',
    2: 'porosity',
    3: 'cracks',
}

CLASS_DESCRIPTIONS = {
    0: 'No Defect (ND) - Clean weld',
    1: 'Lack of Penetration (LP) - Incomplete fusion',
    2: 'Porosity (PO) - Gas pockets/voids',
    3: 'Cracks (CR) - Structural cracks',
}


def create_coco_annotations(images_info, split_name):
    """
    Create COCO format annotations for classification task.
    For images with defects, we create a bounding box covering most of the image.
    """
    annotations = []
    annotation_id = 1
    
    for img_info in images_info:
        if img_info['category_id'] > 0:  # Has defect
            # Create a bounding box covering 80% of image (center region)
            width, height = img_info['width'], img_info['height']
            bbox_width = int(width * 0.8)
            bbox_height = int(height * 0.8)
            x = int((width - bbox_width) / 2)
            y = int((height - bbox_height) / 2)
            
            annotations.append({
                'id': annotation_id,
                'image_id': img_info['id'],
                'category_id': img_info['category_id'],
                'bbox': [x, y, bbox_width, bbox_height],  # [x, y, width, height]
                'area': bbox_width * bbox_height,
                'iscrowd': 0,
                'segmentation': [[
                    x, y,
                    x + bbox_width, y,
                    x + bbox_width, y + bbox_height,
                    x, y + bbox_height
                ]]
            })
            annotation_id += 1
    
    return annotations


def convert_split(input_dir, output_dir, split_name):
    """Convert one split (training/validation/testing) to backend format."""
    
    print(f"\n{'='*60}")
    print(f"Converting {split_name.upper()} split...")
    print(f"{'='*60}")
    
    # Create output directories
    split_map = {'training': 'train', 'validation': 'val', 'testing': 'test'}
    output_split = split_map[split_name]
    
    images_dir = output_dir / output_split / 'images'
    annotations_dir = output_dir / output_split / 'annotations'
    images_dir.mkdir(parents=True, exist_ok=True)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all images
    images_info = []
    image_id = 1
    
    input_split_dir = input_dir / split_name
    
    for class_folder in sorted(input_split_dir.iterdir()):
        if not class_folder.is_dir():
            continue
        
        class_name = class_folder.name
        if class_name not in CLASS_MAPPING:
            print(f"⚠️  Skipping unknown class: {class_name}")
            continue
        
        category_id = CLASS_MAPPING[class_name]
        print(f"\n📂 Processing {class_name} (category {category_id})...")
        
        # Get all image files
        image_files = list(class_folder.glob('*.png')) + list(class_folder.glob('*.jpg'))
        
        for img_file in tqdm(image_files, desc=f"  {class_name}"):
            try:
                # Open image to get dimensions
                with Image.open(img_file) as img:
                    width, height = img.size
                
                # Create new filename
                new_filename = f"{output_split}_{image_id:06d}.png"
                
                # Copy image
                shutil.copy2(img_file, images_dir / new_filename)
                
                # Store image info
                images_info.append({
                    'id': image_id,
                    'file_name': new_filename,
                    'width': width,
                    'height': height,
                    'category_id': category_id,
                    'original_path': str(img_file.relative_to(input_dir))
                })
                
                image_id += 1
                
            except Exception as e:
                print(f"⚠️  Error processing {img_file.name}: {e}")
                continue
    
    # Create COCO annotations
    print(f"\n📝 Creating COCO annotations...")
    annotations = create_coco_annotations(images_info, output_split)
    
    # Create COCO format JSON
    coco_data = {
        'info': {
            'description': 'RadiKal XAI Defect Detection Dataset',
            'version': '1.0',
            'year': 2025,
            'contributor': 'RadiKal Project',
            'date_created': datetime.now().isoformat()
        },
        'licenses': [],
        'categories': [
            {'id': class_id, 'name': class_name, 'supercategory': 'defect'}
            for class_id, class_name in CLASS_NAMES.items()
        ],
        'images': [
            {
                'id': img['id'],
                'file_name': img['file_name'],
                'width': img['width'],
                'height': img['height']
            }
            for img in images_info
        ],
        'annotations': annotations
    }
    
    # Save annotations
    annotations_file = annotations_dir / 'annotations.json'
    with open(annotations_file, 'w') as f:
        json.dump(coco_data, f, indent=2)
    
    # Print statistics
    print(f"\n✅ {output_split.upper()} Split Complete:")
    print(f"   Total images: {len(images_info)}")
    print(f"   Total annotations: {len(annotations)}")
    print(f"   Images with defects: {sum(1 for img in images_info if img['category_id'] > 0)}")
    print(f"   Images without defects: {sum(1 for img in images_info if img['category_id'] == 0)}")
    print(f"   Saved to: {images_dir.parent}")
    
    # Class distribution
    print(f"\n   Class distribution:")
    for class_name, class_id in sorted(CLASS_MAPPING.items(), key=lambda x: x[1]):
        count = sum(1 for img in images_info if img['category_id'] == class_id)
        print(f"     {class_name:15s}: {count:5d} images")
    
    return len(images_info), len(annotations)


def main():
    parser = argparse.ArgumentParser(description='Convert RadiKal dataset to detection format')
    parser.add_argument('--input', type=str, default='DATA',
                        help='Input directory with training/validation/testing folders')
    parser.add_argument('--output', type=str, default='backend/data',
                        help='Output directory for converted dataset')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     RIAWELC Dataset Converter for RadiKal XAI                ║
╚══════════════════════════════════════════════════════════════╝

Dataset: RIAWELC - Radiographic Images for Weld Defects
Source:  Totino et al., ICMECE 2022

📂 Input:  {input_dir.absolute()}
📂 Output: {output_dir.absolute()}

Weld Defect Classes:
  0 - NoDifetto  (No Defect - ND)
  1 - Difetto1   (Lack of Penetration - LP)
  2 - Difetto2   (Porosity - PO)
  3 - Difetto4   (Cracks - CR)
""")
    
    # Convert each split
    total_images = 0
    total_annotations = 0
    
    for split in ['training', 'validation', 'testing']:
        split_dir = input_dir / split
        if split_dir.exists():
            num_images, num_annotations = convert_split(input_dir, output_dir, split)
            total_images += num_images
            total_annotations += num_annotations
        else:
            print(f"⚠️  Skipping {split} (directory not found)")
    
    # Create dataset metadata
    metadata = {
        'dataset_name': 'RIAWELC - Weld Defects Classification',
        'original_name': 'Radiographic Images for Automatic Weld Defects Classification',
        'version': '1.0',
        'source': 'Totino et al., ICMECE 2022',
        'citation': 'Benito Totino, Fanny Spagnolo, Stefania Perri, "RIAWELC: A Novel Dataset of Radiographic Images for Automatic Weld Defects Classification", ICMECE 2022',
        'total_images': total_images,
        'total_annotations': total_annotations,
        'num_classes': len(CLASS_MAPPING),
        'classes': CLASS_NAMES,
        'class_descriptions': CLASS_DESCRIPTIONS,
        'image_format': 'PNG 224x224 8-bit grayscale',
        'defect_types': {
            'lack_of_penetration': 'Incomplete weld penetration',
            'porosity': 'Gas pockets or voids in weld',
            'cracks': 'Structural cracks in weld material',
            'no_defect': 'Clean, defect-free welds'
        },
        'splits': {
            'train': 'Training set',
            'val': 'Validation set',
            'test': 'Test set'
        },
        'converted_for': 'RadiKal XAI Quality Control Module',
        'created': datetime.now().isoformat()
    }
    
    with open(output_dir / 'dataset_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✅ CONVERSION COMPLETE!                    ║
╚══════════════════════════════════════════════════════════════╝

📊 Summary:
   Total images:      {total_images:,}
   Total annotations: {total_annotations:,}
   Classes:           {len(CLASS_MAPPING)}

📁 Dataset structure:
   {output_dir}/
     ├── train/
     │   ├── images/        ({len(list((output_dir / 'train' / 'images').glob('*.png')))} images if exists)
     │   └── annotations/   (annotations.json)
     ├── val/
     │   ├── images/
     │   └── annotations/
     ├── test/
     │   ├── images/
     │   └── annotations/
     └── dataset_metadata.json

🚀 Next steps:
   1. Verify dataset structure:
      cd backend
      python -c "import json; print(json.dumps(json.load(open('data/dataset_metadata.json')), indent=2))"
   
   2. Start training:
      python scripts/train.py --config configs/train_config.json --gpu 0
   
   3. Monitor with MLflow:
      mlflow ui

Happy training! 🎉
""")


if __name__ == '__main__':
    main()
