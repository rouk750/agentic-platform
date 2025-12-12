from typing import Optional, Any
from app.models.settings import LLMProfile
from app.providers.base import BaseLLMProvider
from langchain_anthropic import ChatAnthropic

class AnthropicProvider(BaseLLMProvider):
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        return ChatAnthropic(
            api_key=api_key,
            model=profile.model_id,
            temperature=profile.temperature,
            base_url=profile.base_url
        )
