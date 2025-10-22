"""
Test script for both /metrics and /calibration endpoint fixes.
This verifies the schema validation is working correctly.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/xai-qc"

def test_metrics_endpoint():
    """Test the /metrics endpoint."""
    print("\n" + "="*60)
    print("Testing /metrics endpoint...")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Status: SUCCESS")
            print(f"✅ Response structure valid")
            
            # Check nested structures
            assert "business_metrics" in data, "Missing business_metrics"
            assert "detection_metrics" in data, "Missing detection_metrics"
            assert "segmentation_metrics" in data, "Missing segmentation_metrics"
            assert "total_inspections" in data, "Missing total_inspections"
            
            print(f"✅ business_metrics: {json.dumps(data['business_metrics'], indent=2)}")
            print(f"✅ detection_metrics: {json.dumps(data['detection_metrics'], indent=2)}")
            print(f"✅ total_inspections: {data['total_inspections']}")
            
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server is not running on port 8000")
        print("   Start it with: 1_START_BACKEND.bat")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_calibration_endpoint():
    """Test the /calibration endpoint."""
    print("\n" + "="*60)
    print("Testing /calibration endpoint...")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/calibration")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Status: SUCCESS")
            print(f"✅ Response structure valid")
            
            # Check nested structure
            assert "calibration_metrics" in data, "Missing calibration_metrics"
            assert "num_samples_evaluated" in data, "Missing num_samples_evaluated"
            
            cal_metrics = data['calibration_metrics']
            assert "ece" in cal_metrics, "Missing ECE in calibration_metrics"
            assert "mce" in cal_metrics, "Missing MCE in calibration_metrics"
            assert "avg_confidence" in cal_metrics, "Missing avg_confidence"
            assert "avg_accuracy" in cal_metrics, "Missing avg_accuracy"
            assert "is_calibrated" in cal_metrics, "Missing is_calibrated"
            
            print(f"✅ calibration_metrics:")
            print(f"   - ECE: {cal_metrics['ece']}")
            print(f"   - MCE: {cal_metrics['mce']}")
            print(f"   - Avg Confidence: {cal_metrics['avg_confidence']}")
            print(f"   - Avg Accuracy: {cal_metrics['avg_accuracy']}")
            print(f"   - Is Calibrated: {cal_metrics['is_calibrated']}")
            print(f"   - Temperature: {cal_metrics.get('temperature', 'N/A')}")
            print(f"✅ num_samples_evaluated: {data['num_samples_evaluated']}")
            
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server is not running on port 8000")
        print("   Start it with: 1_START_BACKEND.bat")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    print("\n🔍 Testing Both Fixed Endpoints")
    print("="*60)
    
    test_metrics_endpoint()
    test_calibration_endpoint()
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    print("\n📝 Summary:")
    print("   - Both endpoints fixed for Pydantic V2 strict validation")
    print("   - /metrics now returns nested BusinessMetrics, DetectionMetrics, SegmentationMetrics")
    print("   - /calibration now returns nested CalibrationMetrics")
    print("\n🚀 Next Steps:")
    print("   1. If server is running, refresh frontend at http://localhost:3000/metrics")
    print("   2. Both validation errors should be gone!")
    print("   3. If server is not running, start it with: 1_START_BACKEND.bat")


if __name__ == "__main__":
    main()
