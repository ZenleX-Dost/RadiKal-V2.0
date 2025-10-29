"""
Test the /api/xai-qc/explain endpoint to see the response structure
"""
import requests
import json
from pathlib import Path

# Find a test image
data_dir = Path("DATA")
test_images = list(data_dir.rglob("*.png"))

if test_images:
    test_image = test_images[0]
    print(f"Testing with: {test_image}")
    
    try:
        with open(test_image, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/api/xai-qc/explain',
                files={'file': f}
            )
        
        print(f"\n✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📦 Response keys: {list(data.keys())}")
            print(f"\n📄 Full response:")
            print(json.dumps({k: v for k, v in data.items() if k not in ['aggregated_heatmap', 'explanations']}, indent=2))
            
            if 'metadata' in data:
                print(f"\n📊 Metadata keys: {list(data['metadata'].keys())}")
                
                if 'prediction' in data['metadata']:
                    pred = data['metadata']['prediction']
                    print(f"\n🎯 Prediction keys: {list(pred.keys())}")
                    print(f"\n✨ Prediction:")
                    print(json.dumps(pred, indent=2))
            else:
                print("\n⚠️  NO METADATA IN RESPONSE!")
        else:
            print(f"\n❌ Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Failed: {e}")
else:
    print("No test images found")
