from fastapi.testclient import TestClient
from sqlmodel import Session, select, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import pytest
from app.models.flow import Flow
from app.models.flow_version import FlowVersion
from app.main import app
from app.database import get_session

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

def test_create_version_on_update(client: TestClient, session: Session):
    # 1. Create a flow
    flow_data = {"name": "Test Flow", "data": '{"nodes": [], "edges": []}'}
    response = client.post("/api/flows", json=flow_data)
    assert response.status_code == 200
    flow_id = response.json()["id"]

    # 2. Update flow with NEW data
    new_data = '{"nodes": [{"id": "1"}], "edges": []}'
    response = client.put(f"/api/flows/{flow_id}", json={"name": "Test Flow Updated", "data": new_data})
    assert response.status_code == 200
    
    # 3. Check if version was created
    versions = session.exec(select(FlowVersion).where(FlowVersion.flow_id == flow_id)).all()
    assert len(versions) == 1
    assert versions[0].data == new_data # Logic changed to save version of the new state? 
    # Wait, my logic in api/flows.py was:
    # if should_version:
    #    version = FlowVersion(..., data=db_flow.data, ...)
    # And db_flow was updated properly. So yes, it saves the NEW state.
    
    # 4. Update flow with SAME data
    response = client.put(f"/api/flows/{flow_id}", json={"name": "Test Flow Renamed", "data": new_data})
    assert response.status_code == 200
    
    # 5. Check valid version count (should still be 1)
    versions = session.exec(select(FlowVersion).where(FlowVersion.flow_id == flow_id)).all()
    assert len(versions) == 1

def test_get_versions(client: TestClient, session: Session):
    # Setup flow and versions
    flow_data = {"name": "Version Test", "data": "v1"}
    resp = client.post("/api/flows", json=flow_data)
    flow_id = resp.json()["id"]
    
    # Update twice
    client.put(f"/api/flows/{flow_id}", json={"data": "v2"})
    client.put(f"/api/flows/{flow_id}", json={"data": "v3"})
    
    response = client.get(f"/api/flows/{flow_id}/versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    assert versions[0]["data"] == "v3" # Ordered by created_at desc
    assert versions[1]["data"] == "v2"

def test_restore_version(client: TestClient, session: Session):
    # Setup
    flow_data = {"name": "Restore Test", "data": "original"}
    resp = client.post("/api/flows", json=flow_data)
    flow_id = resp.json()["id"]
    
    # Create version "v2"
    client.put(f"/api/flows/{flow_id}", json={"data": "v2"})
    
    # Verify current is v2
    curr = client.get(f"/api/flows/{flow_id}").json()
    assert curr["data"] == "v2"
    
    # Get version ID
    versions = client.get(f"/api/flows/{flow_id}/versions").json()
    v_id = versions[0]["id"]
    
    # Restore (wait, version v2 is exactly what we have)
    # Let's update to v3 first
    client.put(f"/api/flows/{flow_id}", json={"data": "v3"})
    curr = client.get(f"/api/flows/{flow_id}").json()
    assert curr["data"] == "v3"
    
    # Restore v2
    response = client.post(f"/api/flows/{flow_id}/versions/{v_id}/restore")
    assert response.status_code == 200
    restored = response.json()
    assert restored["data"] == "v2"
    
    # Verify in DB
    final_flow = client.get(f"/api/flows/{flow_id}").json()
    assert final_flow["data"] == "v2"
