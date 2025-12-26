"""
Flow Repository

Data access layer for Flow entities.
"""

from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime

from app.repositories.base import BaseRepository
from app.models.flow import Flow
from app.models.flow_version import FlowVersion


class FlowRepository(BaseRepository[Flow]):
    """Repository for Flow CRUD operations."""
    
    model_class = Flow
    
    def list_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_archived: bool = False
    ) -> List[Flow]:
        """
        List flows with optional archive filter.
        
        Args:
            skip: Pagination offset
            limit: Maximum results
            include_archived: Whether to include archived flows
            
        Returns:
            List of flows
        """
        statement = select(Flow)
        
        if not include_archived:
            statement = statement.where(Flow.is_archived == False)
        
        statement = statement.offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    
    def search_by_name(self, name: str) -> List[Flow]:
        """
        Search flows by name (case-insensitive contains).
        
        Args:
            name: Search term
            
        Returns:
            Matching flows
        """
        statement = select(Flow).where(Flow.name.ilike(f"%{name}%"))
        return list(self.session.exec(statement).all())
    
    def archive(self, flow_id: int) -> Optional[Flow]:
        """
        Archive a flow (soft delete).
        
        Args:
            flow_id: Flow ID to archive
            
        Returns:
            Archived flow or None if not found
        """
        flow = self.get_by_id(flow_id)
        if flow:
            flow.is_archived = True
            flow.updated_at = datetime.utcnow()
            self.session.add(flow)
            self.session.commit()
            self.session.refresh(flow)
        return flow
    
    def unarchive(self, flow_id: int) -> Optional[Flow]:
        """
        Unarchive a flow.
        
        Args:
            flow_id: Flow ID to unarchive
            
        Returns:
            Unarchived flow or None if not found
        """
        flow = self.get_by_id(flow_id)
        if flow:
            flow.is_archived = False
            flow.updated_at = datetime.utcnow()
            self.session.add(flow)
            self.session.commit()
            self.session.refresh(flow)
        return flow


class FlowVersionRepository(BaseRepository[FlowVersion]):
    """Repository for FlowVersion CRUD operations."""
    
    model_class = FlowVersion
    
    def list_by_flow(
        self, 
        flow_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[FlowVersion]:
        """
        List versions for a specific flow, ordered by creation date descending.
        
        Args:
            flow_id: Parent flow ID
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of versions
        """
        statement = (
            select(FlowVersion)
            .where(FlowVersion.flow_id == flow_id)
            .order_by(FlowVersion.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
    
    def get_latest(self, flow_id: int) -> Optional[FlowVersion]:
        """
        Get the most recent version for a flow.
        
        Args:
            flow_id: Parent flow ID
            
        Returns:
            Latest version or None
        """
        statement = (
            select(FlowVersion)
            .where(FlowVersion.flow_id == flow_id)
            .order_by(FlowVersion.created_at.desc())
            .limit(1)
        )
        return self.session.exec(statement).first()
    
    def get_locked_versions(self, flow_id: int) -> List[FlowVersion]:
        """
        Get all locked versions for a flow.
        
        Args:
            flow_id: Parent flow ID
            
        Returns:
            List of locked versions
        """
        statement = (
            select(FlowVersion)
            .where(FlowVersion.flow_id == flow_id)
            .where(FlowVersion.is_locked == True)
        )
        return list(self.session.exec(statement).all())
    
    def delete_unlocked_versions(self, flow_id: int, version_ids: List[int]) -> int:
        """
        Delete multiple unlocked versions.
        
        Args:
            flow_id: Parent flow ID (for validation)
            version_ids: IDs of versions to delete
            
        Returns:
            Number of deleted versions
        """
        deleted_count = 0
        for vid in version_ids:
            version = self.get_by_id(vid)
            if version and version.flow_id == flow_id and not version.is_locked:
                self.session.delete(version)
                deleted_count += 1
        
        self.session.commit()
        return deleted_count
