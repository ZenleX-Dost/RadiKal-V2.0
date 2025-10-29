"""
Test the backend API /explain endpoint to see what it's returning
"""

import requests
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
TEST_IMAGE = Path("DATA/test/Difetto2/bam5_Img2_A80_S1_[11][4].png")  # Porosity

print("="*60)
print("Testing Backend API /explain endpoint")
print("="*60)

# Check if backend is running
print("\n1. Checking backend health...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        print(f"   ✅ Backend is running")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ❌ Backend returned status {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Cannot connect to backend: {e}")
    print(f"   Make sure backend is running: python backend/run_server.py")
    exit(1)

# Test explain endpoint
print(f"\n2. Testing /explain endpoint with: {TEST_IMAGE.name}")

if not TEST_IMAGE.exists():
    print(f"   ❌ Test image not found: {TEST_IMAGE}")
    exit(1)

try:
    with open(TEST_IMAGE, 'rb') as f:
        files = {'file': (TEST_IMAGE.name, f, 'image/png')}
        response = requests.post(
            f"{BACKEND_URL}/api/explain",
            files=files,
            timeout=30
        )
    
    if response.status_code != 200:
        print(f"   ❌ API call failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
    
    print(f"   ✅ API call successful")
    
    # Parse response
    data = response.json()
    
    # Check metadata
    if 'metadata' in data and 'prediction' in data['metadata']:
        prediction = data['metadata']['prediction']
        print(f"\n3. Prediction Results:")
        print(f"   Class ID: {prediction.get('predicted_class')}")
        print(f"   Class Name: {prediction.get('predicted_class_name')}")
        print(f"   Full Name: {prediction.get('predicted_class_full_name')}")
        print(f"   Confidence: {prediction.get('confidence')*100:.1f}%")
        print(f"   Severity: {prediction.get('severity')}")
        
        # Check probabilities
        if 'probabilities' in data['metadata']:
            print(f"\n4. All Class Probabilities:")
            for class_name, prob in data['metadata']['probabilities'].items():
                print(f"   {class_name}: {prob*100:.2f}%")
        
        # Expected vs actual
        print(f"\n5. Validation:")
        expected = "PO"  # Porosity
        actual = prediction.get('predicted_class_name')
        if actual == expected:
            print(f"   ✅ CORRECT: Expected {expected}, got {actual}")
        else:
            print(f"   ❌ WRONG: Expected {expected}, got {actual}")
            print(f"   ⚠️  This indicates a problem with the classification!")
    else:
        print(f"   ❌ No prediction metadata in response")
        print(f"   Response keys: {data.keys()}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test Complete")
print("="*60)
