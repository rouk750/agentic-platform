from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ChromaMode(str, Enum):
    LOCAL = "local"
    SERVER = "server"

class ChromaNodeConfig(BaseModel):
    mode: ChromaMode = Field(default=ChromaMode.LOCAL, description="Connection mode: 'local' (file) or 'server' (http)")
    
    # Local Config
    path: Optional[str] = Field(default="./chroma_db", description="Path to local ChromaDB directory")
    
    # Server Config
    host: Optional[str] = Field(default="localhost", description="ChromaDB Server Host")
    port: Optional[int] = Field(default=8000, description="ChromaDB Server Port")
    
    # Common
    collection_name: str = Field(default="default", description="Name of the collection to use")
    
    class Config:
        use_enum_values = True
