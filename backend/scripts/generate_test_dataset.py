"""Generate synthetic test dataset for quick prototyping.

This script creates synthetic defect images with annotations for testing
the training pipeline without requiring real data.
"""

import os
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import random


def generate_synthetic_image(
    size: tuple = (512, 512),
    num_defects: int = None
) -> tuple:
    """Generate a synthetic radiographic-style image with defects.
    
    Args:
        size: Image size (width, height).
        num_defects: Number of defects to generate. If None, random 1-3.
        
    Returns:
        Tuple of (image, boxes, labels).
    """
    if num_defects is None:
        num_defects = random.randint(1, 3)
    
    img = Image.new('L', size, color=180)
    draw = ImageDraw.Draw(img)
    
    for _ in range(50):
        x = random.randint(0, size[0])
        y = random.randint(0, size[1])
        radius = random.randint(1, 3)
        shade = random.randint(150, 210)
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=shade
        )
    
    boxes = []
    labels = []
    
    for _ in range(num_defects):
        defect_type = random.choice(['crack', 'void', 'inclusion'])
        
        x_center = random.randint(100, size[0] - 100)
        y_center = random.randint(100, size[1] - 100)
        width = random.randint(30, 80)
        height = random.randint(30, 80)
        
        x1 = max(0, x_center - width // 2)
        y1 = max(0, y_center - height // 2)
        x2 = min(size[0], x_center + width // 2)
        y2 = min(size[1], y_center + height // 2)
        
        if defect_type == 'crack':
            for i in range(10):
                px = x_center + random.randint(-width // 2, width // 2)
                py = y_center + random.randint(-height // 2, height // 2)
                draw.line(
                    [px, py, px + random.randint(-5, 5), py + random.randint(-5, 5)],
                    fill=80,
                    width=2
                )
        elif defect_type == 'void':
            draw.ellipse(
                [x1, y1, x2, y2],
                fill=50
            )
        else:
            draw.rectangle(
                [x1, y1, x2, y2],
                fill=220
            )
        
        boxes.append([float(x1), float(y1), float(x2), float(y2)])
        labels.append(1)
    
    img_rgb = img.convert('RGB')
    
    return img_rgb, boxes, labels


def generate_dataset(
    output_dir: str,
    num_train: int = 100,
    num_val: int = 20,
    num_test: int = 20,
    image_size: tuple = (512, 512)
):
    """Generate synthetic dataset with train/val/test splits.
    
    Args:
        output_dir: Output directory for dataset.
        num_train: Number of training samples.
        num_val: Number of validation samples.
        num_test: Number of test samples.
        image_size: Image size (width, height).
    """
    output_path = Path(output_dir)
    
    splits = {
        'train': num_train,
        'val': num_val,
        'test': num_test
    }
    
    for split_name, num_samples in splits.items():
        print(f"Generating {split_name} split with {num_samples} samples...")
        
        split_dir = output_path / split_name
        images_dir = split_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        
        annotations = []
        
        for i in range(num_samples):
            image_filename = f"{split_name}_{i:04d}.jpg"
            image_path = images_dir / image_filename
            
            img, boxes, labels = generate_synthetic_image(size=image_size)
            
            img.save(image_path, quality=95)
            
            annotations.append({
                'image_file': image_filename,
                'boxes': boxes,
                'labels': labels
            })
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{num_samples} images")
        
        annotations_path = split_dir / 'annotations.json'
        with open(annotations_path, 'w') as f:
            json.dump(annotations, f, indent=2)
        
        print(f"  Saved annotations to {annotations_path}")
        print(f"  {split_name} split complete!")
        print()
    
    print("Dataset generation complete!")
    print(f"Total images: {sum(splits.values())}")
    print(f"Location: {output_path}")
    print()
    print("Dataset structure:")
    print(f"{output_dir}/")
    print("├── train/")
    print("│   ├── images/ ({} images)".format(num_train))
    print("│   └── annotations.json")
    print("├── val/")
    print("│   ├── images/ ({} images)".format(num_val))
    print("│   └── annotations.json")
    print("└── test/")
    print("    ├── images/ ({} images)".format(num_test))
    print("    └── annotations.json")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic defect dataset for testing"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for dataset (default: data)'
    )
    parser.add_argument(
        '--num-train',
        type=int,
        default=100,
        help='Number of training samples (default: 100)'
    )
    parser.add_argument(
        '--num-val',
        type=int,
        default=20,
        help='Number of validation samples (default: 20)'
    )
    parser.add_argument(
        '--num-test',
        type=int,
        default=20,
        help='Number of test samples (default: 20)'
    )
    parser.add_argument(
        '--image-size',
        type=int,
        nargs=2,
        default=[512, 512],
        help='Image size as width height (default: 512 512)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Synthetic Defect Dataset Generator")
    print("=" * 60)
    print()
    print(f"Configuration:")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Training samples: {args.num_train}")
    print(f"  Validation samples: {args.num_val}")
    print(f"  Test samples: {args.num_test}")
    print(f"  Image size: {args.image_size[0]}x{args.image_size[1]}")
    print()
    
    generate_dataset(
        output_dir=args.output_dir,
        num_train=args.num_train,
        num_val=args.num_val,
        num_test=args.num_test,
        image_size=tuple(args.image_size)
    )
    
    print("=" * 60)
    print("Ready to train!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review the generated dataset")
    print("  2. Run: python scripts/train.py --config configs/train_config.json --gpu 0")
    print("  3. Monitor with MLflow: mlflow ui")


if __name__ == "__main__":
    main()
