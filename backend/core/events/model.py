from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Events(BaseModel):
    id: Optional[int] = None
    article_id: str = ""
    article_url: str = ""

    registration_title: str = "无"
    registration_time: str = "即时"
    registration_method: Optional[str] = None
    event_time: str = "无"
    event_fee: str = "无"
    audience: str = "无"

    created_at: Optional[str] = None   # ISO datetime string when stored in Supabase
    updated_at: Optional[str] = None
