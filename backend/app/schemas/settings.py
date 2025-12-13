from pydantic import BaseModel
from typing import Optional

class LLMProfileCreate(BaseModel):
    name: str
    provider: str
    api_key: Optional[str] = None # Optional for Ollama
    model_id: str
    base_url: Optional[str] = None

class LLMProfileUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    base_url: Optional[str] = None
