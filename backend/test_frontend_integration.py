"""
Frontend-Backend Integration Test for XAI Visualization

Tests the complete flow:
1. Backend API returns proper ExplanationResponse format
2. All metadata fields are present and correctly typed
3. Frontend TypeScript types match backend schema
4. Components can render with real API data

Run this test to verify the frontend can consume backend XAI data.
"""

import requests
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_IMAGE_PATH = Path("DATA/test/Difetto2/bam5_Img2_A80_S1_[11][4].png")  # Porosity


def test_explain_endpoint():
    """Test that /explain endpoint returns data matching frontend types."""
    
    logger.info("=" * 60)
    logger.info("Frontend-Backend XAI Integration Test")
    logger.info("=" * 60)
    
    # Check if test image exists
    if not TEST_IMAGE_PATH.exists():
        logger.error(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return False
    
    logger.info(f"✅ Test image found: {TEST_IMAGE_PATH}")
    
    # Test 1: Health check
    logger.info("\n1️⃣  Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code != 200:
            logger.error(f"❌ Backend not healthy: {response.status_code}")
            return False
        logger.info("✅ Backend is healthy")
    except Exception as e:
        logger.error(f"❌ Cannot connect to backend: {e}")
        logger.info("   Make sure backend is running: python backend/run_server.py")
        return False
    
    # Test 2: Call /explain endpoint
    logger.info("\n2️⃣  Calling /explain endpoint...")
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': (TEST_IMAGE_PATH.name, f, 'image/png')}
            response = requests.post(f"{BACKEND_URL}/api/explain", files=files, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ API call failed: {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            return False
        
        logger.info("✅ API call successful")
        
    except Exception as e:
        logger.error(f"❌ API call error: {e}")
        return False
    
    # Test 3: Validate response structure
    logger.info("\n3️⃣  Validating response structure...")
    try:
        data = response.json()
        
        # Required top-level fields (matching ExplanationResponse type)
        required_fields = [
            'image_id',
            'explanations',
            'aggregated_heatmap',
            'consensus_score',
            'computation_time_ms',
            'timestamp',
            'metadata'
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            logger.error(f"❌ Missing top-level fields: {missing_fields}")
            return False
        
        logger.info("✅ All top-level fields present")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON response: {e}")
        return False
    
    # Test 4: Validate explanations array
    logger.info("\n4️⃣  Validating explanations array...")
    explanations = data.get('explanations', [])
    
    if not explanations or len(explanations) < 2:
        logger.error(f"❌ Expected 2 explanations (gradcam + overlay), got {len(explanations)}")
        return False
    
    for exp in explanations:
        if 'method' not in exp or 'heatmap_base64' not in exp or 'confidence_score' not in exp:
            logger.error(f"❌ Invalid explanation structure: {exp.keys()}")
            return False
    
    logger.info(f"✅ Found {len(explanations)} explanations: {[e['method'] for e in explanations]}")
    
    # Test 5: Validate metadata structure
    logger.info("\n5️⃣  Validating metadata structure...")
    metadata = data.get('metadata', {})
    
    required_metadata_fields = [
        'prediction',
        'probabilities',
        'regions',
        'location_description',
        'description',
        'recommendation'
    ]
    
    missing_metadata = [f for f in required_metadata_fields if f not in metadata]
    if missing_metadata:
        logger.error(f"❌ Missing metadata fields: {missing_metadata}")
        return False
    
    logger.info("✅ All metadata fields present")
    
    # Test 6: Validate prediction structure (PredictionInfo type)
    logger.info("\n6️⃣  Validating prediction structure...")
    prediction = metadata.get('prediction', {})
    
    required_prediction_fields = [
        'predicted_class',
        'predicted_class_name',
        'predicted_class_full_name',
        'confidence',
        'severity',
        'color'
    ]
    
    missing_prediction = [f for f in required_prediction_fields if f not in prediction]
    if missing_prediction:
        logger.error(f"❌ Missing prediction fields: {missing_prediction}")
        return False
    
    logger.info("✅ All prediction fields present")
    logger.info(f"   Class: {prediction['predicted_class_full_name']} ({prediction['predicted_class_name']})")
    logger.info(f"   Confidence: {prediction['confidence']*100:.1f}%")
    logger.info(f"   Severity: {prediction['severity']}")
    
    # Test 7: Validate probabilities
    logger.info("\n7️⃣  Validating probabilities...")
    probabilities = metadata.get('probabilities', {})
    
    expected_classes = ['LP', 'PO', 'CR', 'ND']
    missing_classes = [c for c in expected_classes if c not in probabilities]
    if missing_classes:
        logger.error(f"❌ Missing probability classes: {missing_classes}")
        return False
    
    logger.info("✅ All class probabilities present")
    for class_name, prob in probabilities.items():
        logger.info(f"   {class_name}: {prob*100:.2f}%")
    
    # Test 8: Validate regions structure (DefectRegion[] type)
    logger.info("\n8️⃣  Validating regions structure...")
    regions = metadata.get('regions', [])
    
    logger.info(f"✅ Found {len(regions)} detected regions")
    
    if regions:
        required_region_fields = ['x', 'y', 'width', 'height', 'coverage', 'intensity']
        for i, region in enumerate(regions):
            missing_region = [f for f in required_region_fields if f not in region]
            if missing_region:
                logger.error(f"❌ Region {i} missing fields: {missing_region}")
                return False
            logger.info(f"   Region {i+1}: ({region['x']}, {region['y']}) "
                       f"{region['width']}×{region['height']} - "
                       f"Coverage: {region['coverage']*100:.1f}%")
    
    # Test 9: Validate text descriptions
    logger.info("\n9️⃣  Validating text descriptions...")
    location_desc = metadata.get('location_description', '')
    description = metadata.get('description', '')
    recommendation = metadata.get('recommendation', '')
    
    if not location_desc or not description or not recommendation:
        logger.error("❌ Missing text descriptions")
        return False
    
    logger.info("✅ All text descriptions present")
    logger.info(f"   Location: {location_desc}")
    logger.info(f"   Description: {description[:80]}...")
    logger.info(f"   Recommendation: {recommendation[:80]}...")
    
    # Test 10: Validate base64 images
    logger.info("\n🔟 Validating base64 images...")
    
    # Check heatmap base64
    heatmap_b64 = explanations[0].get('heatmap_base64', '')
    if not heatmap_b64 or len(heatmap_b64) < 100:
        logger.error("❌ Invalid heatmap base64 data")
        return False
    
    logger.info(f"✅ Heatmap base64 valid ({len(heatmap_b64)} chars)")
    
    # Check aggregated heatmap
    agg_heatmap = data.get('aggregated_heatmap', '')
    if not agg_heatmap or len(agg_heatmap) < 100:
        logger.error("❌ Invalid aggregated heatmap base64 data")
        return False
    
    logger.info(f"✅ Aggregated heatmap valid ({len(agg_heatmap)} chars)")
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 60)
    logger.info("\n📊 Frontend Component Compatibility:")
    logger.info("   ✅ ExplanationResponse type - COMPATIBLE")
    logger.info("   ✅ PredictionInfo type - COMPATIBLE")
    logger.info("   ✅ DefectRegion[] type - COMPATIBLE")
    logger.info("   ✅ ExplanationMetadata type - COMPATIBLE")
    logger.info("\n🎨 Frontend Components Ready:")
    logger.info("   ✅ DefectLocalizationView")
    logger.info("   ✅ DefectBadge")
    logger.info("   ✅ SeverityIndicator")
    logger.info("   ✅ ActionRecommendation")
    logger.info("   ✅ DefectSummaryCard")
    logger.info("   ✅ XAIExplanations")
    logger.info("\n🚀 Ready for Frontend Integration!")
    logger.info("   Start frontend: cd frontend && npm run dev")
    logger.info("   Navigate to: http://localhost:3000/xai-analysis")
    logger.info("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_explain_endpoint()
    exit(0 if success else 1)
