"""
Test the metrics endpoint fix
"""
import requests
import json

API_URL = "http://localhost:8000"

print("🔍 Testing metrics endpoint...")
print()

try:
    # Start by checking health
    print("1️⃣  Testing health endpoint...")
    health_response = requests.get(f"{API_URL}/api/xai-qc/health", timeout=5)
    
    if health_response.status_code == 200:
        print("   ✅ Health check passed")
        print(f"   📊 Server: {health_response.json()}")
    else:
        print(f"   ❌ Health check failed: {health_response.status_code}")
        exit(1)
    
    print()
    
    # Test metrics endpoint
    print("2️⃣  Testing metrics endpoint...")
    metrics_response = requests.get(f"{API_URL}/api/xai-qc/metrics", timeout=5)
    
    if metrics_response.status_code == 200:
        print("   ✅ Metrics endpoint working!")
        data = metrics_response.json()
        print(f"   📊 Response structure:")
        print(f"      - business_metrics: {'✅' if data.get('business_metrics') else '❌'}")
        print(f"      - detection_metrics: {'✅' if data.get('detection_metrics') else '❌'}")
        print(f"      - segmentation_metrics: {'✅' if data.get('segmentation_metrics') else '❌'}")
        print(f"      - total_inspections: {data.get('total_inspections', 'N/A')}")
        print()
        print("   📈 Detection Performance:")
        if data.get('detection_metrics'):
            det = data['detection_metrics']
            print(f"      - mAP@0.5: {det.get('mAP@0.5', 'N/A')}")
            print(f"      - mAP@0.75: {det.get('mAP@0.75', 'N/A')}")
            print(f"      - mAP: {det.get('mAP', 'N/A')}")
    else:
        print(f"   ❌ Metrics endpoint failed: {metrics_response.status_code}")
        print(f"   📄 Response: {metrics_response.text}")
        exit(1)
    
    print()
    print("✅ All tests passed! Metrics endpoint is fixed! 🎉")
    print()
    print("Now refresh your browser at http://localhost:3000/metrics")
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend server")
    print()
    print("Please start the backend first:")
    print("   Double-click: 1_START_BACKEND.bat")
    print("   Or run: cd backend && python main.py")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
