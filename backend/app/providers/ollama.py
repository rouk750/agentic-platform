from typing import Optional, Any
from app.models.settings import LLMProfile
from app.providers.base import BaseLLMProvider

try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

import httpx

class OllamaProvider(BaseLLMProvider):
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        url = profile.base_url or "http://localhost:11434"
        return ChatOllama(
            model=profile.model_id,
            temperature=profile.temperature,
            base_url=url
        )

    async def test_connection(self, profile: LLMProfile, api_key: Optional[str] = None) -> None:
        url = profile.base_url or "http://localhost:11434"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{url}/api/tags")
            resp.raise_for_status()
