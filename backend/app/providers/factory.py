from typing import Dict, Type
from app.models.settings import LLMProfile, ProviderType
from app.providers.base import BaseLLMProvider
from app.providers.openai import OpenAIProvider, LMStudioProvider
from app.providers.ollama import OllamaProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.bedrock import BedrockProvider
from app.providers.mistral import MistralProvider

class LLMProviderFactory:
    _registry: Dict[ProviderType, BaseLLMProvider] = {}
    
    @classmethod
    def register(cls, provider_type: ProviderType, provider: BaseLLMProvider):
        cls._registry[provider_type] = provider

    @classmethod
    def get_provider(cls, provider_type: ProviderType) -> BaseLLMProvider:
        provider = cls._registry.get(provider_type)
        if not provider:
             # Try fallback maps if direct match fails or maybe lazy register
             # For now, explicit registration is preferred
             raise ValueError(f"No provider registered for type {provider_type}")
        return provider

    @classmethod
    def create(cls, profile: LLMProfile, api_key: str = None):
        provider = cls.get_provider(profile.provider)
        return provider.create_client(profile, api_key)

# Initialize registry
LLMProviderFactory.register(ProviderType.OPENAI, OpenAIProvider())
LLMProviderFactory.register(ProviderType.ANTHROPIC, AnthropicProvider())
LLMProviderFactory.register(ProviderType.OLLAMA, OllamaProvider())
LLMProviderFactory.register(ProviderType.LMSTUDIO, LMStudioProvider())

# Add new ones (assuming ProviderType enum has these, otherwise we might need to cast or update Enum)
# If ProviderType enum doesn't have BEDROCK/MISTRAL, we'll need to update models/settings.py
# For now, we assume dynamic str matching or check if Enum needs update.
# Checking logic: if ProviderType is StrEnum, we can register strings?
# Let's check update of models/settings.py soon. 
try:
    LLMProviderFactory.register(ProviderType.BEDROCK, BedrockProvider())
except AttributeError:
    pass # Enum might not have it yet

try:
    LLMProviderFactory.register(ProviderType.MISTRAL, MistralProvider())
except AttributeError:
    pass 
