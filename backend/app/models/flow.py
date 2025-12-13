from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class Flow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    is_archived: bool = Field(default=False)
    data: str  # JSON content of the flow (nodes, edges, viewport)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
