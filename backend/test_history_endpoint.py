"""
Test the /history API endpoint
"""
import requests
import json

def test_history_endpoint():
    """Test the /history endpoint"""
    
    print("=" * 60)
    print("Testing /history API Endpoint")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/xai-qc"
    
    print("\n1. Testing /history endpoint (page 1)...")
    try:
        response = requests.get(f"{base_url}/history", params={"page": 1, "page_size": 20})
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response received:")
        print(json.dumps(data, indent=2))
        
        print(f"\n📊 Summary:")
        print(f"   - Total analyses: {data['total_count']}")
        print(f"   - Current page: {data['page']}")
        print(f"   - Page size: {data['page_size']}")
        print(f"   - Has more: {data['has_more']}")
        print(f"   - Analyses returned: {len(data['analyses'])}")
        
        if data['analyses']:
            print(f"\n📋 First analysis:")
            first = data['analyses'][0]
            print(f"   - ID: {first['id']}")
            print(f"   - Filename: {first['filename']}")
            print(f"   - Detections: {first['num_detections']}")
            print(f"   - Confidence: {first['mean_confidence']:.2%}")
            print(f"   - Status: {first['status']}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to backend server")
        print("   Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n2. Testing with filters...")
    try:
        response = requests.get(
            f"{base_url}/history",
            params={"page": 1, "page_size": 10, "status": "completed"}
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Filter by status='completed': {len(data['analyses'])} results")
        
    except Exception as e:
        print(f"❌ Error testing filters: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All endpoint tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_history_endpoint()
