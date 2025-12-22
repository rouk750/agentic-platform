"""
LLM Profile Repository

Data access layer for LLM Profile entities.
"""

from typing import List, Optional
from sqlmodel import Session, select

from app.repositories.base import BaseRepository
from app.models.settings import LLMProfile, ProviderType


class LLMProfileRepository(BaseRepository[LLMProfile]):
    """Repository for LLMProfile CRUD operations."""
    
    model_class = LLMProfile
    
    def list_by_provider(self, provider: ProviderType) -> List[LLMProfile]:
        """
        List profiles filtered by provider type.
        
        Args:
            provider: Provider type to filter by
            
        Returns:
            List of profiles for the provider
        """
        statement = select(LLMProfile).where(LLMProfile.provider == provider)
        return list(self.session.exec(statement).all())
    
    def get_by_name(self, name: str) -> Optional[LLMProfile]:
        """
        Get profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile if found, None otherwise
        """
        statement = select(LLMProfile).where(LLMProfile.name == name)
        return self.session.exec(statement).first()
    
    def get_first(self) -> Optional[LLMProfile]:
        """
        Get the first available profile (for fallback scenarios).
        
        Returns:
            First profile or None
        """
        statement = select(LLMProfile).limit(1)
        return self.session.exec(statement).first()
    
    def exists_with_model(self, provider: ProviderType, model_id: str) -> bool:
        """
        Check if a profile with the given provider and model already exists.
        
        Args:
            provider: Provider type
            model_id: Model identifier
            
        Returns:
            True if exists, False otherwise
        """
        statement = (
            select(LLMProfile)
            .where(LLMProfile.provider == provider)
            .where(LLMProfile.model_id == model_id)
        )
        return self.session.exec(statement).first() is not None
