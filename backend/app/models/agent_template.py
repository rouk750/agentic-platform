from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class AgentTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    type: str # 'agent' or 'smart_node' or custom types
    is_archived: bool = Field(default=False)
    config: str # JSON content of the node configuration
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentTemplateVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="agenttemplate.id")
    config: str # JSON content of the configuration version
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version_number: Optional[int] = None # Optional for now, can be auto-incremented or just use ID/created_at
