from typing import Optional, Any
from app.models.settings import LLMProfile
from app.providers.base import BaseLLMProvider
# Assuming langchain-aws is installed
try:
    from langchain_aws import ChatBedrock
except ImportError:
    # Fallback or stub if not installed yet (though we ran poetry add)
    from langchain_community.chat_models import ChatBedrock

class BedrockProvider(BaseLLMProvider):
    def create_client(self, profile: LLMProfile, api_key: Optional[str] = None) -> Any:
        # Bedrock typically uses AWS credentials from environment or profile
        # Since profile.api_key might not map directly to AWS credentials structure
        # (needs key + secret + session token + region), we assume environment config
        # OR we could parse api_key as a JSON string for custom credentials.
        # For simplicity, we rely on boto3 environment setup, but pass region if in base_url or defaults.
        
        # TODO: Enhance to support passing credentials explicitly if stored in api_key field
        
        return ChatBedrock(
            model_id=profile.model_id,
            model_kwargs={"temperature": profile.temperature},
            region_name=profile.base_url if profile.base_url else None 
            # abusing base_url for region if needed, or leave to default
        )
