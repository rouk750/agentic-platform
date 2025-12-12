from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    AZURE = "azure"
    LMSTUDIO = "lmstudio"
    BEDROCK = "bedrock"

class LLMProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    provider: ProviderType
    model_id: str
    base_url: Optional[str] = None
    api_key_ref: Optional[str] = None # Optional because Ollama might not need it, or it could be nullable
    
    temperature: float = 0.7
