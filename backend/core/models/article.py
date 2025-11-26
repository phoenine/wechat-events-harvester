from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArticleBase(BaseModel):
    id: str
    mp_id: Optional[str] = None
    title: Optional[str] = None
    pic_url: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    status: int = 1
    publish_time: Optional[int] = None
    publish_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_export: Optional[int] = None

class Article(ArticleBase):
    content: Optional[str] = None
    content_md: Optional[str] = None