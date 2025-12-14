from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AgentTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str # 'agent' or 'smart_node'
    config: str # JSON content

class AgentTemplateCreate(AgentTemplateBase):
    pass

class AgentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    config: Optional[str] = None
    is_archived: Optional[bool] = None

class AgentTemplateRead(AgentTemplateBase):
    id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentTemplateVersionRead(BaseModel):
    id: int
    template_id: int
    config: str
    created_at: datetime
    version_number: Optional[int] = None

    class Config:
        from_attributes = True
