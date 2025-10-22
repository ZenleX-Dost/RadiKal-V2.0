"""
Test script for YOLOv8 detector integration

This script tests the YOLOv8 detector to ensure it's working correctly
before starting the FastAPI server.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image
import torch

from core.models.yolo_detector import YOLODefectDetector

def test_yolo_detector():
    """Test the YOLOv8 detector with a sample image."""
    
    print("=" * 70)
    print("🧪 Testing YOLOv8 Defect Detector")
    print("=" * 70)
    
    # Initialize detector
    print("\n📥 Loading model...")
    try:
        detector = YOLODefectDetector(
            model_path="models/yolo/radikal_weld_detection/weights/best.pt",
            confidence_threshold=0.5
        )
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False
    
    # Print model info
    print("\n📊 Model Information:")
    model_info = detector.get_model_info()
    for key, value in model_info.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"     {k}: {v}")
        else:
            print(f"   {key}: {value}")
    
    # Find a test image
    print("\n🔍 Looking for test image...")
    test_image_paths = [
        "data/test/images",
        "data/val/images",
        "data/train/images"
    ]
    
    test_image = None
    for path in test_image_paths:
        img_dir = Path(path)
        if img_dir.exists():
            images = list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg"))
            if images:
                test_image = images[0]
                break
    
    if test_image is None:
        print("⚠️  No test images found. Creating synthetic test image...")
        # Create a synthetic test image
        test_img_array = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    else:
        print(f"✅ Found test image: {test_image}")
        test_img = Image.open(test_image).convert("RGB")
        test_img_array = np.array(test_img)
    
    # Run detection
    print(f"\n🔬 Running detection on image shape: {test_img_array.shape}")
    try:
        results = detector.detect(test_img_array)
        
        print(f"\n✅ Detection completed!")
        print(f"   Number of detections: {results['num_detections']}")
        
        if results['num_detections'] > 0:
            print(f"\n📋 Detected defects:")
            for i in range(results['num_detections']):
                box = results['boxes'][i]
                score = results['scores'][i]
                class_name = results['class_names'][i]
                print(f"   {i+1}. {class_name}")
                print(f"      Confidence: {score:.2%}")
                print(f"      Box: [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}]")
        else:
            print(f"\n   No defects detected (confidence threshold: {detector.confidence_threshold})")
        
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test API-compatible predict method
    print(f"\n🔬 Testing API-compatible predict() method...")
    try:
        # Convert to tensor format
        if test_img_array.max() > 1.0:
            test_img_array = test_img_array.astype(np.float32) / 255.0
        
        image_tensor = torch.from_numpy(test_img_array).permute(2, 0, 1).unsqueeze(0)
        
        detections = detector.predict(image_tensor)
        
        print(f"✅ Predict method works!")
        print(f"   Number of detections: {len(detections)}")
        
        if len(detections) > 0:
            print(f"\n📋 Detection format (API-compatible):")
            for i, det in enumerate(detections[:3]):  # Show first 3
                print(f"   {i+1}. {det['label']}")
                print(f"      Score: {det['score']:.2%}")
                print(f"      Severity: {det['severity']}")
                print(f"      Box: {det['box']}")
                if 'mask' in det:
                    print(f"      Mask shape: {det['mask'].shape}")
        
    except Exception as e:
        print(f"❌ Predict method failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("🎉 All tests passed! YOLOv8 detector is ready!")
    print("=" * 70)
    print("\n💡 Next steps:")
    print("   1. Start the FastAPI server: python main.py")
    print("   2. Open API docs: http://localhost:8000/api/docs")
    print("   3. Test the /detect endpoint with a real image")
    
    return True


if __name__ == "__main__":
    success = test_yolo_detector()
    sys.exit(0 if success else 1)
