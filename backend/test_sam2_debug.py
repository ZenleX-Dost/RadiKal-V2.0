"""
Debug script for SAM2 segmentation issues.
Run this from the backend directory: python test_sam2_debug.py [image_path]

This script helps diagnose why SAM2 might return "no defects detected".
Common causes:
1. conf_threshold too high (fixed: now 0.3)
2. Low contrast images (fixed: CLAHE enhancement added)
3. pred_iou_thresh too high (fixed: now 0.5)
4. Image format issues
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from PIL import Image
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sam2_with_image(image_path: str):
    """Test SAM2 segmentation with a specific image."""
    
    print("\n" + "="*70)
    print(f"Testing SAM2 with: {image_path}")
    print("="*70)
    
    # Load image
    image = Image.open(image_path).convert('RGB')
    image_np = np.array(image)
    print(f"Image size: {image_np.shape}")
    print(f"Image dtype: {image_np.dtype}")
    print(f"Image range: [{image_np.min()}, {image_np.max()}]")
    
    # Import and initialize
    from core.models.sam2_segmenter import SAM2Segmenter
    
    print("\n[1] Initializing SAM2...")
    segmenter = SAM2Segmenter(
        model_size="base",
        device="cuda",
        conf_threshold=0.3,  # Lower threshold for debugging
        mask_threshold=0.5
    )
    
    print("\n[2] Testing AUTO segmentation...")
    segmenter.set_image(image_np)
    
    # Auto segment with more lenient parameters
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    
    mask_generator = SAM2AutomaticMaskGenerator(
        model=segmenter.sam2_model,
        points_per_side=32,  # Default, but reasonable
        pred_iou_thresh=0.5,  # Lower threshold
        stability_score_thresh=0.7,  # Lower threshold
        crop_n_layers=1,
        min_mask_region_area=50  # Lower minimum area
    )
    
    masks = mask_generator.generate(segmenter.current_image)
    print(f"   Auto-segmentation found {len(masks)} raw masks")
    
    if masks:
        for i, m in enumerate(masks[:5]):  # Show first 5
            print(f"   Mask {i}: area={m['area']}, iou={m['predicted_iou']:.3f}, stability={m['stability_score']:.3f}")
    
    # Now test with segment_defect
    print("\n[3] Testing segment_defect (auto_segment=True)...")
    result = segmenter.segment_defect(
        image=image_np,
        auto_segment=True
    )
    print(f"   num_segments: {result['num_segments']}")
    print(f"   scores: {result['scores']}")
    if result['primary_mask'] is not None:
        mask = np.array(result['primary_mask'])
        print(f"   primary_mask area: {np.sum(mask)}")
        print(f"   bbox: {result['bbox']}")
    
    # Test with center point
    print("\n[4] Testing with CENTER POINT prompt...")
    h, w = image_np.shape[:2]
    center_point = np.array([[w // 2, h // 2]], dtype=np.float32)
    print(f"   Center point: {center_point}")
    
    result_center = segmenter.segment_defect(
        image=image_np,
        prompt_points=center_point,
        auto_segment=False
    )
    print(f"   num_segments: {result_center['num_segments']}")
    print(f"   scores: {result_center['scores']}")
    
    # Now test the full hybrid analyzer
    print("\n[5] Testing HYBRID ANALYZER...")
    from core.models.hybrid_defect_analyzer import HybridDefectAnalyzer
    
    analyzer = HybridDefectAnalyzer(
        classifier_path="models/yolo/classification_defect_focused/weights/best.pt",
        segmenter_size="base",
        device="cuda",
        nd_threshold=0.7,
        enable_sam2=True
    )
    
    result_hybrid = analyzer.analyze(
        image=image_np,
        mode="hybrid",
        return_visualization=False,
        segmentation_guidance="auto"
    )
    
    print("\n   Classification result:")
    if result_hybrid['classification']:
        cls = result_hybrid['classification']
        print(f"      Class: {cls['predicted_class_name']} ({cls['predicted_class_full_name']})")
        print(f"      Confidence: {cls['confidence']:.3f}")
        print(f"      Is defect: {cls['is_defect']}")
        print(f"      All probabilities: {cls['all_probabilities']}")
    
    print("\n   Segmentation result:")
    if result_hybrid['segmentation']:
        seg = result_hybrid['segmentation']
        print(f"      has_segmentation: {seg.get('has_segmentation', False)}")
        print(f"      num_segments: {seg.get('num_segments', 0)}")
        if seg.get('scores'):
            print(f"      scores: {seg['scores']}")
        if seg.get('bbox'):
            print(f"      bbox: {seg['bbox']}")
    
    return result_hybrid


def main():
    print("\n" + "="*70)
    print("SAM2 DEBUG TEST")
    print("="*70)
    
    # Test images - try different defect types
    test_images = [
        # Defect images
        "../DATA/test/Difetto1/bam5_Img2_A80_S5_[3][10].png",  # Lack of Penetration
        "../DATA/test/Difetto2/bam5_Img2_A80_S1_[11][4].png",  # Porosity
        "../DATA/test/Difetto4/bam5_Img1_A80_S2_[4][21].png",  # Cracks
        # No Defect
        "../DATA/test/NoDifetto/RRT-09R_Img1_A80_S9_[2][23].png",
    ]
    
    # Check which images exist
    available_images = []
    for path in test_images:
        if Path(path).exists():
            available_images.append(path)
    
    if not available_images:
        # Try to find any test images
        print("Looking for test images...")
        test_dirs = [
            Path("../DATA/test"),
            Path("DATA/test"),
            Path("../DATA/testing"),
        ]
        for test_dir in test_dirs:
            if test_dir.exists():
                for img_path in test_dir.rglob("*.png"):
                    available_images.append(str(img_path))
                    if len(available_images) >= 4:
                        break
                if available_images:
                    break
    
    if not available_images:
        print("❌ No test images found! Please provide an image path.")
        print("Usage: python test_sam2_debug.py [image_path]")
        return
    
    print(f"\nFound {len(available_images)} test images")
    
    # Test first image or user-provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = available_images[0]
    
    result = test_sam2_with_image(image_path)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if result['segmentation'] and result['segmentation'].get('has_segmentation'):
        print("✅ SAM2 segmentation is WORKING!")
        print(f"   Found {result['segmentation']['num_segments']} segments")
    else:
        print("⚠️ SAM2 returned NO SEGMENTS")
        print("\nPossible causes:")
        print("  1. conf_threshold is too high (currently 0.7)")
        print("  2. Auto-segmentation not finding defect-like regions")
        print("  3. Image has low contrast/unclear defects")
        print("  4. Image size/format issues")
        
        # Check if classification thinks there's a defect
        if result['classification'] and result['classification']['is_defect']:
            print("\n   Note: Classification detected a defect but segmentation found nothing!")
            print("   This suggests the segmentation threshold may be too high.")


if __name__ == "__main__":
    main()
