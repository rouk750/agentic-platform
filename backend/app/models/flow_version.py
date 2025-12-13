from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class FlowVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    flow_id: int = Field(foreign_key="flow.id")
    data: str  # JSON content of the flow version
    created_at: datetime = Field(default_factory=datetime.utcnow)
