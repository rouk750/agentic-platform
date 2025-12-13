from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FlowBase(BaseModel):
    name: str
    description: Optional[str] = None
    data: str  # JSON content of the flow

class FlowCreate(FlowBase):
    pass

class FlowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[str] = None
    is_archived: Optional[bool] = None

class FlowRead(FlowBase):
    id: int
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
