"""
Quick test of the classification model to see why it's predicting everything as ND
"""

from pathlib import Path
from ultralytics import YOLO
import torch

# Test configuration
BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "backend/models/yolo/classification_defect_focused/weights/best.pt"
TEST_IMAGES = [
    BASE_DIR / "DATA/test/Difetto1/bam5_Img2_A80_S5_[3][10].png",  # LP
    BASE_DIR / "DATA/test/Difetto2/bam5_Img2_A80_S1_[11][4].png",  # PO
    BASE_DIR / "DATA/test/Difetto4/bam5_Img1_A80_S2_[4][21].png",  # CR
    BASE_DIR / "DATA/test/NoDifetto/RRT-09R_Img1_A80_S9_[2][23].png",  # ND
]

CLASS_NAMES = {0: "LP", 1: "PO", 2: "CR", 3: "ND"}

print("="*60)
print("Testing YOLOv8 Classification Model")
print("="*60)

# Load model
print(f"\nLoading model from: {MODEL_PATH}")
print(f"Model exists: {MODEL_PATH.exists()}")
print(f"CUDA available: {torch.cuda.is_available()}")

model = YOLO(str(MODEL_PATH))
print(f"Model loaded: {model.task}")
print(f"Model names: {model.names}")

# Test each image
print("\n" + "="*60)
print("Testing predictions:")
print("="*60)

for i, img_path in enumerate(TEST_IMAGES):
    print(f"\n{i+1}. Testing: {img_path.parent.name}/{img_path.name}")
    
    if not img_path.exists():
        print(f"   ❌ Image not found!")
        continue
    
    # Run prediction
    results = model(str(img_path), verbose=False)
    result = results[0]
    
    # Get probabilities
    probs = result.probs.data.cpu().numpy()
    top_class = result.probs.top1
    confidence = result.probs.top1conf.item()
    
    print(f"   Predicted: {CLASS_NAMES[top_class]} ({confidence*100:.1f}%)")
    print(f"   Probabilities:")
    for class_idx, prob in enumerate(probs):
        class_name = CLASS_NAMES[class_idx]
        print(f"      {class_name}: {prob*100:.2f}%")
    
    # Check expected vs actual
    expected_class = img_path.parent.name
    if expected_class == "Difetto1":
        expected = "LP"
    elif expected_class == "Difetto2":
        expected = "PO"
    elif expected_class == "Difetto4":
        expected = "CR"
    elif expected_class == "NoDifetto":
        expected = "ND"
    else:
        expected = "Unknown"
    
    actual = CLASS_NAMES[top_class]
    status = "✅ CORRECT" if actual == expected else "❌ WRONG"
    print(f"   Expected: {expected}, Got: {actual} {status}")

print("\n" + "="*60)
print("Test Complete")
print("="*60)
