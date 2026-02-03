from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class EventCreate(BaseModel):
    article_id: str
    article_url: Optional[str] = None
    registration_title: str = "无"
    registration_time: str = "即时"
    registration_method: Optional[str] = None
    event_time: str = "无"
    event_fee: str = "无"
    audience: str = "无"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EventUpdate(BaseModel):
    registration_title: Optional[str] = None
    registration_time: Optional[str] = None
    registration_method: Optional[str] = None
    event_time: Optional[str] = None
    event_fee: Optional[str] = None
    audience: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
