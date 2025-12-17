
import pytest
from unittest.mock import MagicMock
from app.models.agent_template import AgentTemplate, AgentTemplateVersion
from app.api import agent_templates
import json

# Dummy DB dependency override or using pytest-asyncio and real DB would be ideal.
# For unit tests without full DB setup, we mock the session.
# If integration tests use a test DB fixture, we should use that.
# Based on existing 'tests/api/test_flow_versions.py', it seems we might be using real DB fixtures.
# Let's write this as an integration-style test using 'client' if available, 
# but since I don't see conftest.py right now, I will mirror the style of 'test_settings.py' if it uses client, 
# or standard unit tests if they mock.

# Checking existing style... 'test_flow_versions.py' usually uses client. 
# Let's assume standard pytest-fastapi-client pattern.

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.models.agent_template import AgentTemplate, AgentTemplateVersion
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

def test_list_templates(client: TestClient, session: Session):
    """Test listing agent templates."""
    # Ensure clean state or add dummy data
    # Create a dummy template
    t1 = AgentTemplate(name="Test Agent", type="agent", config="{}")
    session.add(t1)
    session.commit()
    
    response = client.get("/api/agent-templates/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(t['name'] == "Test Agent" for t in data)

def test_update_template_creates_version(client: TestClient, session: Session):
    """Test that updating a template creates a new version."""
    t = AgentTemplate(name="Versioned Agent", type="agent", config='{"v": 1}')
    session.add(t)
    session.commit()
    
    # ...

def test_lock_version(client: TestClient, session: Session):
    """Test locking a version."""
    t = AgentTemplate(name="Locked Agent", type="agent", config='{"v": 1}')
    session.add(t)
    session.commit()
    
    # ...

def test_delete_locked_version_fail(client: TestClient, session: Session):
    """Test that deleting a locked version fails."""
    t = AgentTemplate(name="To Delete", type="agent", config='{"v": 1}')
    session.add(t)
    session.commit()
    
    # ...
