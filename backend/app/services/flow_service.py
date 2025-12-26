"""
Flow Service

Business logic layer for Flow operations.
"""

from typing import List, Optional
from datetime import datetime
from sqlmodel import Session

from app.repositories.flow_repository import FlowRepository, FlowVersionRepository
from app.models.flow import Flow
from app.models.flow_version import FlowVersion
from app.schemas.flow import FlowCreate, FlowUpdate
from app.exceptions import ResourceNotFoundError, ResourceLockedError, ValidationError
from app.logging import get_logger

logger = get_logger(__name__)


class FlowService:
    """
    Service layer for Flow business logic.
    
    Encapsulates complex operations like versioning and validation.
    """
    
    def __init__(self, session: Session):
        self.flow_repo = FlowRepository(session)
        self.version_repo = FlowVersionRepository(session)
        self.session = session
    
    def list_flows(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_archived: bool = False
    ) -> List[Flow]:
        """List flows with pagination and archive filter."""
        return self.flow_repo.list_all(skip, limit, include_archived)
    
    def get_flow(self, flow_id: int) -> Flow:
        """
        Get flow by ID.
        
        Raises:
            ResourceNotFoundError: If flow not found
        """
        flow = self.flow_repo.get_by_id(flow_id)
        if not flow:
            raise ResourceNotFoundError("Flow", flow_id)
        return flow
    
    def create_flow(self, data: FlowCreate) -> Flow:
        """
        Create a new flow.
        
        Args:
            data: Flow creation data
            
        Returns:
            Created flow
        """
        flow = Flow(
            name=data.name,
            description=data.description,
            data=data.data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        flow = self.flow_repo.create(flow)
        logger.info("flow_created", flow_id=flow.id, name=flow.name)
        return flow
    
    def update_flow(self, flow_id: int, data: FlowUpdate) -> Flow:
        """
        Update flow and create version if data changed.
        
        Args:
            flow_id: ID of flow to update
            data: Update data
            
        Returns:
            Updated flow
            
        Raises:
            ResourceNotFoundError: If flow not found
        """
        flow = self.get_flow(flow_id)
        
        # Check if data is changing (triggers version creation)
        should_version = data.data and data.data != flow.data
        
        # Apply updates
        if data.name is not None:
            flow.name = data.name
        if data.description is not None:
            flow.description = data.description
        if data.data is not None:
            flow.data = data.data
        if data.is_archived is not None:
            flow.is_archived = data.is_archived
        
        flow.updated_at = datetime.utcnow()
        flow = self.flow_repo.update(flow)
        
        # Create version if data changed
        if should_version:
            self._create_version(flow)
        
        logger.info("flow_updated", flow_id=flow.id, versioned=should_version)
        return flow
    
    def delete_flow(self, flow_id: int) -> bool:
        """
        Delete flow and all its versions.
        
        Args:
            flow_id: ID of flow to delete
            
        Returns:
            True if deleted
            
        Raises:
            ResourceNotFoundError: If flow not found
        """
        flow = self.get_flow(flow_id)
        
        # Delete all versions first
        versions = self.version_repo.list_by_flow(flow_id)
        for version in versions:
            self.session.delete(version)
        
        self.flow_repo.delete(flow_id)
        logger.info("flow_deleted", flow_id=flow_id, versions_deleted=len(versions))
        return True
    
    def _create_version(self, flow: Flow) -> FlowVersion:
        """Create a version snapshot of the current flow state."""
        version = FlowVersion(
            flow_id=flow.id,
            data=flow.data,
            created_at=datetime.utcnow()
        )
        return self.version_repo.create(version)
    
    # Version Management
    
    def list_versions(self, flow_id: int) -> List[FlowVersion]:
        """List all versions for a flow."""
        self.get_flow(flow_id)  # Validate flow exists
        return self.version_repo.list_by_flow(flow_id)
    
    def restore_version(self, flow_id: int, version_id: int) -> Flow:
        """
        Restore flow to a previous version.
        
        Args:
            flow_id: Flow ID
            version_id: Version to restore
            
        Returns:
            Updated flow
            
        Raises:
            ResourceNotFoundError: If flow or version not found
            ValidationError: If version doesn't belong to flow
        """
        flow = self.get_flow(flow_id)
        version = self.version_repo.get_by_id(version_id)
        
        if not version:
            raise ResourceNotFoundError("FlowVersion", version_id)
        
        if version.flow_id != flow_id:
            raise ValidationError(
                "Version does not belong to this flow",
                field="version_id"
            )
        
        flow.data = version.data
        flow.updated_at = datetime.utcnow()
        flow = self.flow_repo.update(flow)
        
        logger.info("flow_version_restored", flow_id=flow_id, version_id=version_id)
        return flow
    
    def delete_version(self, flow_id: int, version_id: int) -> bool:
        """
        Delete a single version.
        
        Args:
            flow_id: Flow ID
            version_id: Version to delete
            
        Returns:
            True if deleted
            
        Raises:
            ResourceNotFoundError: If not found
            ResourceLockedError: If version is locked
            ValidationError: If version is current active
        """
        flow = self.get_flow(flow_id)
        version = self.version_repo.get_by_id(version_id)
        
        if not version:
            raise ResourceNotFoundError("FlowVersion", version_id)
        
        if version.flow_id != flow_id:
            raise ValidationError("Version does not belong to this flow")
        
        if version.is_locked:
            raise ResourceLockedError("FlowVersion", version_id)
        
        if flow.data == version.data:
            raise ValidationError("Cannot delete the current active version")
        
        self.version_repo.delete(version_id)
        logger.info("flow_version_deleted", flow_id=flow_id, version_id=version_id)
        return True
    
    def toggle_version_lock(
        self, 
        flow_id: int, 
        version_id: int, 
        is_locked: bool
    ) -> FlowVersion:
        """
        Lock or unlock a version.
        
        Args:
            flow_id: Flow ID
            version_id: Version ID
            is_locked: New lock state
            
        Returns:
            Updated version
        """
        self.get_flow(flow_id)  # Validate flow exists
        version = self.version_repo.get_by_id(version_id)
        
        if not version:
            raise ResourceNotFoundError("FlowVersion", version_id)
        
        if version.flow_id != flow_id:
            raise ValidationError("Version does not belong to this flow")
        
        version.is_locked = is_locked
        return self.version_repo.update(version)
