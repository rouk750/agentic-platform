from functools import lru_cache
from sqlmodel import Session, select
from app.database import engine
from app.models.settings import LLMProfile
from app.services.security import get_api_key
from app.providers.factory import LLMProviderFactory

# Cache size - typical number of active models is small
CACHE_SIZE = 32

def get_llm_profile(profile_id: int) -> LLMProfile:
    with Session(engine) as session:
        profile = session.get(LLMProfile, profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        return profile

def get_first_profile() -> LLMProfile | None:
    with Session(engine) as session:
        statement = select(LLMProfile).limit(1)
        results = session.exec(statement)
        return results.first()

def create_llm_instance(profile: LLMProfile):
    """
    Create an LLM instance from a profile.
    This operation handles key decryption but is NOT cached itself.
    """
    api_key = None
    if profile.api_key_ref:
        api_key = get_api_key(profile.api_key_ref)
    
    return LLMProviderFactory.create(profile, api_key)

@lru_cache(maxsize=CACHE_SIZE)
def get_model(profile_id: int):
    """
    Get a cached LLM instance by profile ID.
    This avoids DB lookups and key decryption on repeated calls.
    Pylance/MyPy might infer return type as Any due to decorator.
    """
    profile = get_llm_profile(profile_id)
    return create_llm_instance(profile)

def invalidate_model_cache():
    """Clear the LLM model cache. Call this after updating/deleting profiles."""
    get_model.cache_clear()
