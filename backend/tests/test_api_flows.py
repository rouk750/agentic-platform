from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import pytest
import json
from app.main import app
from app.database import get_session

# --- Fixtures Reused ---
# ideally these should be in conftest.py but keeping self-contained for now

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

def test_flow_crud(client: TestClient):
    """Test full CRUD cycle for Flow resources."""
    
    # 1. Create
    flow_data = {
        "name": "Test Flow",
        "description": "A test flow",
        "data": json.dumps({"nodes": [], "edges": []})
    }
    res = client.post("/api/flows", json=flow_data)
    assert res.status_code == 200
    flow = res.json()
    flow_id = flow["id"]
    assert flow["name"] == "Test Flow"
    assert flow["id"] is not None

    # 2. List
    res = client.get("/api/flows")
    assert res.status_code == 200
    flows = res.json()
    assert len(flows) == 1
    assert flows[0]["id"] == flow_id

    # 3. Update
    update_data = {
        "name": "Updated Flow",
        "data": json.dumps({"nodes": [{"id": "1"}], "edges": []})
    }
    res = client.put(f"/api/flows/{flow_id}", json=update_data)
    assert res.status_code == 200
    updated_flow = res.json()
    assert updated_flow["name"] == "Updated Flow"
    
    # 4. Get One
    res = client.get(f"/api/flows/{flow_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Flow"
    
    # 5. Delete
    res = client.delete(f"/api/flows/{flow_id}")
    assert res.status_code == 200
    
    # Verify Delete
    res = client.get(f"/api/flows/{flow_id}")
    assert res.status_code == 404
