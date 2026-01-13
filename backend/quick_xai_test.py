"""Quick test script for XAI endpoints."""
import requests
import time
import subprocess
import sys
import os

# Test image path
TEST_IMAGE = r"C:\Users\Amine EL-Hend\Documents\GitHub\RadiKal-V2.0\DATA\training\Difetto1\RRT-30R_Img1_A80_S1_[3][34].png"
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    try:
        resp = requests.get(f"{BASE_URL}/api/xai-qc/health", timeout=5)
        print(f"[HEALTH] Status: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"[HEALTH] Error: {e}")
        return False

def test_explain(method):
    """Test explain endpoint with specific method."""
    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': ('test.png', f, 'image/png')}
            resp = requests.post(
                f"{BASE_URL}/api/xai-qc/explain?methods={method}",
                files=files,
                timeout=120  # 2 min timeout for slower methods
            )
        print(f"[{method.upper()}] Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if 'explanations' in data:
                for exp in data['explanations']:
                    print(f"  - Method: {exp.get('method')}, Has heatmap: {'heatmap' in exp}")
            return True
        else:
            print(f"  Error: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[{method.upper()}] Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("RadiKal XAI Quick Test")
    print("=" * 60)
    
    # Check if server is running
    if not test_health():
        print("\nServer not running! Please start it first with:")
        print("  cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("\nTesting XAI methods...")
    results = {}
    
    # Test each method
    for method in ['gradcam', 'shap', 'lime']:
        print(f"\n--- Testing {method} ---")
        results[method] = test_explain(method)
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for method, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {method.upper():10} {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests PASSED!" if all_passed else "Some tests FAILED!"))
