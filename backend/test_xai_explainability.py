"""
Quick Test Script for XAI Explainability System

Tests the complete pipeline:
1. Load YOLOv8 Classification Model
2. Generate Grad-CAM heatmaps
3. Detect defect regions
4. Create visualization panels
5. Generate natural language explanations
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.models.yolo_classifier import YOLOClassifier
from core.xai.classification_explainer import ClassificationExplainer
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_explainability():
    """
    Test XAI explainability on sample images.
    """
    print("\n" + "="*70)
    print(" "*15 + "🎯 XAI EXPLAINABILITY TEST")
    print("="*70 + "\n")
    
    # Step 1: Load classifier
    print("[1/5] Loading YOLOv8 Classification Model...")
    try:
        classifier = YOLOClassifier(
            model_path="models/yolo/classification_defect_focused/weights/best.pt",
            nd_confidence_threshold=0.7
        )
        print(f"✅ Model loaded successfully!")
        print(f"    Device: {classifier.device}")
        print(f"    Task: {classifier.model.task}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Step 2: Create explainer
    print("\n[2/5] Initializing Classification Explainer with Grad-CAM...")
    try:
        explainer = ClassificationExplainer(classifier)
        print(f"✅ Explainer initialized!")
    except Exception as e:
        print(f"❌ Failed to create explainer: {e}")
        return
    
    # Step 3: Test on sample images
    print("\n[3/5] Testing on Sample Images...")
    test_images = {
        'Lack of Penetration': "../DATA/test/Difetto1/bam5_Img2_A80_S5_[3][10].png",
        'Porosity': "../DATA/test/Difetto2/bam5_Img2_A80_S1_[11][4].png",
        'Cracks': "../DATA/test/Difetto4/bam5_Img1_A80_S2_[4][21].png",
        'No Defect': "../DATA/test/NoDifetto/RRT-09R_Img1_A80_S9_[2][23].png",
    }
    
    results = []
    for defect_type, img_path in test_images.items():
        img_path = Path(img_path)
        if not img_path.exists():
            print(f"⚠️  Skipping {defect_type} - Image not found: {img_path}")
            continue
        
        print(f"\n  Testing: {defect_type} ({img_path.name})")
        try:
            # Generate explanation
            explanation = explainer.explain_prediction(
                str(img_path),
                include_overlay=True,
                include_regions=True,
                include_description=True
            )
            
            # Display results
            pred = explanation['prediction']
            print(f"    ✅ Prediction: {pred['class_full_name']} ({pred['class_code']})")
            print(f"       Confidence: {pred['confidence']*100:.1f}%")
            print(f"       Severity: {pred['severity']}")
            print(f"       Location: {explanation['location_description']}")
            print(f"       Regions: {len(explanation['regions'])} detected")
            
            results.append({
                'ground_truth': defect_type,
                'prediction': pred['class_full_name'],
                'confidence': pred['confidence'],
                'image': img_path.name
            })
        
        except Exception as e:
            print(f"    ❌ Failed: {e}")
    
    # Step 4: Generate visualization panels
    print("\n[4/5] Generating Visualization Panels...")
    for defect_type, img_path in test_images.items():
        img_path = Path(img_path)
        if not img_path.exists():
            continue
        
        output_path = f"test_xai_panel_{img_path.stem}.png"
        try:
            explainer.create_visualization_panel(str(img_path), output_path)
            print(f"  ✅ Saved: {output_path}")
        except Exception as e:
            print(f"  ❌ Failed to create panel for {defect_type}: {e}")
    
    # Step 5: Summary
    print("\n[5/5] Test Summary")
    print("\n" + "-"*70)
    print(f"{'Image':<20} {'Ground Truth':<20} {'Prediction':<20} {'Confidence':<15}")
    print("-"*70)
    for result in results:
        correct = "✅" if result['ground_truth'] == result['prediction'] else "❌"
        print(f"{result['image']:<20} {result['ground_truth']:<20} {result['prediction']:<20} {result['confidence']*100:>5.1f}% {correct}")
    print("-"*70)
    
    if len(results) > 0:
        accuracy = sum(1 for r in results if r['ground_truth'] == r['prediction']) / len(results) * 100
        print(f"\nAccuracy: {accuracy:.1f}% ({sum(1 for r in results if r['ground_truth'] == r['prediction'])}/{len(results)} correct)")
    else:
        print(f"\n⚠️ No test images found - check DATA paths")
    
    print("\n" + "="*70)
    print("✅ XAI EXPLAINABILITY TEST COMPLETE!")
    print("="*70 + "\n")
    
    print("📊 Next Steps:")
    print("1. Review generated visualization panels (test_xai_panel_*.png)")
    print("2. Check heatmaps show defect locations correctly")
    print("3. Verify natural language descriptions are clear")
    print("4. Test API endpoint: POST /api/xai-qc/explain")
    print("5. Integrate with frontend for operator display")


def test_single_image(image_path: str):
    """
    Test explainability on a single image with detailed output.
    """
    print("\n" + "="*70)
    print(" "*15 + "🔍 SINGLE IMAGE DETAILED TEST")
    print("="*70 + "\n")
    
    # Load classifier
    print("Loading model...")
    classifier = YOLOClassifier()
    explainer = ClassificationExplainer(classifier)
    
    # Test image
    img_path = Path(image_path)
    if not img_path.exists():
        print(f"❌ Image not found: {img_path}")
        return
    
    print(f"\nProcessing: {img_path.name}")
    print("-"*70)
    
    # Generate explanation
    explanation = explainer.explain_prediction(
        str(img_path),
        include_overlay=True,
        include_regions=True,
        include_description=True
    )
    
    # Display full results
    pred = explanation['prediction']
    print("\n📊 PREDICTION:")
    print(f"  Class: {pred['class_full_name']} ({pred['class_code']})")
    print(f"  Confidence: {pred['confidence']*100:.2f}%")
    print(f"  Is Defect: {pred['is_defect']}")
    print(f"  Severity: {pred['severity']}")
    
    print("\n📈 PROBABILITIES:")
    for prob in explanation['probabilities']:
        bar_length = int(prob['probability'] * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"  {prob['class_code']}: {bar} {prob['probability']*100:>5.1f}%")
    
    print(f"\n📍 LOCATION:")
    print(f"  {explanation['location_description']}")
    
    print(f"\n🔍 DETECTED REGIONS: {len(explanation['regions'])}")
    for i, region in enumerate(explanation['regions'][:3]):  # Top 3
        x, y, w, h = region['bbox']
        print(f"  Region {i+1}:")
        print(f"    BBox: x={x}, y={y}, w={w}, h={h}")
        print(f"    Area: {region['area']} pixels")
        print(f"    Score: {region['score']:.3f}")
        print(f"    Center: ({region['center'][0]}, {region['center'][1]})")
    
    print(f"\n💬 DESCRIPTION:")
    print(f"  {explanation['description']}")
    
    print(f"\n⚡ RECOMMENDATION:")
    print(f"  {explanation['recommendation']}")
    
    # Save visualization
    output_path = f"detailed_test_{img_path.stem}.png"
    explainer.create_visualization_panel(str(img_path), output_path)
    print(f"\n💾 Visualization saved to: {output_path}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test XAI Explainability System")
    parser.add_argument(
        "--image",
        type=str,
        help="Test single image (provide path)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full test suite on all sample images"
    )
    
    args = parser.parse_args()
    
    if args.image:
        test_single_image(args.image)
    else:
        # Default: run full test
        test_explainability()
