from typing import Optional
from pydantic import BaseModel


class Feed(BaseModel):
    id: str
    mp_name: Optional[str] = None
    mp_cover: Optional[str] = None
    mp_intro: Optional[str] = None
    status: Optional[int] = None
    sync_time: Optional[int] = None
    update_time: Optional[int] = None
    created_at: Optional[str] = None   # ISO datetime string
    updated_at: Optional[str] = None   # ISO datetime string
    faker_id: Optional[str] = None
