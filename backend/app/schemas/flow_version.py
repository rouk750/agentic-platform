from pydantic import BaseModel
from datetime import datetime

class FlowVersionRead(BaseModel):
    id: int
    flow_id: int
    data: str
    created_at: datetime
    is_locked: bool = False

    class Config:
        from_attributes = True
