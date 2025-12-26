"""
AgentTemplate Service

Business logic layer for AgentTemplate operations.
"""

from typing import List
from datetime import datetime
from sqlmodel import Session, select

from app.models.agent_template import AgentTemplate, AgentTemplateVersion
from app.schemas.agent_template import AgentTemplateCreate, AgentTemplateUpdate
from app.exceptions import ResourceNotFoundError, ResourceLockedError, ValidationError
from app.logging import get_logger

logger = get_logger(__name__)


class AgentTemplateService:
    """
    Service layer for AgentTemplate business logic.
    
    Encapsulates complex operations like versioning and validation.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def list_templates(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_archived: bool = False
    ) -> List[AgentTemplate]:
        """List templates with pagination and archive filter."""
        query = select(AgentTemplate)
        if not include_archived:
            query = query.where(AgentTemplate.is_archived == False)
        query = query.offset(skip).limit(limit)
        return list(self.session.exec(query).all())
    
    def get_template(self, template_id: int) -> AgentTemplate:
        """
        Get template by ID.
        
        Raises:
            ResourceNotFoundError: If template not found
        """
        template = self.session.get(AgentTemplate, template_id)
        if not template:
            raise ResourceNotFoundError("AgentTemplate", template_id)
        return template
    
    def create_template(self, data: AgentTemplateCreate) -> AgentTemplate:
        """
        Create a new template with initial version.
        
        Args:
            data: Template creation data
            
        Returns:
            Created template
        """
        template = AgentTemplate.model_validate(data)
        template.created_at = datetime.utcnow()
        template.updated_at = datetime.utcnow()
        
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        
        # Create initial version
        version = AgentTemplateVersion(
            template_id=template.id,
            config=template.config,
            created_at=datetime.utcnow(),
            version_number=1
        )
        self.session.add(version)
        self.session.commit()
        
        logger.info("template_created", template_id=template.id, name=template.name)
        return template
    
    def update_template(self, template_id: int, data: AgentTemplateUpdate) -> AgentTemplate:
        """
        Update template and create version if config changed.
        
        Args:
            template_id: ID of template to update
            data: Update data
            
        Returns:
            Updated template
        """
        template = self.get_template(template_id)
        
        # Check if config is changing (triggers version creation)
        should_version = data.config and data.config != template.config
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        
        # Create version if config changed
        if should_version:
            self._create_version(template)
        
        logger.info("template_updated", template_id=template.id, versioned=should_version)
        return template
    
    def delete_template(self, template_id: int) -> bool:
        """
        Delete template and all its versions.
        """
        template = self.get_template(template_id)
        
        # Delete all versions first
        versions = self.session.exec(
            select(AgentTemplateVersion).where(AgentTemplateVersion.template_id == template_id)
        ).all()
        for version in versions:
            self.session.delete(version)
        
        self.session.delete(template)
        self.session.commit()
        
        logger.info("template_deleted", template_id=template_id, versions_deleted=len(versions))
        return True
    
    def _create_version(self, template: AgentTemplate) -> AgentTemplateVersion:
        """Create a version snapshot of the current template state."""
        # Get next version number
        existing = self.session.exec(
            select(AgentTemplateVersion).where(AgentTemplateVersion.template_id == template.id)
        ).all()
        next_version = len(existing) + 1
        
        version = AgentTemplateVersion(
            template_id=template.id,
            config=template.config,
            created_at=datetime.utcnow(),
            version_number=next_version
        )
        self.session.add(version)
        self.session.commit()
        return version
    
    # Version Management
    
    def list_versions(self, template_id: int) -> List[AgentTemplateVersion]:
        """List all versions for a template."""
        self.get_template(template_id)  # Validate exists
        versions = self.session.exec(
            select(AgentTemplateVersion)
            .where(AgentTemplateVersion.template_id == template_id)
            .order_by(AgentTemplateVersion.created_at.desc())
        ).all()
        return list(versions)
    
    def restore_version(self, template_id: int, version_id: int) -> AgentTemplate:
        """
        Restore template to a previous version.
        """
        template = self.get_template(template_id)
        version = self.session.get(AgentTemplateVersion, version_id)
        
        if not version:
            raise ResourceNotFoundError("AgentTemplateVersion", version_id)
        
        if version.template_id != template_id:
            raise ValidationError("Version does not belong to this template")
        
        template.config = version.config
        template.updated_at = datetime.utcnow()
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        
        logger.info("template_version_restored", template_id=template_id, version_id=version_id)
        return template
    
    def delete_version(self, template_id: int, version_id: int) -> bool:
        """
        Delete a single version.
        """
        template = self.get_template(template_id)
        version = self.session.get(AgentTemplateVersion, version_id)
        
        if not version:
            raise ResourceNotFoundError("AgentTemplateVersion", version_id)
        
        if version.template_id != template_id:
            raise ValidationError("Version does not belong to this template")
        
        if version.is_locked:
            raise ResourceLockedError("AgentTemplateVersion", version_id)
        
        if template.config == version.config:
            raise ValidationError("Cannot delete the current active version")
        
        self.session.delete(version)
        self.session.commit()
        
        logger.info("template_version_deleted", template_id=template_id, version_id=version_id)
        return True
    
    def toggle_version_lock(
        self, 
        template_id: int, 
        version_id: int, 
        is_locked: bool
    ) -> AgentTemplateVersion:
        """
        Lock or unlock a version.
        """
        self.get_template(template_id)  # Validate exists
        version = self.session.get(AgentTemplateVersion, version_id)
        
        if not version:
            raise ResourceNotFoundError("AgentTemplateVersion", version_id)
        
        if version.template_id != template_id:
            raise ValidationError("Version does not belong to this template")
        
        version.is_locked = is_locked
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        return version
