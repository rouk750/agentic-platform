from cachetools import TTLCache
from threading import Lock
from typing import Optional
from sqlmodel import Session, select
from app.database import engine
from app.models.settings import LLMProfile
from app.services.security import get_api_key
from app.providers.factory import LLMProviderFactory

# Thread-safe cache with 5-minute TTL
# Cache size - typical number of active models is small
CACHE_SIZE = 32
CACHE_TTL = 300  # 5 minutes in seconds

_model_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
_cache_lock = Lock()

def get_llm_profile(profile_id: int, session: Optional[Session] = None) -> LLMProfile:
    """
    Get an LLM profile from the database.
    
    Args:
        profile_id: ID of the profile to retrieve
        session: Optional database session. If not provided, creates a new one.
        
    Returns:
        LLMProfile instance
        
    Raises:
        ValueError: If profile not found
    """
    if session is not None:
        # Use provided session (preferred for dependency injection)
        profile = session.get(LLMProfile, profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        return profile
    else:
        # Fallback: create new session (backward compatibility)
        with Session(engine) as temp_session:
            profile = temp_session.get(LLMProfile, profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")
            return profile

def get_first_profile() -> LLMProfile | None:
    """
    Get the first available LLM profile (fallback for nodes without configured profile).
    
    Returns:
        First LLMProfile or None if no profiles exist
    """
    with Session(engine) as session:
        statement = select(LLMProfile).limit(1)
        results = session.exec(statement)
        return results.first()

def create_llm_instance(profile: LLMProfile):
    """
    Create an LLM instance from a profile.
    This operation handles key decryption but is NOT cached itself.
    
    Args:
        profile: LLMProfile instance
        
    Returns:
        LangChain LLM instance (ChatOpenAI, ChatAnthropic, etc.)
    """
    api_key = None
    if profile.api_key_ref:
        api_key = get_api_key(profile.api_key_ref)
    
    return LLMProviderFactory.create(profile, api_key)

def get_model(profile_id: int, session: Optional[Session] = None):
    """
    Get a cached LLM instance by profile ID.
    This avoids DB lookups and key decryption on repeated calls.
    Cache expires after 5 minutes (TTL).
    
    Args:
        profile_id: ID of the LLM profile
        session: Optional database session (creates new one if not provided)
        
    Returns:
        Cached or newly created LLM instance
    """
    with _cache_lock:
        # Check cache first
        if profile_id in _model_cache:
            return _model_cache[profile_id]
        
        # Cache miss - create new instance
        profile = get_llm_profile(profile_id, session)
        model = create_llm_instance(profile)
        _model_cache[profile_id] = model
        return model

def invalidate_model_cache(profile_id: Optional[int] = None):
    """
    Clear the LLM model cache.
    
    Args:
        profile_id: If provided, only clear this specific model. Otherwise clear all.
    """
    with _cache_lock:
        if profile_id is not None:
            # Selective invalidation
            _model_cache.pop(profile_id, None)
        else:
            # Clear entire cache
            _model_cache.clear()
