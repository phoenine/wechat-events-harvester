from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TagsCreate(BaseModel):
    name: str
    description: Optional[str] = None
    intro: Optional[str] = None
    cover: Optional[str] = None
    mps_id: Optional[str] = None
    status: Optional[int] = None


class Tags(TagsCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
