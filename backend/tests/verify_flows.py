import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_flow_crud():
    print("Testing Flow CRUD...")
    
    # 1. Create
    flow_data = {
        "name": "Test Flow",
        "description": "A test flow",
        "data": json.dumps({"nodes": [], "edges": []})
    }
    res = requests.post(f"{BASE_URL}/flows", json=flow_data)
    assert res.status_code == 200
    flow = res.json()
    flow_id = flow["id"]
    print(f"Created flow {flow_id}")
    
    # 2. List
    res = requests.get(f"{BASE_URL}/flows")
    assert res.status_code == 200
    flows = res.json()
    assert len(flows) >= 1
    print(f"Listed {len(flows)} flows")
    
    # 3. Update
    update_data = {
        "name": "Updated Flow",
        "data": json.dumps({"nodes": [{"id": "1"}], "edges": []})
    }
    res = requests.put(f"{BASE_URL}/flows/{flow_id}", json=update_data)
    assert res.status_code == 200
    updated_flow = res.json()
    assert updated_flow["name"] == "Updated Flow"
    print("Updated flow")
    
    # 4. Get One
    res = requests.get(f"{BASE_URL}/flows/{flow_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Flow"
    print("Retrieved flow")
    
    # 5. Delete
    res = requests.delete(f"{BASE_URL}/flows/{flow_id}")
    assert res.status_code == 200
    print("Deleted flow")
    
    # Verify Delete
    res = requests.get(f"{BASE_URL}/flows/{flow_id}")
    assert res.status_code == 404
    print("Verified deletion")

if __name__ == "__main__":
    try:
        test_flow_crud()
        print("✅ Flow Persistence Verified")
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
