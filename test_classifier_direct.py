"""
Direct test of YOLOClassifier class to diagnose the issue
"""

import sys
sys.path.insert(0, 'backend')

from pathlib import Path
from core.models.yolo_classifier import YOLOClassifier
import numpy as np
from PIL import Image

print("="*60)
print("Testing YOLOClassifier Class Directly")
print("="*60)

# Initialize classifier
print("\n1. Initializing YOLOClassifier...")
try:
    classifier = YOLOClassifier(
        model_path="backend/models/yolo/classification_defect_focused/weights/best.pt",
        nd_confidence_threshold=0.7
    )
    print(f"   ✅ Classifier loaded")
    print(f"   Device: {classifier.device}")
    print(f"   ND Threshold: {classifier.nd_confidence_threshold}")
    print(f"   Class Names: {classifier.CLASS_NAMES}")
except Exception as e:
    print(f"   ❌ Failed to load classifier: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test images
TEST_IMAGES = [
    ("DATA/test/Difetto1/bam5_Img2_A80_S5_[3][10].png", "LP"),
    ("DATA/test/Difetto2/bam5_Img2_A80_S1_[11][4].png", "PO"),
    ("DATA/test/Difetto4/bam5_Img1_A80_S2_[4][21].png", "CR"),
    ("DATA/test/NoDifetto/RRT-09R_Img1_A80_S9_[2][23].png", "ND"),
]

print("\n2. Testing predictions with apply_nd_threshold=True:")
print("="*60)

for img_path, expected in TEST_IMAGES:
    print(f"\nTesting: {Path(img_path).name}")
    print(f"Expected: {expected}")
    
    if not Path(img_path).exists():
        print(f"   ❌ Image not found!")
        continue
    
    # Load image
    image = np.array(Image.open(img_path))
    
    # Classify with threshold
    result = classifier.classify(image, apply_nd_threshold=True)
    
    print(f"   Predicted Class: {result['predicted_class']}")
    print(f"   Predicted Name: {result['predicted_class_name']}")
    print(f"   Full Name: {result['predicted_class_full_name']}")
    print(f"   Confidence: {result['confidence']*100:.1f}%")
    print(f"   Is Defect: {result['is_defect']}")
    print(f"   ND Threshold Applied: {result['nd_threshold_applied']}")
    
    print(f"   All Probabilities:")
    for class_name, prob in result['all_probabilities'].items():
        marker = "←" if class_name == result['predicted_class_name'] else " "
        print(f"      {class_name}: {prob*100:.2f}% {marker}")
    
    # Check if correct
    status = "✅ CORRECT" if result['predicted_class_name'] == expected else "❌ WRONG"
    print(f"   {status}")

print("\n" + "="*60)
print("3. Testing predictions with apply_nd_threshold=False:")
print("="*60)

for img_path, expected in TEST_IMAGES:
    print(f"\nTesting: {Path(img_path).name}")
    
    if not Path(img_path).exists():
        continue
    
    image = np.array(Image.open(img_path))
    result = classifier.classify(image, apply_nd_threshold=False)
    
    print(f"   Predicted: {result['predicted_class_name']} ({result['confidence']*100:.1f}%)")
    status = "✅ CORRECT" if result['predicted_class_name'] == expected else "❌ WRONG"
    print(f"   {status}")

print("\n" + "="*60)
print("Test Complete")
print("="*60)
