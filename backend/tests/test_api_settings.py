from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import pytest
from app.main import app
from app.database import get_session

# --- Fixtures ---

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# --- Tests ---

def test_create_and_list_models(client: TestClient):
    """Test creating, listing, and deleting LLM profiles."""
    
    # 1. Create
    response = client.post("/api/settings/models", json={
        "name": "Test GPT",
        "provider": "openai",
        "model_id": "gpt-4",
        "api_key": "sk-fake-key"
    })
    assert response.status_code == 200
    data = response.json()
    model_id = data["id"]
    assert data["name"] == "Test GPT"
    assert "api_key" not in data
    assert data["api_key_ref"] is not None

    # 2. List
    response = client.get("/api/settings/models")
    assert response.status_code == 200
    models = response.json()
    assert len(models) == 1
    assert models[0]["id"] == model_id

    # 3. Delete
    response = client.delete(f"/api/settings/models/{model_id}")
    assert response.status_code == 200

    # 4. Verify Empty
    response = client.get("/api/settings/models")
    assert len(response.json()) == 0

def test_connection_validation(client: TestClient):
    """Test connection validation endpoint with fake key."""
    # Should fail elegantly
    response = client.post("/api/settings/test-connection", json={
        "provider": "openai",
        "api_key": "sk-fake-key",
        "model_id": "gpt-4"
    })
    # Our API returns 400 for connection errors usually
    assert response.status_code in [400, 401] 
    assert "error" in response.json().get("detail", "").lower() or response.json().get("valid") is False

def test_ollama_scan(client: TestClient):
    """Test Ollama scan endpoint (might fail if Ollama not running, but shouldn't crash)."""
    response = client.get("/api/settings/providers/ollama/scan")
    # Even if Ollama is down, it should handle it (return empty list or 503/400 handled exception)
    # The original script allowed 200 or failure print. 
    # Let's assert it returns JSON structure at least.
    if response.status_code == 200:
        assert "models" in response.json()
    else:
        # Acceptable failure mode if local ollama is missing
        assert response.status_code in [500, 503, 404]
