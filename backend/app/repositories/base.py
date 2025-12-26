"""
Repository Pattern - Base Classes

Provides a generic repository interface for data access abstraction.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Type
from sqlmodel import Session, select

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository providing CRUD operations.
    
    All repositories should extend this class to ensure consistent
    data access patterns across the application.
    """
    
    model_class: Type[T]
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLModel/SQLAlchemy session for database operations
        """
        self.session = session
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Retrieve entity by primary key.
        
        Args:
            id: Primary key value
            
        Returns:
            Entity if found, None otherwise
        """
        return self.session.get(self.model_class, id)
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Retrieve all entities with optional pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of entities
        """
        statement = select(self.model_class).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    
    def create(self, entity: T) -> T:
        """
        Create new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with ID populated
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def update(self, entity: T) -> T:
        """
        Update existing entity.
        
        Args:
            entity: Entity with updated values
            
        Returns:
            Updated entity
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def delete(self, id: int) -> bool:
        """
        Delete entity by ID.
        
        Args:
            id: Primary key of entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        entity = self.get_by_id(id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False
    
    def count(self) -> int:
        """
        Count total entities.
        
        Returns:
            Total count
        """
        from sqlalchemy import func
        statement = select(func.count()).select_from(self.model_class)
        return self.session.exec(statement).one()
