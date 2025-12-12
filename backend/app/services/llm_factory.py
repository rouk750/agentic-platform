from sqlmodel import Session, select
from app.database import engine
from app.models.settings import LLMProfile, ProviderType
from app.services.security import get_api_key
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
# Using community for Ollama if available, otherwise might need custom or official integration
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

def get_llm_profile(profile_id: int) -> LLMProfile:
    with Session(engine) as session:
        profile = session.get(LLMProfile, profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        # We need to access fields before session closes if they are lazy loaded? 
        # But here fields are basic types.
        # api_key_ref is a string.
        # We'll return a copy or just the object (detached state might be an issue if we try to refresh later)
        # But for read-only it is fine.
        return profile

def get_first_profile() -> LLMProfile | None:
    with Session(engine) as session:
        # Get the first one
        statement = select(LLMProfile).limit(1)
        results = session.exec(statement)
        return results.first()

from app.providers.factory import LLMProviderFactory

def create_llm_instance(profile: LLMProfile):
    api_key = None
    if profile.api_key_ref:
        api_key = get_api_key(profile.api_key_ref)
    
    return LLMProviderFactory.create(profile, api_key)
