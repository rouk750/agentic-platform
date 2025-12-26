"""
Tests for AgentTemplateService
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session

from app.services.template_service import AgentTemplateService
from app.models.agent_template import AgentTemplate, AgentTemplateVersion
from app.schemas.agent_template import AgentTemplateCreate, AgentTemplateUpdate
from app.exceptions import ResourceNotFoundError, ResourceLockedError, ValidationError

@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)

@pytest.fixture
def service(mock_session):
    return AgentTemplateService(mock_session)

class TestAgentTemplateService:
    
    def test_list_templates(self, service, mock_session):
        mock_session.exec.return_value.all.return_value = [
            AgentTemplate(id=1, name="T1", config={}),
            AgentTemplate(id=2, name="T2", config={})
        ]
        
        templates = service.list_templates()
        assert len(templates) == 2
        assert templates[0].name == "T1"
        
    def test_get_template_found(self, service, mock_session):
        t = AgentTemplate(id=1, name="T1", config={})
        mock_session.get.return_value = t
        
        result = service.get_template(1)
        assert result == t
        
    def test_get_template_not_found(self, service, mock_session):
        mock_session.get.return_value = None
        with pytest.raises(ResourceNotFoundError):
            service.get_template(999)
            
    def test_create_template(self, service, mock_session):
        data = AgentTemplateCreate(name="New", type="agent", config='{"model": "gpt-4"}')
        
        # Determine strict structure for return value of add/commit/refresh
        # But we can just verify the calls
        
        created = service.create_template(data)
        
        assert created.name == "New"
        assert mock_session.add.call_count == 2 # Template + Initial Version
        assert mock_session.commit.call_count == 2
        
    def test_update_template_no_version(self, service, mock_session):
        """Update without changing config should not create version."""
        t = AgentTemplate(id=1, name="Old", config='{"a": 1}')
        mock_session.get.return_value = t
        
        update = AgentTemplateUpdate(name="New Name") # config is None/Unset
        
        result = service.update_template(1, update)
        
        assert result.name == "New Name"
        assert mock_session.add.call_count == 1 # Only template update
        
    def test_update_template_with_version(self, service, mock_session):
        """Update changing config should create new version."""
        t = AgentTemplate(id=1, name="Old", config='{"a": 1}')
        service.get_template = MagicMock(return_value=t)
        
        # Mock existing versions check
        mock_session.exec.return_value.all.return_value = [MagicMock()] 
        
        update = AgentTemplateUpdate(config='{"a": 2}')
        
        result = service.update_template(1, update)
        
        assert result.config == '{"a": 2}'
        # Verify version creation call
        assert mock_session.add.call_count == 2 # Template + New Version
        
    def test_delete_template(self, service, mock_session):
        t = AgentTemplate(id=1)
        service.get_template = MagicMock(return_value=t)
        
        mock_session.exec.return_value.all.return_value = [
            AgentTemplateVersion(id=1, template_id=1),
            AgentTemplateVersion(id=2, template_id=1)
        ]
        
        service.delete_template(1)
        
        assert mock_session.delete.call_count == 3 # 2 versions + 1 template
        
    def test_restore_version(self, service, mock_session):
        t = AgentTemplate(id=1, config={"a": 2})
        v = AgentTemplateVersion(id=10, template_id=1, config={"a": 1})
        
        service.get_template = MagicMock(return_value=t)
        mock_session.get.return_value = v
        
        service.restore_version(1, 10)
        
        assert t.config == {"a": 1}
        assert mock_session.add.called
        
    def test_delete_version_success(self, service, mock_session):
        t = AgentTemplate(id=1, config={"a": 2})
        v = AgentTemplateVersion(id=10, template_id=1, config={"a": 1}, is_locked=False)
        
        service.get_template = MagicMock(return_value=t)
        mock_session.get.return_value = v
        
        service.delete_version(1, 10)
        
        mock_session.delete.assert_called_with(v)
        
    def test_delete_version_locked(self, service, mock_session):
        t = AgentTemplate(id=1)
        v = AgentTemplateVersion(id=10, template_id=1, is_locked=True)
        
        service.get_template = MagicMock(return_value=t)
        mock_session.get.return_value = v
        
        with pytest.raises(ResourceLockedError):
            service.delete_version(1, 10)

    def test_delete_active_version(self, service, mock_session):
        t = AgentTemplate(id=1, config={"curr": 1})
        v = AgentTemplateVersion(id=10, template_id=1, config={"curr": 1}, is_locked=False)
        
        service.get_template = MagicMock(return_value=t)
        mock_session.get.return_value = v
        
        with pytest.raises(ValidationError):
            service.delete_version(1, 10)

    def test_toggle_lock(self, service, mock_session):
        v = AgentTemplateVersion(id=10, template_id=1, is_locked=False)
        mock_session.get.side_effect = [v] # get_template is mocked below
        
        service.get_template = MagicMock(return_value=AgentTemplate(id=1))
        
        service.toggle_version_lock(1, 10, True)
        
        assert v.is_locked is True
