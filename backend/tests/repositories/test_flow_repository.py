"""
Tests for Flow Repository
"""

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.repositories.flow_repository import FlowRepository, FlowVersionRepository
from app.models.flow import Flow
from app.models.flow_version import FlowVersion


@pytest.fixture
def session():
    """Create in-memory database session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def flow_repo(session):
    """Create FlowRepository instance."""
    return FlowRepository(session)


@pytest.fixture
def version_repo(session):
    """Create FlowVersionRepository instance."""
    return FlowVersionRepository(session)


class TestFlowRepository:
    """Tests for FlowRepository."""
    
    def test_create_flow(self, flow_repo):
        """Test creating a flow."""
        flow = Flow(name="Test Flow", data='{"nodes": []}')
        created = flow_repo.create(flow)
        
        assert created.id is not None
        assert created.name == "Test Flow"
    
    def test_get_by_id(self, flow_repo):
        """Test getting flow by ID."""
        flow = Flow(name="Test", data="{}")
        created = flow_repo.create(flow)
        
        retrieved = flow_repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_get_by_id_not_found(self, flow_repo):
        """Test getting non-existent flow."""
        result = flow_repo.get_by_id(9999)
        assert result is None
    
    def test_list_all(self, flow_repo):
        """Test listing all flows."""
        flow_repo.create(Flow(name="Flow 1", data="{}"))
        flow_repo.create(Flow(name="Flow 2", data="{}"))
        
        flows = flow_repo.list_all()
        assert len(flows) == 2
    
    def test_list_all_excludes_archived(self, flow_repo):
        """Test that archived flows are excluded by default."""
        flow_repo.create(Flow(name="Active", data="{}"))
        flow_repo.create(Flow(name="Archived", data="{}", is_archived=True))
        
        flows = flow_repo.list_all(include_archived=False)
        assert len(flows) == 1
        assert flows[0].name == "Active"
    
    def test_list_all_includes_archived(self, flow_repo):
        """Test including archived flows."""
        flow_repo.create(Flow(name="Active", data="{}"))
        flow_repo.create(Flow(name="Archived", data="{}", is_archived=True))
        
        flows = flow_repo.list_all(include_archived=True)
        assert len(flows) == 2
    
    def test_update_flow(self, flow_repo):
        """Test updating a flow."""
        flow = flow_repo.create(Flow(name="Original", data="{}"))
        
        flow.name = "Updated"
        updated = flow_repo.update(flow)
        
        assert updated.name == "Updated"
    
    def test_delete_flow(self, flow_repo):
        """Test deleting a flow."""
        flow = flow_repo.create(Flow(name="To Delete", data="{}"))
        
        result = flow_repo.delete(flow.id)
        assert result is True
        assert flow_repo.get_by_id(flow.id) is None
    
    def test_delete_nonexistent(self, flow_repo):
        """Test deleting non-existent flow."""
        result = flow_repo.delete(9999)
        assert result is False
    
    def test_search_by_name(self, flow_repo):
        """Test searching flows by name."""
        flow_repo.create(Flow(name="Customer Support Flow", data="{}"))
        flow_repo.create(Flow(name="Sales Flow", data="{}"))
        flow_repo.create(Flow(name="Other", data="{}"))
        
        results = flow_repo.search_by_name("Flow")
        assert len(results) == 2
    
    def test_archive(self, flow_repo):
        """Test archiving a flow."""
        flow = flow_repo.create(Flow(name="To Archive", data="{}"))
        
        archived = flow_repo.archive(flow.id)
        assert archived.is_archived is True
    
    def test_unarchive(self, flow_repo):
        """Test unarchiving a flow."""
        flow = flow_repo.create(Flow(name="Archived", data="{}", is_archived=True))
        
        unarchived = flow_repo.unarchive(flow.id)
        assert unarchived.is_archived is False
    
    def test_count(self, flow_repo):
        """Test counting flows."""
        flow_repo.create(Flow(name="Flow 1", data="{}"))
        flow_repo.create(Flow(name="Flow 2", data="{}"))
        
        count = flow_repo.count()
        assert count == 2


class TestFlowVersionRepository:
    """Tests for FlowVersionRepository."""
    
    def test_create_version(self, flow_repo, version_repo):
        """Test creating a version."""
        flow = flow_repo.create(Flow(name="Test", data="{}"))
        
        version = FlowVersion(flow_id=flow.id, data='{"v": 1}')
        created = version_repo.create(version)
        
        assert created.id is not None
        assert created.flow_id == flow.id
    
    def test_list_by_flow(self, flow_repo, version_repo):
        """Test listing versions for a flow."""
        flow = flow_repo.create(Flow(name="Test", data="{}"))
        
        version_repo.create(FlowVersion(flow_id=flow.id, data='{"v": 1}'))
        version_repo.create(FlowVersion(flow_id=flow.id, data='{"v": 2}'))
        
        versions = version_repo.list_by_flow(flow.id)
        assert len(versions) == 2
    
    def test_get_latest(self, flow_repo, version_repo):
        """Test getting latest version."""
        flow = flow_repo.create(Flow(name="Test", data="{}"))
        
        from datetime import datetime
        v1 = FlowVersion(flow_id=flow.id, data='{"v": 1}', created_at=datetime(2024, 1, 1))
        v2 = FlowVersion(flow_id=flow.id, data='{"v": 2}', created_at=datetime(2024, 1, 2))
        
        version_repo.create(v1)
        version_repo.create(v2)
        
        latest = version_repo.get_latest(flow.id)
        assert latest.data == '{"v": 2}'
    
    def test_get_locked_versions(self, flow_repo, version_repo):
        """Test getting locked versions."""
        flow = flow_repo.create(Flow(name="Test", data="{}"))
        
        version_repo.create(FlowVersion(flow_id=flow.id, data='{}', is_locked=True))
        version_repo.create(FlowVersion(flow_id=flow.id, data='{}', is_locked=False))
        version_repo.create(FlowVersion(flow_id=flow.id, data='{}', is_locked=True))
        
        locked = version_repo.get_locked_versions(flow.id)
        assert len(locked) == 2
