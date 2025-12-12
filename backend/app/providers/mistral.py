from typing import Optional, Any
from app.models.settings import LLMProfile
from app.providers.base import BaseLLMProvider

try:
    from langchain_mistralai import ChatMistralAI
except ImportError:
    # Fallback to community if specific package fails
    from langchain_community.chat_models import ChatMistralAI

class MistralProvider(BaseLLMProvider):
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        return ChatMistralAI(
            api_key=api_key,
            model=profile.model_id,
            temperature=profile.temperature,
            endpoint=profile.base_url 
        )
