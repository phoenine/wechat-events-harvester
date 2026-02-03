from typing import Optional
from pydantic import BaseModel


class MessageTask(BaseModel):
    id: str
    task_id: str
    mps_id: str
    update_count: int = 0
    log: Optional[str] = None
    status: int = 0
    created_at: Optional[str] = None   # ISO datetime string
    updated_at: Optional[str] = None   # ISO datetime string
