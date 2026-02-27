from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TagsCreate(BaseModel):
    name: str
    cover: Optional[str] = None
    intro: Optional[str] = None
    mps_id: str
    status: int = 1


class Tags(TagsCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
