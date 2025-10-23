"""Quick test of the new YOLOClassifier"""
import sys
sys.path.insert(0, '.')

from core.models.yolo_classifier import YOLOClassifier
import os
import cv2

# Initialize classifier
print("Initializing YOLOClassifier...")
classifier = YOLOClassifier()
print(f"✅ {classifier.get_model_info()['model_type']}")
print(f"   ND Threshold: {classifier.nd_confidence_threshold}")
print()

# Test on each class
test_cases = [
    ('Difetto1', 'LP - Lack of Penetration'),
    ('Difetto2', 'PO - Porosity'),
    ('Difetto4', 'CR - Cracks'),
    ('NoDifetto', 'ND - No Defect')
]

for folder, expected in test_cases:
    test_dir = f'../DATA/testing/{folder}'
    test_img_name = [f for f in os.listdir(test_dir) if f.endswith('.png')][0]
    test_img_path = os.path.join(test_dir, test_img_name)
    
    img = cv2.imread(test_img_path)
    result = classifier.classify(img)
    
    print(f"Test: {expected}")
    print(f"  Image: {test_img_name}")
    print(f"  Predicted: {result['predicted_class_name']} - {result['predicted_class_full_name']}")
    print(f"  Confidence: {result['confidence']:.4f}")
    print(f"  Is Defect: {result['is_defect']}")
    print(f"  Probabilities:")
    for cls, prob in result['all_probabilities'].items():
        print(f"    {cls}: {prob:.4f}")
    print()

print("✅ All tests complete!")
