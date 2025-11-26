from typing import Optional
from pydantic import BaseModel

class Tags(BaseModel):
    id: str
    name: Optional[str] = None
    cover: Optional[str] = None
    intro: Optional[str] = None
    status: Optional[int] = None
    mps_id: Optional[str] = None
    sync_time: Optional[int] = None
    update_time: Optional[int] = None
    created_at: Optional[str] = None   # ISO datetime string
    updated_at: Optional[str] = None   # ISO datetime string
