from typing import Optional, Any
from app.models.settings import LLMProfile, ProviderType
from app.providers.base import BaseLLMProvider
from langchain_openai import ChatOpenAI

class OpenAIProvider(BaseLLMProvider):
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        # OpenAI supports standard models and compatible ones (proxies, etc.)
        return ChatOpenAI(
            api_key=api_key,
            model=profile.model_id,
            temperature=profile.temperature,
            base_url=profile.base_url
        )

class LMStudioProvider(BaseLLMProvider):
    """
    LM Studio is OpenAI-compatible but typically runs locally.
    """
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        # Check if base_url is set, otherwise default
        base_url = profile.base_url or "http://localhost:1234/v1"
        
        return ChatOpenAI(
            api_key="lm-studio", # Not strictly used but required by client
            model=profile.model_id,
            temperature=profile.temperature,
            base_url=base_url
        )
