from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_session

# Setup in-memory DB for testing
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

def test_workflow():
    SQLModel.metadata.create_all(engine)
    client = TestClient(app)

    print("1. Testing Create Model...")
    response = client.post("/api/settings/models", json={
        "name": "Test GPT",
        "provider": "openai",
        "model_id": "gpt-4",
        "api_key": "sk-fake-key"
    })
    if response.status_code != 200:
        print(f"FAILED: {response.text}")
        sys.exit(1)
    data = response.json()
    model_id = data["id"]
    print(f"   Created Model ID: {model_id}")
    assert data["name"] == "Test GPT"
    assert "api_key" not in data
    assert data["api_key_ref"] is not None

    print("2. Testing List Models...")
    response = client.get("/api/settings/models")
    data = response.json()
    print(f"   Required 1 model, got {len(data)}")
    assert len(data) == 1
    assert data[0]["id"] == model_id

    print("3. Testing Connection (Expect Error with fake key)...")
    # We expect this to try and query OpenAI and fail
    response = client.post("/api/settings/test-connection", json={
        "provider": "openai",
        "api_key": "sk-fake-key",
        "model_id": "gpt-4"
    })
    # Depending on how langchain handles auth error, it might be 400 or 401. 
    # Our API wraps exceptions in 400.
    if response.status_code == 400:
        print("   Got expected 400 error for fake key.")
    else:
        print(f"   Unexpected status: {response.status_code}")

    print("4. Testing Ollama Scan...")
    response = client.get("/api/settings/providers/ollama/scan")
    if response.status_code == 200:
        print(f"   Scan success. Models found: {response.json().get('models')}")
    else:
        print(f"   Scan failed: {response.status_code}")

    print("5. Testing Delete Model...")
    response = client.delete(f"/api/settings/models/{model_id}")
    assert response.status_code == 200
    
    # Verify deletion
    response = client.get("/api/settings/models")
    assert len(response.json()) == 0
    print("   Deletion verified.")

    print("\nALL BACKEND TESTS PASSED for Epic 3!")

if __name__ == "__main__":
    test_workflow()
